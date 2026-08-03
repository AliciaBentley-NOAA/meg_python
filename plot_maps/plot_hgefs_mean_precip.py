import time, os, sys
import numpy as np
import subprocess
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

#####################################################
var = "precip"

pdy = str(sys.argv[1])             # 20251120
cyc = str(sys.argv[2])             # 12
fhr = str(sys.argv[3])             # 024 (3 digits)
grid = str(sys.argv[4])            # conus
DATA_PATH = str(sys.argv[5])       # /lfs/h2/emc/vpppg/noscrub/alicia.bentley/feb2026
MAP_PATH = str(sys.argv[6])        # /lfs/h2/emc/vpppg/noscrub/alicia.bentley/feb2026/maps
duration = str(sys.argv[7])        # 36 (hours)
vpdy = str(sys.argv[8])            # 20251121
vhr = str(sys.argv[9])             # 12

show_colorbar="yes"

print("pdy:", pdy)
print("cyc:", cyc)
print("grid:", grid)
print("vpdy:", vpdy)
print("vhr:", vhr)
print("duration:", duration)

init_str = str(pdy)
init_hour = int(cyc)
valid_str = str(vpdy)
valid_hour = int(vhr)

#Create the datetime object
# strptime converts the string to a datetime object
init_dt = datetime.strptime(init_str, "%Y%m%d").replace(hour=init_hour)
valid_dt = datetime.strptime(valid_str, "%Y%m%d").replace(hour=valid_hour)

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
ccpa_delta = timedelta(hours=6)
start_dt = valid_dt - duration_delta
current_dt = start_dt

# Print the results in a readable format
print(f"Initialization Time: {init_dt.strftime('%Y-%m-%d %HZ')}")
print(f"Forecast Lead:       {fcst_hour} hours")
print(f"Start Time:          {start_dt.strftime('%Y-%m-%d %HZ')}")
print(f"Valid Time:          {valid_dt.strftime('%Y-%m-%d %HZ')}")

# Determine how many 6-hour periods are in the full duration (e.g., 24h/6h)
segments = int(duration) / int(6)
print(f"Number of CCPA files needed: {segments}")

gefs_array = np.zeros((int(segments), 721, 1440), dtype=np.float32)

