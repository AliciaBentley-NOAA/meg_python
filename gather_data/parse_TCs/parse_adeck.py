# Author: L Dawson
#
# Script to pull fcst files from HPSS, rename, and save in desired data directory
# Desired cycle and model string can be passed in from command line
# If no arguments are passed in, script will prompt user for these inputs
#
# Run as:
# python parse_adeck.py $MODEL $TC_name/ID
# python parse_adeck.py GFS FlorenceAL06
#
# Script History Log:
# 2018-10-03 L Dawson initial version to pull HWRF/HMON ATCF files from tape
# 2022-10-03 L Dawson WCOSS2 update 


import numpy as np
import datetime, os, sys, subprocess
import re, csv


# Determine desired model
try:
   model_str = str(sys.argv[1])
except IndexError:
   model_str = None

if model_str is None:
   print('Model string options: GFS (AVNO or GFS), EC (EC, ECMWF, or EMX), UK (UK, UKMet, EGRR, or UKX), CMC, HWRF, HMON, NAM')
   print('Model string options (early): AVNI, CMCI, HWFI, HMNI')
   print('Model string options (ensemble mean): GEFSMean, ECENSmean')
   model_str = input('Enter desired model: ')


if str.upper(model_str) == 'GFS':
   model = 'AVNO'
elif str.upper(model_str) == 'EC' or str.upper(model_str) == 'ECMWF':
   model = 'ECMO'   # GTS tracker
   model = 'EMX'   # NCEP tracker - data used by NHC
elif str.upper(model_str) == 'UK' or str.upper(model_str) == 'UKMET':
   model = 'EGRR'
elif str.upper(model_str) == 'GEFSMEAN':
   model = 'AEMN'
elif str.upper(model_str) == 'ECENSMEAN' or str.upper(model_str) == 'ECMEAN':
   model = 'EEMN'
else:
   model = model_str


if (str.upper(model_str[0:2]) == 'UK' or str.upper(model_str) == 'EGRR') and str.upper(model_str) != 'UKX':
   wind_id = '0'
else:
   wind_id = '34'

# Get TC name and number
try:
   TC = str(sys.argv[2])
except IndexError:
   TC = None

if TC is None:
   print('Enter TC name, number, and year as one string')
   print('Example: FlorenceAL062018')
   TC = input('Enter TC name/number/year: ')

TC_name = TC[:-8]   #AL062018 is 8 characters
TC_number = TC[-8:-4]
YYYY = TC[-4:]
print(TC_name, TC_number, YYYY)






# Set path and create data directory (if not already created)
DIR = os.getcwd()

if str.upper(model_str[0:3]) == 'HF3':
    ADECK_DIR = '/lfs/h2/emc/hur/noscrub/zhan.zhang/real-time-2022'
else:
    ADECK_DIR = '/lfs/h1/ops/prod/dcom/nhc/atcf-noaa/aid_nws'
DATA_DIR = os.path.join('/lfs/h2/emc/vpppg/noscrub',os.environ['USER'],'MEG', TC_name, 'data', str.lower(model_str))

if not os.path.exists(DATA_DIR):
      os.makedirs(DATA_DIR)


cycles=[]
fhrs=[]
lats=[]
lons=[]
vmax=[]
pres=[]
rmw=[]


with open(ADECK_DIR+'/a'+str.lower(TC_number)+YYYY+'.dat','r') as f:
   reader = csv.reader(f)
   for row in reader:
      if row[4].replace(" ","") == str.upper(model) and row[11].replace(" ","") == wind_id:   # needs to be '0' for UKMet
         thislat = row[6].replace(" ","")
         thislon = row[7].replace(" ","")

         cycles.append(row[2].replace(" ",""))
         fhrs.append(row[5].replace(" ",""))
         lats.append(float(re.sub("N","",thislat))/10.0)
         try:
            lons.append(float(re.sub("W","",thislon))/-10.0)
         except:
            lons.append(float(re.sub("E","",thislon))/10.0)
         vmax.append(row[8].replace(" ",""))
         pres.append(row[9].replace(" ",""))
#        rmw.append(row[19].replace(" ",""))


used=set()
cycles_in_file = [x for x in cycles if x not in used and (used.add(x) or True)]


i = 0
for cycle in cycles_in_file:

   if str.upper(model_str) == 'EC' or str.upper(model_str) == 'ECMWF':
      model_str = 'EC'
   elif str.upper(model_str) == 'UK' or str.upper(model_str) == 'UKMET' or str.upper(model_str) == 'EGRR':
      model_str = 'UK'
   elif str.upper(model_str) == 'ECENSMEAN' or str.upper(model_str) == 'ECMEAN' or str.upper(model_str) == 'EEMN':
      model_str = 'ECMEAN'
   elif str.upper(model_str) == 'AEMN':
      model_str = 'GEFSMEAN'

   f = open(DATA_DIR+'/'+str.lower(TC_name)+'_'+str.lower(model_str)+'_'+cycle+'.csv','wt')

   cycle_time = datetime.datetime(int(cycle[0:4]),int(cycle[4:6]),int(cycle[6:8]),int(cycle[8:10]))

   try:
      writer = csv.writer(f)
      print(cycle, cycles[i])
      while cycle == cycles[i]:
         valid_time = cycle_time + datetime.timedelta(hours=int(fhrs[i]))
      #  writer.writerow([fhrs[i],valid_time.strftime('%Y%m%d%H'),lats[i],lons[i],pres[i],vmax[i],rmw[i]])
         writer.writerow([fhrs[i],valid_time.strftime('%Y%m%d%H'),lats[i],lons[i],pres[i],vmax[i]])
         i += 1

         if i > len(cycles)-1:
            break

   finally:
      f.close()





