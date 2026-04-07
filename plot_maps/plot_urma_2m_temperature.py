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
import subprocess

#####################################################
var = "urma"

pdy = str(sys.argv[1])             # 20251120
cyc = str(sys.argv[2])		   # 12 
grid = str(sys.argv[3])            # conus
DATA_PATH = str(sys.argv[4])       # /lfs/h2/emc/vpppg/noscrub/alicia.bentley/feb2026
MAP_PATH = str(sys.argv[5])        # /lfs/h2/emc/vpppg/noscrub/alicia.bentley/feb2026/maps

show_colorbar="yes"

print("pdy:", pdy)
print("cyc:", cyc)
print("grid:", grid)

valid_str = str(pdy)
valid_hour = int(cyc)

#Create the datetime object
# strptime converts the string to a datetime object
valid_dt = datetime.strptime(valid_str, "%Y%m%d").replace(hour=valid_hour)

# Create maps directory
Path(f"{MAP_PATH}/{grid}/{var}").mkdir(parents=True, exist_ok=True)

####################################################

# Use f-string to format with leading zeros (e.g., 000, 006)

# Print the results in a readable format
print(f"Valid Time:          {valid_dt.strftime('%Y-%m-%d %HZ')}")

#---------------------------------------------------------
#---------------------------------------------------------
#---------------------------------------------------------

# Open GFS GRIB2 file and extract parameters
filename_urma = f"/lfs/h2/emc/vpppg/noscrub/alicia.bentley/urma/jan2026/urma2p5.t{cyc}z.2dvaranl_ndfd.grb2_wexp"
with grib2io.open(filename_urma) as f_urma:

    # Select the specific messages we want
    temp_msg = f_urma.select(shortName='TMP', level='2 m above ground')[0]

    # Extract values
    temp_data = (temp_msg.data - 273.15)*(9.0/5.0)+32.0  # Convert K to F

    # Extract data and coordinates
    lats, lons = temp_msg.latlons()

#########################################################


#########################################################

# Create the Plot
if grid == 'northeast':
	fig = plt.figure(figsize=(12, 10))
elif grid == 'conus':
	fig = plt.figure(figsize=(13, 10))
elif grid == 'eastcoast':
        fig = plt.figure(figsize=(13, 12))
elif grid == 'colorado':
        fig = plt.figure(figsize=(14, 12))
elif grid == 'easternUS':
    fig = plt.figure(figsize=(13,12))

# Define a 2x2 grid
gs = gridspec.GridSpec(1, 1, figure=fig)

# Define the specific normalization (Panel 1)
temp_norm = mcolors.Normalize(vmin=-30, vmax=126)
temp_levels = np.arange(-30, 128, 2)
T2m_levels = np.array([-16, 0, 16, 32, 48, 64, 80, 96, 112])

# Update configs with specific 'norm' and 'levels'
plot_configs = [
    {'data': temp_data, 'cmap': 'gist_rainbow_r', 'norm': temp_norm, 'levels': temp_levels, 'title': f'URMA 2-m Temperature (F)\nValid: {valid_dt.strftime("%Y-%m-%d %HZ")}'},
]

# Define the grid locations: [row, col] or [row, span]
# gs[0, 0] = Top Left, gs[0, 1] = Top Right, gs[1, :] = Bottom Center
grid_locs = [gs[0, 0]]

