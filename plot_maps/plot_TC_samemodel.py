#!/usr/bin/env python

# Run as:
# python plot_TC_samemodel.py $MODEL $TC_name/ID/Year
# python plot_TC_samemodel.py GFS FlorenceAL062018
#

import numpy as np
import os, sys, datetime, time, subprocess
import re, csv, glob
import multiprocessing, itertools, collections
import scipy, ncepy

import pyproj
import cartopy.crs as ccrs
#from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
import cartopy.feature as cfeature
import cartopy.io.shapereader as shpreader

import matplotlib
import matplotlib.image as image
from matplotlib.gridspec import GridSpec
import matplotlib.ticker as mticker
import matplotlib.pyplot as plt
from matplotlib import colors as c
matplotlib.use('Agg')

import cartopy



# Determine desired model
try:
   model_str = str(sys.argv[1])
except IndexError:
   model_str = None

if model_str is None:
   print('Model string options: GFS, HWRF, HMON')
   model_str = input('Enter desired model: ')

if str.upper(model_str) == 'EMX' or str.upper(model_str) == 'ECMO' or str.upper(model_str) == 'EC_DET':
   model = 'EC'
#elif str.upper(model_str) == 'GFSO':
#   model = 'GFSv14'
elif str.upper(model_str) == 'UKX':
   model = 'UKM'
elif str.upper(model_str) == 'UK':
   model = 'UKM'
elif str.upper(model_str[0:3]) == 'HF3':
   model = 'HAFS v0.3'+model_str[-1]
elif str.upper(model_str[-4:]) == 'MEAN':
   model = model_str[:-4]+' Mean'
else:
   model = str.upper(model_str)


# Get TC name and number
try:
   TC = str(sys.argv[2])
except IndexError:
   TC = None

if TC is None:
   print('Enter TC name, number, and year as one string')
   print('Example: FlorenceAL062018')
   TC = input('Enter TC name/number/year: ')

TC_name = TC[:-8]
TC_number = TC[-8:-4]
YYYY = TC[-4:]
print(TC_name, TC_number, YYYY)



# Option to make special HAFS comparison graphics
try:
    dummy = str(sys.argv[3])
    do_hafs = True
    print('Plotting HAFS comparison images')
except IndexError:
    dummy = None
    do_hafs = False


# Set path and create graphx directory (if not already created)
MEG_DIR = os.getcwd()


BDECK_DIR = '/lfs/h1/ops/prod/dcom/nhc/atcf-noaa/btk'

if do_hafs:
    DATA_DIR = os.path.join('/lfs/h2/emc/vpppg/noscrub/',os.environ['USER'],'MEG', TC_name, 'data','hafs')
    GRAPHX_DIR = os.path.join('/lfs/h2/emc/vpppg/noscrub/',os.environ['USER'],'MEG', TC_name, 'graphx','hafs')
else:
    DATA_DIR = os.path.join('/lfs/h2/emc/vpppg/noscrub/',os.environ['USER'],'MEG', TC_name, 'data')
    GRAPHX_DIR = os.path.join('/lfs/h2/emc/vpppg/noscrub/',os.environ['USER'],'MEG', TC_name, 'graphx')


if os.path.exists(DATA_DIR):
   if not os.path.exists(GRAPHX_DIR):
      os.makedirs(GRAPHX_DIR)
else:
   raise NameError('data for '+TC_name+' not found')


#OUT_DIR = os.path.join(GRAPHX_DIR, model_str)
OUT_DIR = GRAPHX_DIR
if not os.path.exists(OUT_DIR):
      os.makedirs(OUT_DIR)


# Set Landfall Date based on NHC 
# Needed to only look for RI periods prior to this time
landfall_date = datetime.datetime(2024,9,27,3,0,0)
landfall_date2 = datetime.datetime(2020,8,29,16,55,0)

try:
   valid_time
except NameError:
   valid_time = None


