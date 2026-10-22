import time, os, sys
import numpy as np
import copy
from datetime import datetime, timedelta
import grib2io
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.colors as mcolors
import cartopy.crs as ccrs
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import cartopy.feature as cfeature
import io
from PIL import Image
import matplotlib.image as image
from matplotlib.gridspec import GridSpec
from scipy import ndimage
from netCDF4 import Dataset
import pyproj
import cartopy
import cartopy.io.shapereader as shpreader
from pathlib import Path
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from mpl_toolkits.axes_grid1 import make_axes_locatable

#####################################################
var = "ptype"

print(f"#############################################")

pdy = str(sys.argv[1])             # 20251120
cyc = str(sys.argv[2])		   # 12 
fhr = str(sys.argv[3])             # 024 (3 digits) 
grid = str(sys.argv[4])            # conus
DATA_PATH = str(sys.argv[5])       # /lfs/h2/emc/vpppg/noscrub/alicia.bentley/feb2026
MAP_PATH = str(sys.argv[6])        # /lfs/h2/emc/vpppg/noscrub/alicia.bentley/feb2026/maps
show_colorbar="yes"

print("pdy:", pdy)
print("cyc:", cyc)
print("fhr:", fhr)
print("grid:", grid)

init_str = str(pdy)
init_hour = int(cyc)

# strptime converts the string to a datetime object
init_dt = datetime.strptime(init_str, "%Y%m%d").replace(hour=init_hour)

# Create maps directory
Path(f"{MAP_PATH}/{grid}/{var}").mkdir(parents=True, exist_ok=True)

####################################################

# Use f-string to format with leading zeros (e.g., 000, 006)
fhr_str = f"{fhr}"
fcst_hour= int(fhr)
    
# Add the forecast lead time
forecast_delta = timedelta(hours=fcst_hour)
valid_dt = init_dt + forecast_delta

# Print the results in a readable format
print(f"Initialization Time: {init_dt.strftime('%Y-%m-%d %HZ')}")
print(f"Forecast Lead:       {fcst_hour} hours")
print(f"Valid Time:          {valid_dt.strftime('%Y-%m-%d %HZ')}")

# Open GFS GRIB2 file and extract parameters
filename_gfsv17 = f"/lfs/h2/emc/gfstemp/emc.global/EVS_archive/retrov17_01/gfs.{pdy}/{cyc}/products/atmos/grib2/0p25/gfs.t{cyc}z.pres_a.0p25.f{fhr_str}.grib2"
#filename_gfsv17 = f"/lfs/h2/emc/vpppg/noscrub/alicia.bentley/GFSv17archive/data/gfs.{pdy}/{cyc}/products/atmos/grib2/0p25/gfs.t{cyc}z.pres_a.0p25.f{fhr_str}.grib2"
with grib2io.open(filename_gfsv17) as f_gfsv17:

    # Select the message objects
    msg_refc = f_gfsv17.select(shortName='REFC')[0]
    msg_rain = f_gfsv17.select(shortName='CRAIN')[0]
    msg_frzr = f_gfsv17.select(shortName='CFRZR')[0]
    msg_icep = f_gfsv17.select(shortName='CICEP')[0]
    msg_snow = f_gfsv17.select(shortName='CSNOW')[0]

    # Extract latitude and longitude arrays from any message object
    lats, lons = msg_rain.latlons()

    # Extract data arrays and create masks
    refc_raw = msg_refc.data
    rain_raw = msg_rain.data
    frzr_raw = msg_frzr.data
    icep_raw = msg_icep.data
    snow_raw = msg_snow.data

    rain_mask = rain_raw > 0.5
    frzr_mask = frzr_raw > 0.5
    icep_mask = icep_raw > 0.5
    snow_mask = snow_raw > 0.5

    # Mask reflectivity directly
    #rain_data = np.where(rain_mask, refc_raw, -1)
    #frzr_data   = np.where(frzr_mask, refc_raw, -1)
    #icep_data   = np.where(icep_mask, refc_raw, -1)
    #snow_data   = np.where(snow_mask, refc_raw, -1)

