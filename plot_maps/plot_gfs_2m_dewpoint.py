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
var = "2mTd"

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
filename_gfs = f"{DATA_PATH}/gfs.{pdy}/{cyc}/atmos/gfs.t{cyc}z.pgrb2.0p25.f{fhr_str}"
with grib2io.open(filename_gfs) as f_gfs:

	# Select the specific messages we want
	temp_msg = f_gfs.select(shortName='DPT', level='2 m above ground')[0]

	# Extract values
	temp_data = (temp_msg.data - 273.15)*(9.0/5.0)+32.0  # Convert K to F

	# Extract data and coordinates
	lats, lons = temp_msg.latlons()

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

temp_data = temp_data[:, i_sort]

# Finding the values
minimum = np.min(temp_data)
maximum = np.max(temp_data)

# Printing the results
print(f"The minimum temperature is: {minimum}")
print(f"The maximum temperature is: {maximum}")

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

temp_norm = mcolors.Normalize(vmin=-36, vmax=120)
temp_levels = np.arange(-36, 124, 4)
T2m_levels = np.array([-36, -24, -12, 0, 12, 24, 36, 48, 60, 72, 84, 96, 108, 120])

temp_colors = [
    "#555555", "#666666", "#999999", "#CCCCCC", # -36 to -24
    "#9300FF", "#7D00E3", "#6700C7", "#5100AB", # -24 to -12
    "#E642A5", "#D23791", "#BE2C7D", "#AA2169", # -12 to 0
    "#C77EB5", "#BA8EBD", "#AD9EC5", "#A0AECD", # 0 to 12
    "#C2C2EB", "#D1D1F2", "#E0E0F9", "#EFEFFF", # 12 to 24
    "#63B8FF", "#0096FF", "#0073FF", "#0050FF", # 24 to 36
    "#009000", "#00A300", "#00B600", "#00C900", # 36 to 48
    "#C6EF00", "#D6F500", "#E6FB00", "#F6FF00", # 48 to 60
    "#FFEB00", "#FFD700", "#FFC300", "#FFAF00", # 60 to 72
    "#FF8C00", "#FF6600", "#FF4000", "#FF1A00", # 72 to 84
    "#E31A1C", "#C81416", "#AD0E10", "#92080A", # 84 to 96
    "#980043", "#83003B", "#6E0033", "#59002B", # 96 to 108
    "#FF00FF", "#FF55FF", "#FFAAFF", "#FFD9F5"  # 108 to 120+
]

cmap = mcolors.ListedColormap(temp_colors)
cmap.set_under('#333333')
cmap.set_over('#FFFFFF')

# Update configs with specific 'norm' and 'levels'
plot_configs = [
	{'data': temp_data, 'cmap': cmap, 'norm': temp_norm, 'levels': temp_levels, 'title': f'GFSv16 2-m Dewpoint (F)\nInitialized: {init_dt.strftime("%Y-%m-%d %HZ")} (F{fhr_str}) | Valid: {valid_dt.strftime("%Y-%m-%d %HZ")}'},
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
		     extend='both')

	# Plot the contour lines
	# Only add lines if it's one of the MSLP panels (0 or 1)
    #contours = ax.contour(lons, lats, config['data'], 
	#		      levels=[32], 
	#		      colors='white', 
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
plt.savefig(f"{MAP_PATH}/{grid}/{var}/gfsv16_{var}_init{pdy}_{cyc}Z_f{fhr}.png", bbox_inches='tight', pad_inches=0.1)