# Get list of GFS cycles to get max number of cycles
filelist1 = [f for f in glob.glob(DATA_DIR+'/'+str.lower(model_str)+'/'+str.lower(TC_name)+'_'+str.lower(model_str)+'_'+str(YYYY)+'*csv')]
max_cycles_unordered = [filelist1[x][-14:-4] for x in range(len(filelist1))]
max_cycles_int = [int(x) for x in max_cycles_unordered]
max_cycles_int.sort()
max_cycles = [str(x) for x in max_cycles_int]
max_ncycles = len(max_cycles)


# Get list of cycles based on matching files in DATA_DIR
filelist = [f for f in glob.glob(DATA_DIR+'/'+str.lower(model_str)+'/'+str.lower(TC_name)+'_'+str.lower(model_str)+'_'+str(YYYY)+'*csv')]

cycles_unordered = [filelist[x][-14:-4] for x in range(len(filelist))]
cycles_int = [int(x) for x in cycles_unordered]
cycles_int.sort()
cycles = [str(x) for x in cycles_int]
preLF_cycles = [str(x) for x in cycles if x < landfall_date.strftime('%Y%m%d%H')]

# From Dorian (2019) when the center reformed
RF_preLF_cycles = [str(x) for x in cycles if x >= '2019082718' and x < landfall_date.strftime('%Y%m%d%H')]
print(RF_preLF_cycles[0])
RF_ind = cycles.index(RF_preLF_cycles[0])

#print(str(x), landfall_date.strftime('%Y%m%d%H'))
#print cycles
print(preLF_cycles)
#print(RF_preLF_cycles)

# Get observed data from Best Track file
# Get final valid time by picking last time of TD strength in Best Track file
olat = []
olon = []
opres = []
ovmax = []
otime = []

with open(BDECK_DIR+'/b'+str.lower(TC_number)+str(YYYY)+'.dat','r') as f:
   reader = csv.reader(f)
   for row in reader:
    # if row[27].replace(" ","")==str.upper(TC_name) and (row[11].replace(" ","")=='34' or row[11].replace(" ","")=='0'):
    # if row[10].replace(" ","")=='TD' or row[10].replace(" ","")=='TS' or row[10].replace(" ","")=='HU':
    # if row[10].replace(" ","")=='TD' or row[10].replace(" ","")=='TS' or row[10].replace(" ","")=='HU' or row[10].replace(" ","")=='EX':
      if (row[10].replace(" ","")=='DB' or row[10].replace(" ","")=='LO' or row[10].replace(" ","")=='TD' or row[10].replace(" ","")=='TS' or row[10].replace(" ","")=='HU' or row[10].replace(" ","")=='EX') and row[2].replace(" ","")>= cycles[0]:
         if row[11].replace(" ","")=='34' or row[11].replace(" ","")=='0':
         #  print row[2].replace(" ","")
            rowtime=datetime.datetime.strptime(row[2].replace(" ",""),"%Y%m%d%H")

            olat.append(float(re.sub("N","",row[6]))/10.0)
            try:
               olon.append(float(re.sub("W","",row[7]))/-10.0)
            except:
               olon.append(float(re.sub("E","",row[7]))/10.0)
            ovmax.append(float(row[8]))
            opres.append(float(row[9]))
            otime.append(rowtime)



# Get list of dates from first model initialization through final valid time
if str.upper(model_str[0:2]) == 'UK':
   init_inc = 12
else:
   init_inc = 6

date_list = []

first_model_date = datetime.datetime(int(cycles[0][0:4]),int(cycles[0][4:6]),int(cycles[0][6:8]),int(cycles[0][8:10]),0,0)
if str.upper(model_str) == 'FV3GFS': 
   first_model_date = datetime.datetime(2018,10,7,0,0,0)

final_valid_date = otime[-1]
cycle_date = first_model_date

while cycle_date <= final_valid_date:
   date_list.append(cycle_date)
   cycle_date += datetime.timedelta(hours=init_inc)

print(date_list[0].strftime('%Y%m%d%H'), date_list[-1].strftime('%Y%m%d%H'))


plot_opres=[]
plot_ovmax=[]
plot_olf=[]
k = 1