for i, loc in enumerate(grid_locs):
    config = plot_configs[i]

    # Add subplot with projection
    ax = fig.add_subplot(loc, projection=ccrs.PlateCarree())

    # Geographic features
    ax.add_feature(cfeature.COASTLINE, linewidth=2.0)
    ax.add_feature(cfeature.BORDERS, edgecolor='0.3', linewidth=2.0)
    ax.add_feature(cfeature.STATES, edgecolor='0.3', linewidth=2.0)
	
	# Define domain
    if grid == 'northeast':   
        ax.set_extent([-82.5, -66.5, 39.25, 45.25], crs=ccrs.PlateCarree())
		# Add manual aspect ratio here. 
		# Increase this number (e.g., 1.4) to stretch it more vertically
        ax.set_aspect(1.25, adjustable='datalim')
    elif grid == 'conus':                
        ax.set_extent([-125, -63, 25, 54], crs=ccrs.PlateCarree())
        # Add manual aspect ratio here. 
        # Increase this number (e.g., 1.4) to stretch it more vertically
        ax.set_aspect(1.2, adjustable='datalim')
    elif grid == 'eastcoast':
        ax.set_extent([-82, -57, 25.0, 48.0], crs=ccrs.PlateCarree())
        # Add manual aspect ratio here. 
        # Increase this number (e.g., 1.4) to stretch it more vertically
        ax.set_aspect(1.25, adjustable='datalim')
    elif grid == 'colorado':
        ax.set_extent([-112.0, -99.0, 32.5, 42.0], crs=ccrs.PlateCarree())
        # Add manual aspect ratio here. 
        # Increase this number (e.g., 1.4) to stretch it more vertically
        ax.set_aspect(1.2, adjustable='datalim')
    elif grid == 'easternUS':
            ax.set_extent([-97, -72, 25.0, 48.0], crs=ccrs.PlateCarree())
            # Add manual aspect ratio here. 
            # Increase this number (e.g., 1.4) to stretch it more vertically
            ax.set_aspect(1.25, adjustable='datalim')

    # Check if we are on the third panel and apply special cmap
    #current_cmap = config['cmap']
    current_cmap = copy.copy(plt.get_cmap(config['cmap']))

    # Set the "over" and "under" colors
    # You can use named colors, hex codes, or RGB tuples
    current_cmap.set_over('crimson')   # Color for values > max
    current_cmap.set_under('deeppink')  # Color for values < min

    # Plot the shading
    im = ax.contourf(lons, lats, config['data'],
             levels=config['levels'],
             norm=config['norm'],
             cmap=current_cmap,
             transform=ccrs.PlateCarree(),
             extend='both')

    # Plot the contour lines
    # Only add lines if it's one of the MSLP panels (0 or 1)
    contours = ax.contour(lons, lats, config['data'],
                  levels=[32],
                  colors='white',
                  linewidths=3.0,
                  transform=ccrs.PlateCarree())
    # Add labels to the lines (e.g., '1012')
    # Reduce padding (default is 4) to allow more labels to fit in tight spaces
    ax.clabel(contours, contours.levels, inline=True, fontsize=18, fmt='%i', inline_spacing=8)

    # Capture the colorbar in a variable (e.g., 'cbar')
    if grid == 'northeast':
        cbar = plt.colorbar(im, ax=ax, ticks=T2m_levels, orientation='horizontal', pad=0.05, fraction=0.055, shrink=0.95) # fraction is height, shrink is width
    elif grid == 'conus':
        cbar = plt.colorbar(im, ax=ax, ticks=T2m_levels, orientation='horizontal', pad=0.05, fraction=0.055, shrink=0.95) # fraction is height, shrink is width
    elif grid == 'colorado':
        cbar = plt.colorbar(im, ax=ax, ticks=T2m_levels, orientation='horizontal', pad=0.05, fraction=0.055, shrink=0.95) # fraction is height, shrink is width
    elif grid == 'easternUS':
        cbar = plt.colorbar(im, ax=ax, ticks=T2m_levels, orientation='horizontal', pad=0.05, fraction=0.055, shrink=0.95) # fraction is height, shrink is width
    ax.set_title(config['title'], fontweight='bold', fontsize=20)

	# Set the label size for the ticks
    cbar.ax.tick_params(labelsize=20)

	# Optional: Ensure the labels are formatted nicely (e.g., no extra decimals)
    cbar.ax.set_xticklabels([f'{l:g}' for l in T2m_levels])

#################################################

# Add a title and adjust layout to prevent overlapping
#plt.suptitle(f"GFS | 500-hPa Geopotential Height (dam) | Initialized: {init_dt.strftime('%Y-%m-%d %HZ')} (Fhr: {fhr_str}) | Valid: {valid_dt.strftime('%Y-%m-%d %HZ')}", fontsize=20)
plt.tight_layout()
plt.savefig(f"{MAP_PATH}/{grid}/{var}/{var}_valid{pdy}_{cyc}Z_2mT.png", bbox_inches='tight', pad_inches=0.1)
