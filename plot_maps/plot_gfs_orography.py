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
import xarray as xr

#####################################################
var = "orography"

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

#Create the datetime object
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
filename_gfs = f"/lfs/h1/ops/prod/com/gfs/v16.3/gfs.{pdy}/{cyc}/atmos/gfs.t{cyc}z.sfcanl.nc"

# 1. Open the NetCDF dataset
ds = xr.open_dataset(filename_gfs)

# 2. Extract 'orog' and drop extra dimensions if present (e.g., time)
orog = ds['orog']
if 'time' in orog.dims:
    orog = orog.isel(time=0)

# Squeeze out any single-length dimensions
orog = orog.squeeze()

# Convert orog from meters to feet
orog_ft = orog * 3.28084

# 3. Extract lat and lon coordinates
# Common dimension names in GFS NetCDF are 'latitude'/'longitude' or 'lat'/'lon'
lat_name = 'latitude' if 'latitude' in ds else 'lat'
lon_name = 'longitude' if 'longitude' in ds else 'lon'

lats = ds[lat_name].values
lons = ds[lon_name].values

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

# Define a 2x2 grid
gs = gridspec.GridSpec(1, 1, figure=fig)

# Grab original terrain colormap
orig_terrain = plt.get_cmap('terrain')

# Slice from 0.25 to 1.0 (removes the bottom blue ~25%)
land_terrain = mcolors.LinearSegmentedColormap.from_list(
    'land_terrain', orig_terrain(np.linspace(0.30, 1.0, 256))
)

# Update configs
plot_configs = [
	{'title': f'GFSv16 Orography (ft)\nSurface Analysis'},
]

# Define the grid locations: [row, col] or [row, span]
# gs[0, 0] = Top Left, gs[0, 1] = Top Right, gs[1, :] = Bottom Center
grid_locs = [gs[0, 0]]

for i, loc in enumerate(grid_locs):
    config = plot_configs[i]

	# Add subplot with projection
    ax = fig.add_subplot(loc, projection=ccrs.PlateCarree())

	# Geographic features
    ax.add_feature(cfeature.BORDERS, edgecolor='0.3', linewidth=2.0, zorder=3)
    ax.add_feature(cfeature.STATES, edgecolor='0.3', linewidth=2.0, zorder=3)
    ax.add_feature(cfeature.LAKES, facecolor='white', edgecolor='0.25', linewidth=1.0, zorder=4)
    ax.add_feature(cfeature.OCEAN, facecolor='white', edgecolor='0.25', linewidth=1.0, zorder=2)
    ax.add_feature(cfeature.COASTLINE, edgecolor='0.3', linewidth=2.0, zorder=3)

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

	# Plot the shading
	# Note: CONUS = levels=np.arange(0, 13500, 500),
    im = ax.contourf(lons, lats, orog_ft, 
		     levels=np.arange(0, 7250, 250),
		     cmap=land_terrain,
		     extend='max',
		     transform=ccrs.PlateCarree(),
		     zorder=1
    )

	# Capture the colorbar in a variable (e.g., 'cbar')
    #cbar = plt.colorbar(im, ax=ax, orientation='horizontal', pad=0.06, fraction=0.055)
    if grid == 'alaska':
        cbar = plt.colorbar(im, ax=ax, orientation='horizontal', pad=0.06, fraction=0.045)
    elif grid == 'conus':
        cbar = plt.colorbar(im, ax=ax, orientation='horizontal', pad=0.06, fraction=0.055, ticks=np.arange(0, 15000, 2000))
    else:
        cbar = plt.colorbar(im, ax=ax, orientation='horizontal', pad=0.06, fraction=0.055, ticks=np.arange(0, 8000, 1000))

    ax.set_title(config['title'], fontweight='bold', fontsize=24)

	# Set the label size for the ticks
    cbar.ax.tick_params(labelsize=24)

#################################################

# Add a title and adjust layout to prevent overlapping
#plt.suptitle(f"GFSv16 | 500-hPa Geopotential Height (dam) | Initialized: {init_dt.strftime('%Y-%m-%d %HZ')} (Fhr: {fhr_str}) | Valid: {valid_dt.strftime('%Y-%m-%d %HZ')}", fontsize=20)
plt.tight_layout()
plt.savefig(f"{MAP_PATH}/{grid}/{var}/gfsv16_{var}_init{pdy}_{cyc}Z_f{fhr}.png", bbox_inches='tight', pad_inches=0.1)