for j in range(len(date_list)):
   for i in range(len(opres)):
      if otime[i] == date_list[j]:
         plot_opres.append(opres[i])
         plot_ovmax.append(ovmax[i])
       # if otime[i] == landfall_date:
         if otime[i] == landfall_date or otime[i] == landfall_date2:
            plot_olf.append(1)
         else:
            plot_olf.append(0)

   if len(plot_opres) < k: 
      plot_opres.append(np.nan)  
      plot_ovmax.append(np.nan)  
      plot_olf.append(np.nan)  

   k += 1


try:
#  plot_olf_ind = plot_olf.index(1)
   plot_olf_ind = [i for i, x in enumerate(plot_olf) if x == 1]
   print(plot_olf_ind)
   markers_on = [plot_olf_ind]
except:
   markers_on = []


#print(len(date_list), len(plot_opres))




# Option to set final valid time to end of Best Track
match_end_bt = False
if match_end_bt:
   valid_time = otime[-1]


mlats=[]
mlons=[]
mpres=[]
mvmax=[]
#mrmw=[]
mtimes=[]

for cycle in cycles:

   YYYY = int(cycle[0:4])
   MM   = int(cycle[4:6])
   DD   = int(cycle[6:8])
   HH   = int(cycle[8:10])
   print(YYYY, MM, DD, HH)

   cycle_date = datetime.datetime(YYYY,MM,DD,HH,0,0)

   track_file = DATA_DIR+'/'+str.lower(model_str)+'/'+str.lower(TC_name)+'_'+str.lower(model_str)+'_'+cycle+'.csv' 

   # lat/lon lists for each model
   clat=[]
   clon=[]
   cpres=[]
   cvmax=[]
#  crmw=[]
   ctime=[]

   if os.path.exists(track_file):
      with open(track_file,'r') as f:
         reader=csv.reader(f)
         for row in reader:  
            fcst_time = cycle_date+datetime.timedelta(hours=int(row[0]))
            if valid_time is not None:
               if fcst_time <= valid_time:
                  clat.append(float(row[2]))
                  if float(row[3]) > 0:
                     clon.append(float(row[3])-360)
                  else:
                     clon.append(float(row[3]))
                  cpres.append(float(row[4]))
                  cvmax.append(float(row[5]))
       #          crmw.append(float(row[6]))
                  ctime.append(fcst_time)
            else:
               clat.append(float(row[2]))
               if float(row[3]) > 0:
                # clon.append(float(row[3])-360)
                  clon.append(float(row[3]))
               else:
                  clon.append(float(row[3]))
               if float(row[4]) != 0:
                  cpres.append(float(row[4]))
               else:
                  cpres.append(np.nan)
               if float(row[5]) != 0:
                  cvmax.append(float(row[5]))
               else:
                  cvmax.append(np.nan)
       #       crmw.append(float(row[6]))
               ctime.append(fcst_time)


      mlats.append(clat)
      mlons.append(clon)
      mpres.append(cpres)
      mvmax.append(cvmax)
#     mrmw.append(crmw)
      mtimes.append(ctime)

#print(mvmax[17])

plot_mpres=[]
plot_mvmax=[]

for x in range(len(mlats)):
   k = 1
   temp_mpres=[]
   temp_mvmax=[]
   for j in range(len(date_list)):
      for i in range(len(mpres[x])):
         if mtimes[x][i] == date_list[j]:
            temp_mpres.append(mpres[x][i])
            temp_mvmax.append(mvmax[x][i])

      if len(temp_mpres) < k: 
         temp_mpres.append(np.nan)  
         temp_mvmax.append(np.nan)  

      k += 1

   plot_mpres.append(temp_mpres)
   plot_mvmax.append(temp_mvmax)

#print(len(date_list), len(plot_opres))




# Define dictionary of colors based on the max number of cycles
# This will fail if GFS CSVs haven't been created
# Attempts to apply the same color to a given cycle, regardless of model
cmap=matplotlib.cm.get_cmap('YlGnBu')
values = []
for i in range(max_ncycles):
   values.append(cmap(float(i+1)/float(max_ncycles+1)))
