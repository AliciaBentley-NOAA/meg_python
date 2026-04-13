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

#####################################################
var = "cape_sfc_based"

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
filename_gfsv17 = f"/lfs/h2/emc/gfstemp/emc.global/EVS_archive/retrov17_01/gfs.{pdy}/{cyc}/products/atmos/grib2/0p25/gfs.t{cyc}z.pres_a.0p25.f{fhr_str}.grib2"
with grib2io.open(filename_gfsv17) as f_gfsv17:

	# Select the specific messages we want
	cape_msg = f_gfsv17.select(shortName='CAPE', level='surface')[0]

	# Extract values
	cape_data = cape_msg.data

	# Extract data and coordinates
	lats, lons = cape_msg.latlons()

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

cape_data = cape_data[:, i_sort]

# Finding the values
minimum = np.min(cape_data)
maximum = np.max(cape_data)

# Printing the results
print(f"The minimum surface-based CAPE is: {minimum}")
print(f"The maximum surface-based CAPE is: {maximum}")

#########################################################


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
elif grid == 'easternUS':
        fig = plt.figure(figsize=(13, 12))

# Define a 2x2 grid
gs = gridspec.GridSpec(1, 1, figure=fig)

# Define the specific normalization (Panel 1)
cape_levels = np.array([100,250,500,1000,1500,2000,2500,3000,3500,4000,4500,5000])
cape_colors = [
    '#ffffcc', # 100-250: Pale Yellow
    '#ffeda0', # 250-500: Light Yellow
    '#fed976', # 500-1000: Yellow
    '#feb24c', # 1000-1500: Light Orange
    '#fd8d3c', # 1500-2000: Orange
    '#fc4e2a', # 2000-2500: Red-Orange
    '#e31a1c', # 2500-3000: Red
    '#bd0026', # 3000-3500: Dark Red
    '#980043', # 3500-4000: Dark Magenta
    '#670043', # 4000-4500: Deep Plum
    '#49006a', # 4000-4500: Dark Purple
    ]

cmap = mcolors.ListedColormap(cape_colors)
cmap.set_under('none')
cmap.set_over('#240036') # Midnight Purple
cape_norm = mcolors.BoundaryNorm(cape_levels, cmap.N)

# Update configs with specific 'norm' and 'levels'
plot_configs = [
	{'data': cape_data, 'cmap': cmap, 'norm': cape_norm, 'levels': cape_levels, 'title': f'GFSv17 Surface-based CAPE (J/kg)\nInitialized: {init_dt.strftime("%Y-%m-%d %HZ")} (F{fhr_str}) | Valid: {valid_dt.strftime("%Y-%m-%d %HZ")}'},
]

# Define the grid locations: [row, col] or [row, span]
# gs[0, 0] = Top Left, gs[0, 1] = Top Right, gs[1, :] = Bottom Center
grid_locs = [gs[0, 0]]

for i, loc in enumerate(grid_locs):
    config = plot_configs[i]

	# Add subplot with projection
    ax = fig.add_subplot(loc, projection=ccrs.PlateCarree())

    # Geographic features
    ax.add_feature(cfeature.LAND, facecolor='lightgray', edgecolor='none', zorder=1)
    ax.add_feature(cfeature.LAKES, facecolor='white', edgecolor='0.25', linewidth=1.0, zorder=2)
    ax.add_feature(cfeature.COASTLINE, edgecolor='0.3', linewidth=2, zorder=4)
    ax.add_feature(cfeature.BORDERS, edgecolor='0.3', linewidth=2, zorder=4)
    ax.add_feature(cfeature.STATES, edgecolor='0.3', linewidth=2, zorder=4)

	# Define domain
    if grid == 'northeast':   
        ax.set_extent([-82, -67, 38.75, 45.75], crs=ccrs.PlateCarree())
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
    elif grid == 'southeastUS':
        #ax.set_extent([-89, -76, 19.0, 34.0], crs=ccrs.PlateCarree())
        ax.set_extent([-86, -81, 21.0, 32.0], crs=ccrs.PlateCarree())
        # Add manual aspect ratio here. 
        # Increase this number (e.g., 1.4) to stretch it more vertically
        ax.set_aspect(1.25, adjustable='datalim')
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
    #current_cmap.set_over('crimson')   # Color for values > max
    #current_cmap.set_under('deeppink')  # Color for values < min

	# Plot the shading
    im = ax.contourf(lons, lats, config['data'], 
		     levels=config['levels'],
		     norm=config['norm'], 
		     cmap=current_cmap,
		     transform=ccrs.PlateCarree(),
		     extend='both',
             zorder=3)

	# Plot the contour lines
	# Only add lines if it's one of the MSLP panels (0 or 1)
    #contours = ax.contour(lons, lats, config['data'], 
	#		      levels='cape_level', 
	#		      colors='cape_colors', 
	#		      linewidths=3.0, 
	#		      transform=ccrs.PlateCarree())
	# Add labels to the lines (e.g., '1012')
	# Reduce padding (default is 4) to allow more labels to fit in tight spaces
    #ax.clabel(contours, contours.levels, inline=True, fontsize=18, fmt='%i', inline_spacing=8)

	# Capture the colorbar in a variable (e.g., 'cbar')
    cbar = plt.colorbar(im, ax=ax, orientation='horizontal', pad=0.06, fraction=0.055)
    ax.set_title(config['title'], fontweight='bold', fontsize=24)

	# Set the label size for the ticks
    cbar.ax.tick_params(labelsize=24)

#################################################

# Add a title and adjust layout to prevent overlapping
#plt.suptitle(f"GFSv16 | 500-hPa Geopotential Height (dam) | Initialized: {init_dt.strftime('%Y-%m-%d %HZ')} (Fhr: {fhr_str}) | Valid: {valid_dt.strftime('%Y-%m-%d %HZ')}", fontsize=20)
plt.tight_layout()
plt.savefig(f"{MAP_PATH}/{grid}/{var}/gfsv17_{var}_init{pdy}_{cyc}Z_f{fhr}.png", bbox_inches='tight', pad_inches=0.1)
