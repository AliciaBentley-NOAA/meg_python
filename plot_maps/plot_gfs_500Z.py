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

#####################################################
var = "500Z"

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

# Open GFSv16 GRIB2 file and extract parameters
filename_gfsv16 = f"{DATA_PATH}/gfs.{pdy}/{cyc}/atmos/gfs.t{cyc}z.pgrb2.0p25.f{fhr_str}"
with grib2io.open(filename_gfsv16) as f_v16:

	# Select the specific messages we want
	hgt500_msg_v16 = f_v16.select(shortName='HGT', level='500 mb')[0]

	# Extract values
	hgt500_data_v16 = hgt500_msg_v16.data / 10.0  # Convert m to dam

# Open GFSv17 GRIB2 file and extract parameters
filename_gfsv17 = f"/lfs/h1/ops/prod/com/gfs/v16.3/gfs.{pdy}/{cyc}/atmos/gfs.t{cyc}z.pgrb2.0p25.f{fhr_str}"
with grib2io.open(filename_gfsv17) as f_v17:

	# Select the specific messages we want
	hgt500_msg_v17 = f_v17.select(shortName='HGT', level='500 mb')[0]

	# Extract values
	hgt500_data_v17 = hgt500_msg_v17.data / 10.0  # Convert m to dam

	# Calculate the difference (e.g., Panel 1 minus Panel 2)
	diff_data = hgt500_data_v17 - hgt500_data_v16

	# Extract data and coordinates
	lats, lons = hgt500_msg_v17.latlons()

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

hgt500_data_v16 = hgt500_data_v16[:, i_sort]

#########################################################


#########################################################

# Create the Plot
fig = plt.figure(figsize=(16, 12))

# Define a 2x2 grid
gs = gridspec.GridSpec(1, 1, figure=fig)

# Define the specific normalization (Panel 1)
hgt500_norm = mcolors.Normalize(vmin=474, vmax=600)
hgt500_levels = np.arange(474, 606, 6)

# Update configs with specific 'norm' and 'levels'
plot_configs = [
	{'data': hgt500_data_v16, 'cmap': 'gist_rainbow_r', 'norm': hgt500_norm, 'levels': hgt500_levels, 'title': f'GFS 500-hPa Geopotential Height (dam)\nInitialized: {init_dt.strftime("%Y-%m-%d %HZ")} (F{fhr_str}) | Valid: {valid_dt.strftime("%Y-%m-%d %HZ")}'},
]

# Define the grid locations: [row, col] or [row, span]
# gs[0, 0] = Top Left, gs[0, 1] = Top Right, gs[1, :] = Bottom Center
grid_locs = [gs[0, 0]]

for i, loc in enumerate(grid_locs):
	config = plot_configs[i]

	# Add subplot with projection
	ax = fig.add_subplot(loc, projection=ccrs.PlateCarree())

	# Geographic features
	ax.add_feature(cfeature.COASTLINE, linewidth=1)
	ax.add_feature(cfeature.BORDERS, linewidth=1)
	ax.add_feature(cfeature.STATES, edgecolor='gray', linewidth=1.5, alpha=0.5)

	# Define domain
	ax.set_extent([-130, -65, 20, 56], crs=ccrs.PlateCarree())

	# Check if we are on the third panel and apply special cmap
	current_cmap = config['cmap']

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
			      levels=config['levels'], 
			      colors='black', 
			      linewidths=0.5, 
			      transform=ccrs.PlateCarree())
	# Add labels to the lines (e.g., '1012')
	# Reduce padding (default is 4) to allow more labels to fit in tight spaces
	ax.clabel(contours, inline=True, fontsize=8, fmt='%i', inline_spacing=1)

	# Capture the colorbar in a variable (e.g., 'cbar')
	cbar = plt.colorbar(im, ax=ax, orientation='horizontal', pad=0.06, fraction=0.055)
	ax.set_title(config['title'], fontweight='bold', fontsize=24)

	# Set the label size for the ticks
	cbar.ax.tick_params(labelsize=24)

#################################################

# Add a title and adjust layout to prevent overlapping
#plt.suptitle(f"GFS | 500-hPa Geopotential Height (dam) | Initialized: {init_dt.strftime('%Y-%m-%d %HZ')} (Fhr: {fhr_str}) | Valid: {valid_dt.strftime('%Y-%m-%d %HZ')}", fontsize=20)
plt.tight_layout()
plt.savefig(f"{MAP_PATH}/{grid}/{var}/gfs_{var}_init{pdy}_{cyc}Z_f{fhr}.png", bbox_inches='tight', pad_inches=0.1)