color_dict = dict(zip(max_cycles,values))





def plot_tracks(domain):

   print('plotting '+TC_name+' on '+domain+' domain')

   fig = plt.figure(figsize=(10.9,8.9))
   gs = GridSpec(1,1,wspace=0.0,hspace=0.0)

   # Define where Cartopy maps are located
   cartopy.config['data_dir'] = '/lfs/h2/emc/vpppg/save/'+os.environ['USER']+'/python/NaturalEarth'

   back_res='50m'
   back_img='off'


   if str.upper(domain) == 'CONUS':
       llcrnrlon = -121.5 
       llcrnrlat = 22.
       urcrnrlon = -64.5
       urcrnrlat = 48.
       proj = 'lcc'
       lon0 =-101.
       lat0 = 39.
       standard_parallels=(32,46)
       draw_counties = False
   elif str.upper(domain) == 'GOA':
       llcrnrlon = -100. 
       llcrnrlat = 12.5
       urcrnrlon = -70.
       urcrnrlat = 35.
       proj = 'lcc'
       lon0 =-87.5
       lat0 = 35.5
       standard_parallels=(25,46)
       draw_counties = False
   elif str.upper(domain) == 'MICHAEL':
       llcrnrlon = -90.
       llcrnrlat = 20.    # 17.5 or 25.
       urcrnrlon = -60.   # -65.
       urcrnrlat = 40.    # 45.
       proj = 'lcc'
       draw_counties = False
   elif str.upper(domain) == 'SE_COAST':
       llcrnrlon = -90.
       llcrnrlat = 22.    # 24.
       urcrnrlon = -72.   # -62.5, -67.5
       urcrnrlat = 37.5   # 42
       proj = 'lcc'
       lon0 =-81.
       lat0 = 39.
       standard_parallels=(32,46)
       draw_counties = False
   elif str.upper(domain) == 'IDA':
       llcrnrlon = -100. 
       llcrnrlat = 10.
       urcrnrlon = -60.
       urcrnrlat = 45.
       proj = 'merc'
       lat_ts = 35.
       draw_counties = False
   elif str.upper(domain) == 'IAN':
       llcrnrlon = -100. 
       llcrnrlat = 5.
       urcrnrlon = -52.
       urcrnrlat = 45.
       proj = 'merc'
       lon0 = -76.
       lat_ts = 35.
       draw_counties = False
   elif str.upper(domain) == 'CARIB':
       llcrnrlon = -80.
       llcrnrlat = 10.
       urcrnrlon = -55.
       urcrnrlat = 27.5
       proj = 'merc'
       lat_ts = 20.
       draw_counties = False
   elif str.upper(domain) == 'GR_ANT':
       llcrnrlon = -85.
       llcrnrlat = 15.
       urcrnrlon = -62.5
       urcrnrlat = 32.
       proj = 'merc'
       lon0 = -73.75
       lat_ts = 20.
       draw_counties = False
   elif str.upper(domain) == 'BAHAMAS':
       llcrnrlon = -85.
       llcrnrlat = 22.
       urcrnrlon = -72.5
       urcrnrlat = 30.
       proj = 'merc'
       lat_ts = 25.
       draw_counties = False
   elif str.upper(domain) == 'CPAC':
       llcrnrlon = -180.
       llcrnrlat = 5.
       urcrnrlon = -110.
       urcrnrlat = 40.
       proj = 'merc'
       lat_ts = 20.
       draw_counties = False
   elif str.upper(domain) == 'HAWAII':
       llcrnrlon = -165.
       llcrnrlat = 10.
       urcrnrlon = -145.
       urcrnrlat = 25.
       proj = 'merc'
       lon0 = -155.
       lat_ts = 20.
       draw_counties = False


   extent = [llcrnrlon-1,urcrnrlon+1,llcrnrlat-1,urcrnrlat+1]

   if proj == 'lcc':
       myproj = ccrs.LambertConformal(central_longitude=lon0,central_latitude=lat0,
                false_easting=0.0,false_northing=0.0,secant_latitudes=None,
                standard_parallels=standard_parallels,globe=None)
   elif proj == 'merc':
       myproj = ccrs.Mercator(central_longitude=lon0,min_latitude=llcrnrlat,
                max_latitude=urcrnrlat,latitude_true_scale=lat_ts,globe=None)

   # All lat lons are earth relative, so setup the associated projection correct for that data
   transform = ccrs.PlateCarree()

   ax = fig.add_subplot(gs[0:1,0:1], projection=myproj)
   ax.set_extent(extent,crs=transform)
   axes = [ax]

   fline_wd = 1.0        # line width
   fline_wd_lakes = 0.3  # line width
   falpha = 0.7          # transparency

   lakes = cfeature.NaturalEarthFeature('physical','lakes',back_res,
                edgecolor='black',facecolor='none',
                linewidth=fline_wd_lakes,zorder=1)
   coastlines = cfeature.NaturalEarthFeature('physical','coastline',
                back_res,edgecolor='black',facecolor='none',
                linewidth=fline_wd,zorder=1)
   states = cfeature.NaturalEarthFeature('cultural','admin_1_states_provinces',
                back_res,edgecolor='black',facecolor='none',
                linewidth=fline_wd,zorder=1)
   borders = cfeature.NaturalEarthFeature('cultural','admin_0_countries',
                back_res,edgecolor='black',facecolor='none',
                linewidth=fline_wd,zorder=1)


   # high-resolution background images
   if back_img=='on':
       img = plt.imread('/lfs/h2/emc/vpppg/save/'+os.environ['USER']+'/python/NaturalEarth/raster_files/NE1_50M_SR_W.tif')
       ax.imshow(img, origin='upper', transform=transform)


   ax.add_feature(cfeature.COASTLINE.with_scale('50m'),linewidths=0.6,linestyle='solid',edgecolor='k',zorder=4)

   ax.add_feature(cfeature.OCEAN.with_scale('50m'),linewidths=0.5,linestyle='solid',edgecolor='k',facecolor='#5c5c5c',zorder=1)
   ax.add_feature(cfeature.LAND.with_scale('50m'),linewidths=0.5,linestyle='solid',edgecolor='k',facecolor='#D3D3D3',zorder=1)
   ax.add_feature(cfeature.BORDERS.with_scale('50m'),linewidths=0.5,linestyle='solid',edgecolor='k',zorder=4)
   ax.add_feature(cfeature.STATES.with_scale('50m'),linewidths=0.3,linestyle='solid',edgecolor='k',zorder=4)

   latlongrid = 10.
   if draw_counties:
      ax.add_feature(COUNTIES,facecolor='none',edgecolor='gray')
      latlongrid = 5.
   if str.upper(domain) == 'BARRY':
      latlongrid = 5.

   parallels = np.arange(0.,90.,latlongrid)
   meridians = np.arange(180.,360.,latlongrid)
   print(parallels)


   if str.upper(domain) == 'IAN':

    #  xgl = ax.gridlines(crs=transform,draw_labels=True,xlocs=meridians,
    #                     linewidth=0.3,color='black',linestyle='solid')
       gl = ax.gridlines(crs=transform,draw_labels=True,
                         linewidth=0.3,color='black',linestyle='solid')
       gl.top_labels = False
       gl.right_labels = False
       gl.xlocater = mticker.FixedLocator(meridians)
       gl.ylocater = mticker.FixedLocator(parallels)
     # gl.xformatter = LONGITUDE_FORMATTER
     # gl.yformatter = LATITUDE_FORMATTER
       gl.xformatter = LongitudeFormatter()
       gl.yformatter = LatitudeFormatter()
       gl.xlabel_style = {'size':10, 'color':'black'}
       gl.ylabel_style = {'size':10, 'color':'black'}


