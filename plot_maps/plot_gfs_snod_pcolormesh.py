import time, os, sys
import numpy as np
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
import subprocess

#####################################################
var = "snod"

pdy = str(sys.argv[1])             # 20251120
cyc = str(sys.argv[2])		   # 12 
fhr = str(sys.argv[3])             # 024 (3 digits) 
grid = str(sys.argv[4])            # conus
DATA_PATH = str(sys.argv[5])       # /lfs/h2/emc/vpppg/noscrub/alicia.bentley/feb2026
MAP_PATH = str(sys.argv[6])        # /lfs/h2/emc/vpppg/noscrub/alicia.bentley/feb2026/maps
duration = str(sys.argv[7])        # 36 (hours)

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
duration_hour = int(duration)
start_fhr = fcst_hour - duration_hour
start_fhr_str = f"{start_fhr:03}"
    
# Add the forecast lead time
forecast_delta = timedelta(hours=fcst_hour)
duration_delta = timedelta(hours=duration_hour)
nohrsc_delta = timedelta(hours=6)
valid_dt = init_dt + forecast_delta
start_dt = valid_dt - duration_delta    # Remember: Valid time in NOHRSC filenames is at the *end* of the 6-h period

# Print the results in a readable format
print(f"Initialization Time: {init_dt.strftime('%Y-%m-%d %HZ')}")
print(f"Forecast Lead:       {fcst_hour} hours")
print(f"Start Time:          {start_dt.strftime('%Y-%m-%d %HZ')}")
print(f"Valid Time:          {valid_dt.strftime('%Y-%m-%d %HZ')}")

# Open GFS GRIB2 file at the start of the snowfall period and extract parameters
filename_gfss = f"{DATA_PATH}/gfs.{pdy}/{cyc}/atmos/gfs.t{cyc}z.pgrb2.0p25.f{start_fhr_str}"
with grib2io.open(filename_gfss) as f_gfss:

        # Select the specific messages we want
        snod_start_msg = f_gfss.select(shortName='SNOD', level='surface')[0]

        # Extract values
        snod_start_data = snod_start_msg.data * 39.3701  # Convert meters to inches

# Open GFS GRIB2 file at the end of the snowfall period and extract parameters
filename_gfs = f"{DATA_PATH}/gfs.{pdy}/{cyc}/atmos/gfs.t{cyc}z.pgrb2.0p25.f{fhr_str}"
with grib2io.open(filename_gfs) as f_gfs:

        # Select the specific messages we want
        snod_msg = f_gfs.select(shortName='SNOD', level='surface')[0]

        # Extract values
        snod_data = snod_msg.data * 39.3701  # Convert meters to inches

        # Calculate the difference (e.g., SNOD at end - SNOD at start)
        diff_data = snod_data - snod_start_data

        lats, lons = snod_msg.latlons()

print(f"DEBUG: Lon min: {lons.min()}, max: {lons.max()}")
print(f"DEBUG: Lat min: {lats.min()}, max: {lats.max()}")

print(f"Data Shape: {diff_data.shape}")
print(f"X Mesh Shape: {lons.shape}") # Should match Data Shape
print(f"Y Mesh Shape: {lats.shape}") # Should match Data Shape

# 1. Collapse the 2D mesh back to 1D axes (721 and 1440)
# We take the first column of lats and the first row of lons
lats_1d = lats[:, 0]
lons_1d = lons[0, :]

# 2. Shift Longitudes from 0-360 to -180-180
# This math moves everything > 180 (like 285) into the negative space (like -75)
lons_1d = np.where(lons_1d > 180, lons_1d - 360, lons_1d)

# 3. CRITICAL: GFS 0-360 data is often NOT sorted once shifted to -180/180
# We must sort them so the slicing [start:end] doesn't return an empty array
sort_idx = np.argsort(lons_1d)
lons_1d = lons_1d[sort_idx]

# 4. Sort the data array to match the new longitude order
# This keeps the weather over the US and not the Indian Ocean
diff_data = diff_data[:, sort_idx]

print(f"NEW Lon Range: {lons_1d.min()} to {lons_1d.max()}")
print(f"NEW Lon Shape: {lons_1d.shape}")

# 1. Find the 1D indices for the Northeast
# West: -100, East: -60, South: 20, North: 55
idx_w = np.abs(lons_1d - (-100)).argmin()
idx_e = np.abs(lons_1d - (-60)).argmin()
idx_s = np.abs(lats_1d - 20).argmin()
idx_n = np.abs(lats_1d - 55).argmin()

# 2. Define the slice ranges (min/max ensures order doesn't matter)
lon_slice = slice(min(idx_w, idx_e), max(idx_w, idx_e) + 1)
lat_slice = slice(min(idx_n, idx_s), max(idx_n, idx_s) + 1)

# 3. Create the subset arrays
lons_sub = lons_1d[lon_slice]
lats_sub = lats_1d[lat_slice]
data_sub = diff_data[lat_slice, lon_slice]

#########################################################


#########################################################

# Create the Plot
if grid == 'northeast':
        fig = plt.figure(figsize=(12, 10))
elif grid == 'conus':
        fig = plt.figure(figsize=(15, 12))
elif grid == 'eastcoast':
        fig = plt.figure(figsize=(13, 12))

# Define a 2x2 grid
gs = gridspec.GridSpec(1, 1, figure=fig)

# Define the colorbar
snod_levels = np.array([0.1, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0, 18.0, 24.0, 30.0, 36.0, 48.0, 60.0])
snod_colors = ['#749DDE', '#588ADC', '#2F74C8', '#2364B9', '#1E559D', '#FFF68F', '#F4C430', '#ED781E', '#E23916', '#C92828', '#D986D9', '#D95DD9', '#CD0ACD']