# Shift longitudes from [0, 360] to [-180, 180]
lons = np.where(lons > 180, lons - 360, lons)

# If lons is a 2D meshgrid, we only want the 1D vector to get sort indices
# We'll take the first row of lons to determine the sorting order
if lons.ndim == 2:
	lons_1d = lons[0, :]
else:
	lons_1d = lons

# Get the sorting indices
i_sort = np.argsort(lons_1d)

# Apply sorting to the 2D arrays across the longitude axis (axis=1)
if lons.ndim == 2:
	lons = lons[:, i_sort]
	lats = lats[:, i_sort] # Sort lats too if it's a meshgrid
else:
	lons = lons[i_sort]

refc = refc_raw[:, i_sort]
rain = rain_mask[:, i_sort]
frzr = frzr_mask[:, i_sort]
icep = icep_mask[:, i_sort]
snow = snow_mask[:, i_sort]

#########################################################

# Define Reflectivity Thresholds (dBZ)
valid_refc  = (refc > -30) & (refc < 100)
light_mask  = valid_refc & (refc >= 0) & (refc < 20)
medium_mask = valid_refc & (refc >= 20) & (refc < 40)
heavy_mask  = valid_refc & (refc >= 40)

print("REFC max dBZ:", np.max(refc))
print("CRAIN count == 1:", np.sum(rain))

# Separate Categorized Reflectivity Arrays per Precip Type
# (Preserves continuous reflectivity values, masked out where inactive)

# Rain: 1 (Light), 2 (Medium), 3 (Heavy)
rain_cat = np.where(rain & light_mask, 1,
           np.where(rain & medium_mask, 2,
           np.where(rain & heavy_mask, 3, -1)))

# Snow: 4 (Light), 5 (Medium), 6 (Heavy)
snow_cat = np.where(snow & light_mask, 4,
           np.where(snow & medium_mask, 5,
           np.where(snow & heavy_mask, 6, -1)))

# Sleet / Ice Pellets: 7 (Light), 8 (Medium), 9 (Heavy)
icep_cat = np.where(icep & light_mask, 7,
           np.where(icep & medium_mask, 8,
           np.where(icep & heavy_mask, 9, -1)))

# Freezing Rain: 10 (Light), 11 (Medium), 12 (Heavy)
frzr_cat = np.where(frzr & light_mask, 10,
           np.where(frzr & medium_mask, 11,
           np.where(frzr & heavy_mask, 12, -1)))

#########################################################

# Create the Plot
if grid == 'northeast':
	fig = plt.figure(figsize=(12, 12))
elif grid == 'conus':
	fig = plt.figure(figsize=(15, 12))
elif grid == 'eastcoast':
        fig = plt.figure(figsize=(13, 12))
elif grid == 'southeastUS':
        fig = plt.figure(figsize=(12, 12))
elif grid == 'westcoast':
        fig = plt.figure(figsize=(13, 12))
elif grid == 'alaska':
        fig = plt.figure(figsize=(12, 12))
elif grid == 'easternUS':
        fig = plt.figure(figsize=(13, 12))
elif grid == 'florida':
        fig = plt.figure(figsize=(12, 12))
elif grid == 'gulf':
        fig = plt.figure(figsize=(12, 12))

# Define a 2x2 grid
gs = gridspec.GridSpec(1, 1, figure=fig)

rain_levs = [0.5, 1.5, 2.5, 3.5]
snow_levs = [3.5, 4.5, 5.5, 6.5]
icep_levs = [6.5, 7.5, 8.5, 9.5]
frzr_levs = [9.5, 10.5, 11.5, 12.5]

snowhex=["#64B3E8", "#3E7CC6", "#1945A4"]
rainhex=["#4EEE94", "#43CD80", "#2E8B57"]
sleethex=["#947EEC", "#6B47AB", "#42106A"]
freezehex=["#E65956", "#D93B3A", "#CC1E1E"]