#  print(np.shape(olat))
#  cmap=matplotlib.cm.get_cmap('YlGnBu')

   for i in range(len(mlats)):
   #  label_str = mtimes[i][0].strftime('%HZ %m/%d')
   #  x, y = m(mlons[i],mlats[i])
   #  m.plot(x, y, '-', color=cmap(float(i+1)/float(len(mlats)+1)), label=label_str, linewidth=2.)
      plt.plot(mlons[i], mlats[i], '-', color=color_dict[mtimes[i][0].strftime("%Y%m%d%H")], linewidth=2., transform=transform)

 # x, y = m(olon,olat)
 # m.plot(x, y, '-', color='black', label='BEST', linewidth=2.)
   plt.plot(olon, olat, '-', color='black', label='BEST', linewidth=2., transform=transform)

#  plt.legend(loc="upper right")

   titlestr1 = 'Hurricane '+TC_name+' - '+model+' Tracks'
   titlestr2 = mtimes[0][0].strftime('%HZ %d %b')+' to '+mtimes[-1][0].strftime('%HZ %d %b %Y Initializations')
   plt.text(0.5, 1.05, titlestr1, fontweight='bold', horizontalalignment='center', transform=ax.transAxes)
   plt.text(0.5, 1.01, titlestr2, fontweight='bold', horizontalalignment='center', transform=ax.transAxes)

   fname = str.lower(TC_name)+'_'+str.lower(model_str)+'_tracks_'+str.lower(domain)

   plt.savefig(OUT_DIR+'/'+fname+'.png',bbox_inches='tight')
   plt.close()