cmap = mcolors.ListedColormap(snod_colors)
#cmap.set_under('white')
#cmap.set_over('#CD0ACD')

# Mask values that are clearly 'missing' (usually > 100 inches) 
# or zero (to keep the ocean clean)
data_sub = np.where((data_sub > 100.0) | (data_sub < 0.1), np.nan, data_sub)

norm = mcolors.BoundaryNorm(snod_levels, ncolors=len(snod_colors))

# Update configs with specific 'norm' and 'levels'
plot_configs = [
	{'data': data_sub, 'cmap': cmap, 'norm': norm, 'levels': snod_levels, 'title': f'GFS | {duration}-h Positive Change in Snow Depth (in.)\nInitialized: {init_dt.strftime("%Y-%m-%d %HZ")} (F{fhr_str}) | Valid: {valid_dt.strftime("%Y-%m-%d %HZ")}'},
]

# Define the grid locations: [row, col] or [row, span]
# gs[0, 0] = Top Left, gs[0, 1] = Top Right, gs[1, :] = Bottom Center
grid_locs = [gs[0, 0]]

for i, loc in enumerate(grid_locs):
	config = plot_configs[i]

	# Add subplot with projection
	ax = fig.add_subplot(loc, projection=ccrs.PlateCarree())

	# Geographic features
	ax.add_feature(cfeature.STATES, edgecolor='0.25', linewidth=2.0)
	ax.add_feature(cfeature.COASTLINE, edgecolor='0.25', linewidth=1.5)
	ax.add_feature(cfeature.BORDERS, edgecolor='0.25', linewidth=1.5)
	ax.add_feature(cfeature.LAKES, facecolor='white', edgecolor='0.25', linewidth=1.0)

	# Add the land feature and shade it gray
	ax.add_feature(cfeature.LAND, facecolor='lightgray', edgecolor='none')
	# Add oceans for contrast (optional)
	#ax.add_feature(cfeature.OCEAN, facecolor='lightblue')

	# Define domain
	if grid == 'northeast':
		ax.set_extent([-82.5, -66.5, 39.25, 45.25], crs=ccrs.PlateCarree())
		# Add manual aspect ratio here. 
		# Increase this number (e.g., 1.4) to stretch it more vertically
		ax.set_aspect(1.25, adjustable='datalim')
	elif grid == 'conus':                
		ax.set_extent([-125, -64, 22, 57], crs=ccrs.PlateCarree())
		# Add manual aspect ratio here. 
		# Increase this number (e.g., 1.4) to stretch it more vertically
		ax.set_aspect(1.2, adjustable='datalim')
	elif grid == 'eastcoast':
		ax.set_extent([-82, -57, 25.0, 48.0], crs=ccrs.PlateCarree())
		# Add manual aspect ratio here. 
		# Increase this number (e.g., 1.4) to stretch it more vertically
		ax.set_aspect(1.25, adjustable='datalim')

        # 1. Define the Globe (The 'NCEP Sphere')
        # This is the most common reason for shifted high-res grids!
	ncep_globe = ccrs.Globe(ellipse=None, semimajor_axis=6371229, semiminor_axis=6371229)

        # 2. Update the Projection to use this globe
#       nohrsc_proj = ccrs.LambertConformal(central_longitude=-95.0,
#                                    central_latitude=25.0,
#                                    standard_parallels=(25.0, 25.0),
#                                    globe=ncep_globe)
	map_proj = ccrs.PlateCarree(globe=ncep_globe)

	# 4. Create the regional Meshgrid
	X_sub, Y_sub = np.meshgrid(lons_sub, lats_sub)

	print(f"FINAL CHECK: Lon Range: {lons_sub.min()} to {lons_sub.max()}")
	print(f"FINAL CHECK: Data Shape: {data_sub.shape}") # Should be ~ (141, 161)

	# Plot the shading
	im = ax.pcolormesh(X_sub, Y_sub, data_sub,
		   shading='nearest',
		   cmap=config['cmap'],
		   norm=config['norm'],
		   clip_on=True, # Extra safety for the coordinate math
		   zorder=1)

	## Plot the contour lines
	## Only add lines if it's one of the MSLP panels (0 or 1)
	#contours = ax.contour(lons, lats, config['data'], 
	#		      levels=config['levels'], 
	#		      colors='black', 
	#		      linewidths=2.0, 
	#		      transform=ccrs.PlateCarree())
	## Add labels to the lines (e.g., '1012')
	## Reduce padding (default is 4) to allow more labels to fit in tight spaces
	#ax.clabel(contours, inline=True, fontsize=18, fmt='%i', inline_spacing=1)

        # Capture the colorbar in a variable (e.g., 'cbar')
        cbar = plt.colorbar(im, ax=ax, ticks=snod_levels, orientation='horizontal', pad=0.06, fraction=0.055, shrink=0.95) # fraction is height, shrink is width
        ax.set_title(config['title'], fontweight='bold', fontsize=18)

        # Set the label size for the ticks
        cbar.ax.tick_params(labelsize=20)

        # Optional: Ensure the labels are formatted nicely (e.g., no extra decimals)
        cbar.ax.set_xticklabels([f'{l:g}' for l in snod_levels])

#################################################

# Add a title and adjust layout to prevent overlapping
#plt.suptitle(f"GFS | 500-hPa Geopotential Height (dam) | Initialized: {init_dt.strftime('%Y-%m-%d %HZ')} (Fhr: {fhr_str}) | Valid: {valid_dt.strftime('%Y-%m-%d %HZ')}", fontsize=20)
plt.tight_layout()
plt.savefig(f"{MAP_PATH}/{grid}/{var}/gfsv16_{var}_init{pdy}_{cyc}Z_f{fhr}.png", bbox_inches='tight', pad_inches=0.1)