for j in range(int(segments)):

    # Remember: Valid time in filenames is at the *end* of the 6-h period (add ccpa_delta)
    current_dt = current_dt + ccpa_delta
    print(f"Current GEFS File Time: {current_dt.strftime('%Y-%m-%d %HZ')}")

    # Subtract datetime objects to get a timedelta
    time_diff = valid_dt - current_dt

    # Convert time_diff to hours
    hours_diff = int(time_diff.total_seconds() // 3600)

    # Make sure fhr is an integer when subtracting
    fhr_new = int(fhr) - hours_diff

    # FIXED: fhr_new is already an integer in hours!
    fhr_int = fhr_new

    # Format as a string (e.g., "006", "024", or "120" with 3-digit zero-padding)
    fhr_str = f"{fhr_int:03d}"
    print(fhr_str)

    # Open GEFS GRIB2 file at the start of the snowfall period and extract parameters
    filename_gefs = f"{DATA_PATH}/hgefs.{pdy}/{cyc}/atmos/hgefs.t{cyc}z.sfc.avg.f{fhr_str}.grib2"
    print(filename_gefs)
    with grib2io.open(filename_gefs) as f_gefs:

      try:
        # Select the specific messages we want
        precip_msg = f_gefs.select(shortName='APCP')[0]

        # Extract values
        precip_data = precip_msg.data * 0.0393701 # Convert mm to inches

        print(f"Extracted: {precip_msg.shortName} for {precip_msg.leadTime} hours")
        print(f"Max Precip: {precip_data.max():.2f} inches")

      except (IndexError, ValueError):
        # APCP doesn't exist (Hour 0) -> Load MSLP and set values to 0.0
        precip_msg = f_gefs.select(shortName='PRMSL')[0]
        precip_data = np.zeros_like(precip_msg.data, dtype=np.float32)
            
      gefs_array[j, :, :] = precip_data

      print(f"Success! Loaded {current_dt} for {j} into CCPA array.")

      lats, lons = precip_msg.latlons()

# Sum across the time segments (axis 0)
# This gives you a 2D map of the total accumulation
diff_data = np.sum(gefs_array, axis=0)

# Finding the values
minimum = np.min(diff_data)
maximum = np.max(diff_data)

# Printing the results
print(f"The minimum precip is: {minimum}")
print(f"The maximum precip is: {maximum}")

#########################################################


#########################################################

# Create the Plot
if grid == 'northeast':
	fig = plt.figure(figsize=(12, 12))
elif grid == 'conus':
	fig = plt.figure(figsize=(15, 12))
elif grid == 'eastcoast':
        fig = plt.figure(figsize=(13, 12))
elif grid == 'westcoast':
        fig = plt.figure(figsize=(12, 12))
elif grid == 'easternUS':
        fig = plt.figure(figsize=(13, 12))

# Define a 2x2 grid
gs = gridspec.GridSpec(1, 1, figure=fig)

# Define the specific normalization (Panel 1)
snod_levels = np.array([0.01, 0.1, 0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.5, 3, 4, 5, 6, 8, 10, 12])

snod_colors = [
    '#33ff00', # 0.01 - 0.1  (Bright Green)
    '#00cd00', # 0.1 - 0.25  (Medium Green)
    '#008b00', # 0.25 - 0.5  (Dark Green)
    '#104e8b', # 0.5 - 0.75  (Deep Blue)
    '#1e90ff', # 0.75 - 1.0  (Dodger Blue)
    '#00b2ee', # 1.0 - 1.25  (Sky Blue)
    '#00eeee', # 1.25 - 1.5  (Cyan)
    '#8968cd', # 1.5 - 1.75  (Medium Purple)
    '#912cee', # 1.75 - 2.0  (Vibrant Purple)
    '#8b008b', # 2.0 - 2.5   (Dark Magenta)
    '#8b0000', # 2.5 - 3.0   (Dark Red)
    '#cd0000', # 3.0 - 4.0   (Red)
    '#ee0000', # 4.0 - 5.0   (Bright Red)
    '#ff7f00', # 5.0 - 7.0   (Orange)
    '#cd8500', # 7.0 - 10.0  (Gold/Tan)
    '#ffd700', # 10.0 - 15.0 (Goldenrod)
    '#ffff00', # 15.0 - 20.0 (Yellow)
]

cmap = mcolors.ListedColormap(snod_colors)
cmap.set_under(color='none')
cmap.set_over('tan')

norm = mcolors.BoundaryNorm(snod_levels, ncolors=len(snod_colors))

# Update configs with specific 'norm' and 'levels'
plot_configs = [
	{'data': diff_data, 'cmap': cmap, 'norm': norm, 'levels': snod_levels, 'title': f'HGEFS mean | {duration}-h Accumulated Precipitation (in.)\nInitialized: {init_dt.strftime("%Y-%m-%d %HZ")} (F{fhr_str}) | Valid: {valid_dt.strftime("%Y-%m-%d %HZ")}'},
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
    elif grid == 'westcoast':
        ax.set_extent([-124.0, -108.0, 31.0, 50.0], crs=ccrs.PlateCarree())
        # Increase this number (e.g., 1.4) to stretch it more vertically
        ax.set_aspect(1.25, adjustable='datalim')
    elif grid == 'easternUS':
        ax.set_extent([-97, -72, 25.0, 48.0], crs=ccrs.PlateCarree())
        # Increase this number (e.g., 1.4) to stretch it more vertically
        ax.set_aspect(1.25, adjustable='datalim')

	# Plot the shading
    im = ax.contourf(lons, lats, config['data'], 
		     levels=config['levels'],
		     norm=config['norm'], 
		     cmap= config['cmap'],
		     transform=ccrs.PlateCarree(),
		     extend='max')

	# Capture the colorbar in a variable (e.g., 'cbar')
    cbar = plt.colorbar(im, ax=ax, ticks=snod_levels, orientation='horizontal', pad=0.06, fraction=0.061, shrink=0.95) # fraction is height, shrink is width
    ax.set_title(config['title'], fontweight='bold', fontsize=24)

	# Set the label size for the ticks
    cbar.ax.tick_params(labelsize=20)

	# Optional: Ensure the labels are formatted nicely (e.g., no extra decimals)
    cbar.ax.set_xticklabels([f'{l:g}' for l in snod_levels])

#################################################

# Add a title and adjust layout to prevent overlapping
plt.tight_layout()
plt.savefig(f"{MAP_PATH}/{grid}/{var}/hgefs_{var}_init{pdy}_{cyc}Z_f{fhr}.png", bbox_inches='tight', pad_inches=0.1)