def ptrace():

   print('plotting pressure traces')
   print(len(plot_opres))    # same length as date_list

   fig = plt.figure(figsize=(9,8))
   cmap=matplotlib.cm.get_cmap('YlGnBu')

   for i in range(len(plot_mpres)):
#     label_str = mtimes[i][0].strftime('%HZ %m/%d')
#     plt.plot(plot_mpres[i], '-', color=cmap(float(i+1)/float(len(plot_mpres)+1)), label=label_str, linewidth=2.)
      plt.plot(plot_mpres[i], '-', color=color_dict[mtimes[i][0].strftime("%Y%m%d%H")], linewidth=2.)

#  plt.plot(plot_opres, '-', color='black', label='BEST', linewidth=2.)
   plt.plot(plot_opres, '-', color='black', label='BEST', linewidth=2., marker='D', markersize=7, markevery=markers_on)


   xlen = len(plot_opres) 
   x = np.arange(0,xlen,1)


   plt.axis([0,xlen,920,1020])
   plt.axhspan(900, 1020, facecolor='0.5', alpha=0.5)

   labels=[]
   for x in range(0,xlen,2):
      if x%4 == 0 and str.upper(model) != 'UK':
         labels.append(date_list[x].strftime('%HZ %m/%d'))
      elif x%2 == 0 and str.upper(model) == 'UK':
         labels.append(date_list[x].strftime('%HZ %m/%d'))
      else:
         labels.append('')

#  labels = [date_list[x].strftime('%HZ %m/%d') for x in range(0,xlen,6)]
   plt.xticks(np.arange(0,xlen,step=2),labels,rotation=-45,ha='left')
   plt.ylabel('Minimum Pressure (mb)')

   plt.grid(True)

   titlestr = 'Hurricane '+TC_name+' - '+model+' Minimum Pressure Traces \n'+ \
              mtimes[0][0].strftime('%HZ %d %b')+' to '+mtimes[-1][0].strftime('%HZ %d %b %Y Initializations')
   plt.title(titlestr, fontweight='bold')

   fname = str.lower(TC_name)+'_'+str.lower(model_str)+'_ptrace'

   plt.savefig(OUT_DIR+'/'+fname+'.png',bbox_inches='tight')
   plt.close()




def vtrace():

   print('plotting wind traces')
   print(len(plot_ovmax))    # same length as date_list

   fig = plt.figure(figsize=(9,8))
   cmap=matplotlib.cm.get_cmap('YlGnBu')

   for i in range(len(plot_mvmax)):
    # label_str = mtimes[i][0].strftime('%HZ %m/%d')
    # plt.plot(plot_mvmax[i], '-', color=cmap(float(i+1)/float(len(plot_mvmax)+1)), label=label_str, linewidth=2.)
      plt.plot(plot_mvmax[i], '-', color=color_dict[mtimes[i][0].strftime("%Y%m%d%H")], linewidth=2.)