rain_cmap, rain_norm = mcolors.from_levels_and_colors(rain_levs, rainhex)
snow_cmap, snow_norm = mcolors.from_levels_and_colors(snow_levs, snowhex)
icep_cmap, icep_norm = mcolors.from_levels_and_colors(icep_levs, sleethex)
frzr_cmap, frzr_norm = mcolors.from_levels_and_colors(frzr_levs, freezehex)

# Define the grid locations: [row, col] or [row, span]
# gs[0, 0] = Top Left, gs[0, 1] = Top Right, gs[1, :] = Bottom Center
grid_locs = [gs[0, 0]]

for i, loc in enumerate(grid_locs):
	# Add subplot with projection
    ax = fig.add_subplot(loc, projection=ccrs.PlateCarree())

    # Determine the appropriate scale based on the domain
    state_scale = '10m' if grid != "conus" else '50m'

    # Fetch STATES with the lakes strictly cut out
    states_clipped = cfeature.NaturalEarthFeature(category='cultural', name='admin_1_states_provinces_lakes', scale=state_scale, facecolor='none')

    # Fetch COUNTRIES with the lakes strictly cut out (Replaces cfeature.BORDERS)
    countries_clipped = cfeature.NaturalEarthFeature(category='cultural', name='admin_0_countries_lakes', scale=state_scale, facecolor='none')

    # Geographic features
    ax.add_feature(cfeature.LAKES, facecolor='white', edgecolor='0.25', linewidth=1.0, zorder=2)
    ax.add_feature(states_clipped, edgecolor='0.25', linewidth=1.5, zorder=4)
    ax.add_feature(cfeature.COASTLINE, edgecolor='0.25', linewidth=1.5, zorder=4)
    ax.add_feature(countries_clipped, edgecolor='0.25', linewidth=1.5, zorder=4)

	# Define domain
    if grid == 'northeast':   
        ax.set_extent([-82, -67, 38.75, 45.75], crs=ccrs.PlateCarree())
        # Increase this number (e.g., 1.4) to stretch it more vertically
        ax.set_aspect(1.25, adjustable='datalim')
    elif grid == 'conus':                
        ax.set_extent([-125, -64, 22, 57], crs=ccrs.PlateCarree())
        # Increase this number (e.g., 1.4) to stretch it more vertically
        ax.set_aspect(1.2, adjustable='datalim')
    elif grid == 'eastcoast':
        ax.set_extent([-82, -57, 25.0, 48.0], crs=ccrs.PlateCarree())
        # Increase this number (e.g., 1.4) to stretch it more vertically
        ax.set_aspect(1.25, adjustable='datalim')
    elif grid == 'southeastUS':
        #ax.set_extent([-89, -76, 19.0, 34.0], crs=ccrs.PlateCarree())
        ax.set_extent([-86, -81, 21.0, 32.0], crs=ccrs.PlateCarree())
        # Increase this number (e.g., 1.4) to stretch it more vertically
        ax.set_aspect(1.25, adjustable='datalim')
    elif grid == 'westcoast':
        ax.set_extent([-148, -116, 29.0, 61.0], crs=ccrs.PlateCarree())
        # Increase this number (e.g., 1.4) to stretch it more vertically
        ax.set_aspect(1.25, adjustable='datalim')
    elif grid == 'alaska':
        ax.set_extent([-180, -130, 50.0, 70.0], crs=ccrs.PlateCarree())
        # Increase this number (e.g., 1.4) to stretch it more vertically
        ax.set_aspect(1.6, adjustable='datalim')
    elif grid == 'easternUS':
        ax.set_extent([-97, -72, 25.0, 48.0], crs=ccrs.PlateCarree())
        # Increase this number (e.g., 1.4) to stretch it more vertically
        ax.set_aspect(1.25, adjustable='datalim')
    elif grid == 'florida':
        ax.set_extent([-86, -81, 23.0, 34.0], crs=ccrs.PlateCarree())
        # Increase this number (e.g., 1.4) to stretch it more vertically
        ax.set_aspect(1.25, adjustable='datalim')
    elif grid == 'gulf':
        ax.set_extent([-88, -85, 24.0, 34.0], crs=ccrs.PlateCarree())
        # ax.set_extent([-93, -85, 18.0, 33.0], crs=ccrs.PlateCarree()
        ax.set_aspect(1.25, adjustable='datalim')

    print("Rain array min/max:", np.min(rain_cat), np.max(rain_cat))
    print("Rain unique values:", np.unique(rain_cat))

	# Plot the shading
    csrain_1 = ax.contourf(lons,lats,rain_cat,rain_levs,cmap=rain_cmap,norm=rain_norm,transform=ccrs.PlateCarree(),extend='neither',zorder=3)
    cssnow_1 = ax.contourf(lons,lats,snow_cat,snow_levs,cmap=snow_cmap,norm=snow_norm,transform=ccrs.PlateCarree(),extend='neither',zorder=3)
    csicep_1 = ax.contourf(lons,lats,icep_cat,icep_levs,cmap=icep_cmap,norm=icep_norm,transform=ccrs.PlateCarree(),extend='neither',zorder=3)
    csfrzr_1 = ax.contourf(lons,lats,frzr_cat,frzr_levs,cmap=frzr_cmap,norm=frzr_norm,transform=ccrs.PlateCarree(),extend='neither',zorder=3)

    rain_ticks = [1, 2, 3]
    snow_ticks = [4, 5, 6]
    icep_ticks = [7, 8, 9]
    frzr_ticks = [10, 11, 12]

    # 1. Create a hidden container axis below 'ax' 
    # [left, bottom, width, height] relative to ax (0,0 is bottom-left of map)
    cbar_ax = ax.inset_axes([0.0, -0.12, 1.0, 0.05])
    cbar_ax.axis('off')  # Hide container frame so no phantom boxes appear

    # 2. Divide 'cbar_ax' into 4 perfectly equal & spaced sub-axes
    caxrain = cbar_ax.inset_axes([0.01, 0.0, 0.20, 1.0])
    caxsnow = cbar_ax.inset_axes([0.27, 0.0, 0.20, 1.0])
    caxicep = cbar_ax.inset_axes([0.53, 0.0, 0.20, 1.0])
    caxfrzr = cbar_ax.inset_axes([0.79, 0.0, 0.20, 1.0])

    # Colorbar for Rain
    cbrain = fig.colorbar(csrain_1, cax=caxrain, ticks=rain_ticks, orientation='horizontal')
    cbrain.ax.set_xticklabels(['light', '', 'heavy'])
    cbrain.ax.tick_params(labelsize=13)
    cbrain.set_label('Rain', fontsize=17, fontweight='bold')

    cbsnow = fig.colorbar(cssnow_1, cax=caxsnow, ticks=snow_ticks, orientation='horizontal')
    cbsnow.ax.set_xticklabels(['light', '', 'heavy'])
    cbsnow.ax.tick_params(labelsize=13)
    cbsnow.set_label('Snow', fontsize=17, fontweight='bold')

    cbicep = fig.colorbar(csicep_1, cax=caxicep, ticks=icep_ticks, orientation='horizontal')
    cbicep.ax.set_xticklabels(['light', '', 'heavy'])
    cbicep.ax.tick_params(labelsize=13)
    cbicep.set_label('Sleet', fontsize=17, fontweight='bold')

    cbfrzr = fig.colorbar(csfrzr_1, cax=caxfrzr, ticks=frzr_ticks, orientation='horizontal')
    cbfrzr.ax.set_xticklabels(['light', '', 'heavy'])
    cbfrzr.ax.tick_params(labelsize=13)
    cbfrzr.set_label('Freezing Rain', fontsize=17, fontweight='bold')

    ax.set_title(f'GFSv17 | Precipitation Type (p-type)\nInitialized: {init_dt.strftime("%Y-%m-%d %HZ")} (F{fhr_str}) | Valid: {valid_dt.strftime("%Y-%m-%d %HZ")}', fontweight='bold', fontsize=24)

#################################################

# Add a title and adjust layout to prevent overlapping
plt.tight_layout()
plt.savefig(f"{MAP_PATH}/{grid}/{var}/gfsv17_{var}_init{pdy}_{cyc}Z_f{fhr}.png", bbox_inches='tight', pad_inches=0.1)
