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
var = "nohrsc"

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
start_dt = valid_dt - duration_delta
current_dt = start_dt

# Print the results in a readable format
print(f"Initialization Time: {init_dt.strftime('%Y-%m-%d %HZ')}")
print(f"Forecast Lead:       {fcst_hour} hours")
print(f"Start Time:          {start_dt.strftime('%Y-%m-%d %HZ')}")
print(f"Valid Time:          {valid_dt.strftime('%Y-%m-%d %HZ')}")

#---------------------------------------------------------
#---------------------------------------------------------
#---------------------------------------------------------

segments = int(duration) / int(6)
print(segments)

nohrsc_array = np.zeros((int(segments), 1377, 2145), dtype=np.float32)

for j in range(int(segments)):

	current_dt = current_dt + nohrsc_delta # Remember: Valid time in NOHRSC filenames is at the *end* of the 6-h period
	print(f"Current NOHRSC File Time: {current_dt.strftime('%Y-%m-%d %HZ')}")
	date_string = current_dt.strftime('%Y%m%d%H')

	# Open 6-h NOHRSC file 
	filename_nohrsc = f"{DATA_PATH}/nohrsc/sfav2_CONUS_6h_{date_string}_grid184.grb2"

	# 1. Define a temporary binary file name
	bin_file = f"temp_data_{j}.bin"

	try:
		# 2. Use wgrib2 to export the data to a raw float32 binary file
		# -bin exports the data, -no_header removes metadata
		cmd = f"wgrib2 {filename_nohrsc} -bin {bin_file} -no_header"
		subprocess.run(cmd, shell=True, check=True, capture_output=True)

		# 3. Read the binary file directly into NumPy
		# NOHRSC Grid 184 is 1377 rows x 2145 columns
		nohrsc_data = np.fromfile(bin_file, dtype=np.float32)
    
		# 4. Reshape it to the correct dimensions and save to your array
		nohrsc_array[j, :, :] = nohrsc_data.reshape((1377, 2145))

		print(f"Success! Loaded {date_string} using wgrib2.")

	except Exception as e:
    		print(f"wgrib2 failed for {date_string}: {e}")

	finally:
		# 5. Clean up the binary file
		if os.path.exists(bin_file):
			os.remove(bin_file)

	#lats, lons = nohrsc_msg.latlons()

	print(f"Added NOHRSC for {j}!")

# Sum across the 6 time segments (axis 0) 
# This gives you a 2D map of the total accumulation
nohrsc_total = np.sum(nohrsc_array, axis=0) * 39.3701   # convert meters to inches

# This tells us the exact lat/lon bounds wgrib2 sees in the file
result = subprocess.run(f"wgrib2 {filename_nohrsc} -grid", shell=True, capture_output=True, text=True)
print(result.stdout)

#########################################################


#########################################################

# Create the Plot
if grid == 'northeast':
	fig = plt.figure(figsize=(12, 12))
elif grid == 'conus':
	fig = plt.figure(figsize=(15, 12))
elif grid == 'eastcoast':
        fig = plt.figure(figsize=(13, 12))

# Define a 2x2 grid
gs = gridspec.GridSpec(1, 1, figure=fig)

# Define the specific normalization (Panel 1)
snod_levels = np.array([0.1, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0, 18.0, 24.0, 30.0, 36.0, 48.0, 60.0])
snod_colors = ['#749DDE', '#588ADC', '#2F74C8', '#2364B9', '#1E559D', '#FFF68F', '#F4C430', '#ED781E', '#E23916', '#C92828', '#D986D9', '#D95DD9', '#CD0ACD']

cmap = mcolors.ListedColormap(snod_colors)
#cmap.set_under('white')
#cmap.set_over('#CD0ACD')

# Mask values that are clearly 'missing' (usually > 100 inches) 
# or zero (to keep the ocean clean)
nohrsc_total = np.where((nohrsc_total > 100.0) | (nohrsc_total < 0.1), np.nan, nohrsc_total)

norm = mcolors.BoundaryNorm(snod_levels, ncolors=len(snod_colors))

# Update configs with specific 'norm' and 'levels'
plot_configs = [
	{'data': nohrsc_total, 'cmap': cmap, 'norm': norm, 'levels': snod_levels, 'title': f'NOHRSC {duration}-h Snowfall Analysis (in.)\nInitialized: {init_dt.strftime("%Y-%m-%d %HZ")} (F{fhr_str}) | Valid: {valid_dt.strftime("%Y-%m-%d %HZ")}'},
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
	nohrsc_proj = ccrs.LambertConformal(central_longitude=-95.0,
                                    central_latitude=25.0,
                                    standard_parallels=(25.0, 25.0),
                                    globe=ncep_globe)

	# Use linspace to guarantee matching dimensions
	# We calculate the start/end in meters based on the Dx/Dy and origin
	dx = 2539.703
	dy = 2539.703

	x0, y0 = nohrsc_proj.transform_point(238.446 - 360, 20.191999, ccrs.PlateCarree())

	# Generate exactly the right number of points
	x_coords = np.linspace(x0, x0 + (2144 * dx), 2145)
	y_coords = np.linspace(y0, y0 + (1376 * dy), 1377)

	X, Y = np.meshgrid(x_coords, y_coords)

	# Plot the shading
	im = ax.pcolormesh(X, Y, config['data'], 
		     norm=config['norm'], 
		     cmap= config['cmap'],
		     transform=nohrsc_proj,
		     shading='nearest')

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
	ax.set_title(config['title'], fontweight='bold', fontsize=24)

	# Set the label size for the ticks
	cbar.ax.tick_params(labelsize=24)

	# Optional: Ensure the labels are formatted nicely (e.g., no extra decimals)
	cbar.ax.set_xticklabels([f'{l:g}' for l in snod_levels])

#################################################

# Add a title and adjust layout to prevent overlapping
#plt.suptitle(f"GFS | 500-hPa Geopotential Height (dam) | Initialized: {init_dt.strftime('%Y-%m-%d %HZ')} (Fhr: {fhr_str}) | Valid: {valid_dt.strftime('%Y-%m-%d %HZ')}", fontsize=20)
plt.tight_layout()
plt.savefig(f"{MAP_PATH}/{grid}/{var}/{var}_init{pdy}_{cyc}Z_f{fhr}.png", bbox_inches='tight', pad_inches=0.1)