#  plt.plot(plot_ovmax, '-', color='black', label='BEST', linewidth=2.)
   plt.plot(plot_ovmax, '-', color='black', label='BEST', linewidth=2., marker='D', markersize=7, markevery=markers_on)

   xlen = len(plot_ovmax) 
   x = np.arange(0,xlen,1)


   plt.axis([0,xlen,5,160])
   plt.axhspan(0, 34, facecolor='0.5', alpha=0.5)
   plt.axhspan(34, 64, facecolor='0.4', alpha=0.5)
   plt.axhspan(64, 83, facecolor='0.3', alpha=0.5)
   plt.axhspan(83, 96, facecolor='0.25', alpha=0.5)
   plt.axhspan(96, 113, facecolor='0.2', alpha=0.5)
   plt.axhspan(113, 137, facecolor='0.15', alpha=0.5)
   plt.axhspan(137, 200, facecolor='0.1', alpha=0.5)

   labels=[]
   for x in range(0,xlen,2):
      if x%4 == 0 and str.upper(model) != 'UK':
         labels.append(date_list[x].strftime('%HZ %m/%d'))
      elif x%2 == 0 and str.upper(model) == 'UK':
         labels.append(date_list[x].strftime('%HZ %m/%d'))
      else:
         labels.append('')

#  labels = [date_list[x].strftime('%HZ %m/%d') for x in range(0,xlen,6)]
   plt.xticks(np.arange(0,xlen,step=2),labels,rotation=-45,ha='left')
   plt.ylabel('Maximum Sustained 10-m Wind (kts)')

#  plt.annotate('Cat 1',xy=(xlen+1,73.5))

   plt.grid(True)

   titlestr = 'Hurricane '+TC_name+' - '+model+' Max 10-m Wind Traces \n'+ \
              mtimes[0][0].strftime('%HZ %d %b')+' to '+mtimes[-1][0].strftime('%HZ %d %b %Y Initializations')
   plt.title(titlestr, fontweight='bold')

   fname = str.lower(TC_name)+'_'+str.lower(model_str)+'_vmaxtrace'

   plt.savefig(OUT_DIR+'/'+fname+'.png',bbox_inches='tight')
   plt.close()




def check_RI():
   print('checking for RI periods')

#  print('number of '+model_str+' cycles is:', len(mvmax))
#  print('number of '+model_str+' pre-landfall cycles is:', len(preLF_cycles))

   RI_count = 0
   if len(ovmax) > 1:
      ohr_diff = otime[1] - otime[0]
      ohr_inc = int(ohr_diff.total_seconds()/3600)
      t1 = 0
      t2 = int(24/ohr_inc)

      while t2 < len(ovmax):
         if ovmax[t2]-ovmax[t1] >= 30:
            RI_count += 1
            print('Observed RI period began at',otime[t1],'and ended at',otime[t2])

         t1 += 1
         t2 += 1


   RI_cycles = 0
   RI_cycle_list = []

   this_list = preLF_cycles
#  this_list = RF_preLF_cycles

   for i in range(len(this_list)):
      RI_count = 0   # RI periods for this cycle

      if this_list == RF_preLF_cycles:
         x = i+RF_ind
      else:
         x = i 

      if len(mtimes[x]) > 1:
         fhr_diff = mtimes[x][1]-mtimes[x][0]
         fhr_inc = int(fhr_diff.total_seconds()/3600)
         t1 = 0
         t2 = int(24/fhr_inc)

         while t2 < len(mtimes[x]) and RI_count==0:
            if mvmax[x][t2]-mvmax[x][t1] >= 30:
               RI_count += 1
   #           os.system('touch '+OUT_DIR+'/ri_'+str.lower(model_str)+'_'+cycles[i])

            t1 += 1
            t2 += 1

         if RI_count >= 1:
            RI_cycles +=1

            RI_cycle_list.append(this_list[i])


   write_RI_list = True
   if write_RI_list:
      f = open(DATA_DIR+'/'+str.lower(model_str)+'/'+str.lower(TC_name)+'_'+str.lower(model_str)+'_RIlist.csv','wt')      
      try:
         writer = csv.writer(f)
         writer.writerow(RI_cycle_list)
      finally:
         f.close()

   print('number of '+model_str+' RI cycles is:', RI_cycles)
  


