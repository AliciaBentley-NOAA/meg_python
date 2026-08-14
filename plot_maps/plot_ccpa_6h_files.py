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
from metpy.plots import USCOUNTIES

#####################################################
var = "ccpa"

print(f"#############################################")

pdy = str(sys.argv[1])             # 20251120
cyc = str(sys.argv[2])		   # 12 
grid = str(sys.argv[3])            # conus
DATA_PATH = str(sys.argv[4])       # /lfs/h2/emc/vpppg/noscrub/alicia.bentley/feb2026
MAP_PATH = str(sys.argv[5])        # /lfs/h2/emc/vpppg/noscrub/alicia.bentley/feb2026/maps
duration = str(sys.argv[6])        # 36 (hours)

show_colorbar="yes"

print("pdy:", pdy)
print("cyc:", cyc)
print("grid:", grid)

valid_str = str(pdy)
valid_hour = int(cyc)

# strptime converts the string to a datetime object
valid_dt = datetime.strptime(valid_str, "%Y%m%d").replace(hour=valid_hour)

# Create maps directory
Path(f"{MAP_PATH}/{grid}/{var}").mkdir(parents=True, exist_ok=True)

####################################################

# Use f-string to format with leading zeros (e.g., 000, 006)
duration_hour = int(duration)
    
# Add the forecast lead time
duration_delta = timedelta(hours=duration_hour)
ccpa_delta = timedelta(hours=6)
start_dt = valid_dt - duration_delta
current_dt = start_dt

# Print the results in a readable format
print(f"Start Time:          {start_dt.strftime('%Y-%m-%d %HZ')}")
print(f"Valid Time:          {valid_dt.strftime('%Y-%m-%d %HZ')}")

#---------------------------------------------------------
#---------------------------------------------------------
#---------------------------------------------------------

# Determine how many 6-hour periods are in the full duration (e.g., 24h/6h)
segments = int(duration) / int(6) 
print(f"Number of CCPA files needed: {segments}")

ccpa_array = np.zeros((int(segments), 881, 1121), dtype=np.float32)

for j in range(int(segments)):

    # Remember: Valid time in CCPA filenames is at the *end* of the 6-h period (add ccpa_delta)
    current_dt = current_dt + ccpa_delta
    print(f"Current CCPA File Time: {current_dt.strftime('%Y-%m-%d %HZ')}")
    date_string = current_dt.strftime('%Y%m%d%H')

    # Open 6-h CCPA file 
    filename_ccpa = f"{DATA_PATH}/ccpa.hrap.{date_string}.6h"
    with grib2io.open(filename_ccpa) as f_ccpa:

        # Extract the message and data
        precip_msg = f_ccpa[0]
        precip_data = precip_msg.data
    
    ccpa_array[j, :, :] = precip_data

    print(f"Success! Loaded {date_string} into index {j} into CCPA array.")

    lats, lons = precip_msg.latlons()

# Sum across the time segments (axis 0) 
ccpa_total = np.sum(ccpa_array, axis=0) * 0.0393701   # convert mm to inches

# This tells us the exact lat/lon bounds wgrib2 sees in the file
#result = subprocess.run(f"wgrib2 {filename_ccpa} -grid", shell=True, capture_output=True, text=True)
#print(result.stdout)

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
#precip_levels = np.array([0.01, 0.1, 0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.5, 3, 4, 5, 7, 10, 15, 20])
precip_levels = np.array([0.01, 0.1, 0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.5, 3, 4, 5, 6, 8, 10, 12])

precip_colors = [
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

cmap = mcolors.ListedColormap(precip_colors)
cmap.set_over('tan')

norm = mcolors.BoundaryNorm(precip_levels, ncolors=len(precip_colors))

# Update configs with specific 'norm' and 'levels'
plot_configs = [
    {'data': ccpa_total, 'cmap': cmap, 'norm': norm, 'levels': precip_levels, 'title': f'CCPA | {duration}-h Accumulated Precipitation (in.)\nValid: {start_dt.strftime("%Y-%m-%d %HZ")} - {valid_dt.strftime("%Y-%m-%d %HZ")}'},
]

# Define the grid locations: [row, col] or [row, span]
grid_locs = [gs[0, 0]]

for i, loc in enumerate(grid_locs):
    config = plot_configs[i]

    # Add subplot with projection
    ax = fig.add_subplot(loc, projection=ccrs.PlateCarree())

    # Geographic features
    ax.add_feature(cfeature.STATES, edgecolor='0.25', linewidth=2.5)
    ax.add_feature(cfeature.COASTLINE, edgecolor='0.25', linewidth=2.0)
    ax.add_feature(cfeature.BORDERS, edgecolor='0.25', linewidth=2.0)
    ax.add_feature(cfeature.LAKES, facecolor='white', edgecolor='0.25', linewidth=1.5)
    ax.add_feature(USCOUNTIES, edgecolor='black', linewidth=0.3, alpha=0.6)

    # Add the land feature and shade it gray
    ax.add_feature(cfeature.LAND, facecolor='lightgray', edgecolor='none')

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
    cbar = plt.colorbar(im, ax=ax, ticks=precip_levels, orientation='horizontal', pad=0.06, fraction=0.061, shrink=0.95) # fraction is height, shrink is width
    ax.set_title(config['title'], fontweight='bold', fontsize=24)

    # Set the label size for the ticks
    cbar.ax.tick_params(labelsize=20)

    # Optional: Ensure the labels are formatted nicely (e.g., no extra decimals)
    cbar.ax.set_xticklabels([f'{l:g}' for l in precip_levels])

#################################################

# Add a title and adjust layout to prevent overlapping
plt.tight_layout()
plt.savefig(f"{MAP_PATH}/{grid}/{var}/{var}_valid{pdy}_{cyc}Z_{duration}h_accum.png", bbox_inches='tight', pad_inches=0.1)