def check_max_vmax():
   print('checking for max vmax')

   hurr_cycles = 0
   major_cycles = 0
   max_vmax_list = []
   hurr_list = []
   major_list = []

   this_list = preLF_cycles
#  this_list = RF_preLF_cycles

   for i in range(len(this_list)):

      if this_list == RF_preLF_cycles:
         x = i+RF_ind
      else:
         x = i 

#     cycle_vmax = np.amax(mvmax[x])
      cycle_vmax = np.nanmax(mvmax[x])

      print(cycle_vmax)
      max_vmax_list.append(cycle_vmax)

      if cycle_vmax >= 64:
         hurr_cycles += 1
         hurr_list.append(this_list[i])

      if cycle_vmax >= 96:
         major_cycles += 1
         major_list.append(this_list[i])

   cycle_ind = np.argmax(max_vmax_list)
   print(max_vmax_list)

   print('number of '+model_str+' cycles is:', len(mvmax))
   print('number of '+model_str+' pre-landfall cycles is:', len(this_list))
   print('number of '+model_str+' hurricane cycles is:', hurr_cycles)
   print('number of '+model_str+' major cycles is:', major_cycles)
   print('max of '+model_str+' wind speed is:', np.nanmax(max_vmax_list), 'from', this_list[cycle_ind], 'cycle')

   obs_vmax = np.amax(ovmax)
   obs_vmax_ind = np.argmax(ovmax)
   if obs_vmax >= 64:
      print(TC_name,'reached hurricane status')
   if obs_vmax >= 96:
      print(TC_name,'reached major hurricane status')
   print('max observed wind speed is:', obs_vmax, 'at', otime[obs_vmax_ind].strftime('%Y%m%d%H'))




   write_vmax_list = True
   if write_vmax_list:
      f = open(DATA_DIR+'/'+str.lower(model_str)+'/'+str.lower(TC_name)+'_'+str.lower(model_str)+'_vmaxlist.csv','wt')      
      try:
         writer = csv.writer(f)
         writer.writerow(this_list)
         writer.writerow(max_vmax_list)
      finally:
         f.close()


   write_hurr_list = True
   if write_hurr_list:
      f = open(DATA_DIR+'/'+str.lower(model_str)+'/'+str.lower(TC_name)+'_'+str.lower(model_str)+'_hurrrlist.csv','wt')      
      try:
         writer = csv.writer(f)
         writer.writerow(hurr_list)
      finally:
         f.close()


   write_major_list = True
   if write_major_list:
      f = open(DATA_DIR+'/'+str.lower(model_str)+'/'+str.lower(TC_name)+'_'+str.lower(model_str)+'_majorlist.csv','wt')      
      try:
         writer = csv.writer(f)
         writer.writerow(major_list)
      finally:
         f.close()




def main():

    # plot composite pressure traces
    ptrace()

    # Plote composite wind traces
    vtrace()

    # Prints info related to max wind predicted by the model    
    check_max_vmax()

    # Prints info related to RI periods predicted by the model
    check_RI()

    # Creates composite track maps over these domains
 #  domains = ['NW_ATL','NATL','SE_COAST','CARIB','GR_ANT','BAHAMAS']
 #  domains = ['MICHAEL','BARRY']
 #  domains = ['GOA','IDA','BARRY','LOUISIANA']
    domains = ['IAN','SE_COAST','GOA']
    pool = multiprocessing.Pool(len(domains))
    pool.map(plot_tracks,domains)




main()



