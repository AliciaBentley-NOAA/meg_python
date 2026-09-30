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
var = "stageiv"

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
st4_delta = timedelta(hours=6)
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
print(f"Number of Stage IV files needed: {segments}")

st4_array = np.zeros((int(segments), 881, 1121), dtype=np.float32)

for j in range(int(segments)):

	# Remember: Valid time in Stage IV filenames is at the *end* of the 6-h period (add st4_delta)
	current_dt = current_dt + st4_delta
	print(f"Current Stage IV File Time: {current_dt.strftime('%Y-%m-%d %HZ')}")
	date_string = current_dt.strftime('%Y%m%d%H')

	# Open 6-h stageiv file 
	filename_st4 = f"{DATA_PATH}/stageiv/st4_conus.{date_string}.06h.grb2"

	try:
        	# Open directly using grib2io (No binary files or wgrib2 needed!)
        	with grib2io.open(filename_st4) as gfile:
            		# Select the total precipitation message
            		msg = gfile.select(shortName='APCP')[0]
            
            		# .data automatically returns a 2D array with shape (881, 1121)
            		# Fill undef/mask values with 0.0 mm so the sum works correctly
            		data = np.nan_to_num(msg.data, nan=0.0)
            		data[data > 1000.0] = 0.0  # Mask any raw 9.99e20 fill values
            
            		st4_array[j, :, :] = data

	except Exception as e:
    		print(f"wgrib2 failed for {date_string}: {e}")

	print(f"Added Stage IV into index {j} in st4_array!")

# Sum across the 6 time segments (axis 0) --> resulting shape (881,1121) 
st4_total = np.sum(st4_array, axis=0) * .0393701   # convert mm to inches

# This tells us the exact lat/lon bounds wgrib2 sees in the file
#result = subprocess.run(f"wgrib2 {filename_st4} -grid", shell=True, capture_output=True, text=True)
#print(result.stdout)

#########################################################

# Create the Plot
if grid == 'northeast':
	fig = plt.figure(figsize=(12, 10))
elif grid == 'conus':
	fig = plt.figure(figsize=(18, 12))
elif grid == 'eastcoast':
        fig = plt.figure(figsize=(13, 12))
elif grid == 'easternUS':
        fig = plt.figure(figsize=(14, 11))

# Define a 2x2 grid
gs = gridspec.GridSpec(1, 1, figure=fig)

# Define the specific normalization (Panel 1)
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
cmap.set_under(color='none')
cmap.set_over('tan')

norm = mcolors.BoundaryNorm(precip_levels, ncolors=len(precip_colors))

# Update configs with specific 'norm' and 'levels'
plot_configs = [
	{'data': st4_total, 'cmap': cmap, 'norm': norm, 'levels': precip_levels, 'title': f'Stage IV | {duration}-h Precipitation Analysis (in.)\nValid: {start_dt.strftime("%Y-%m-%d %HZ")} - {valid_dt.strftime("%Y-%m-%d %HZ")}'},
]

# Define the grid locations: [row, col] or [row, span]
grid_locs = [gs[0, 0]]

for i, loc in enumerate(grid_locs):
	config = plot_configs[i]

	# Add subplot with projection
	ax = fig.add_subplot(loc, projection=ccrs.PlateCarree())

	# Determine the appropriate scale based on the domain
	state_scale = '10m' if grid != "conus" else '50m'

	# Fetch STATES with the lakes strictly cut out
	states_clipped = cfeature.NaturalEarthFeature(category='cultural', name='admin_1_states_provinces_lakes', scale=state_scale, facecolor='none')

	# Fetch COUNTRIES with the lakes strictly cut out (Replaces cfeature.BORDERS)
	countries_clipped = cfeature.NaturalEarthFeature(category='cultural', name='admin_0_countries_lakes', scale=state_scale, facecolor='none')

	# Geographic features
	ax.add_feature(cfeature.LAND, facecolor='lightgray', edgecolor='none', zorder=1)
	ax.add_feature(cfeature.LAKES, facecolor='white', edgecolor='0.25', linewidth=1.0, zorder=2)
	ax.add_feature(states_clipped, edgecolor='0.25', linewidth=2.5, zorder=4)
	ax.add_feature(cfeature.COASTLINE, edgecolor='0.25', linewidth=1.5, zorder=4)
	ax.add_feature(countries_clipped, edgecolor='0.25', linewidth=1.5, zorder=4)
	ax.add_feature(USCOUNTIES, edgecolor='black', linewidth=0.3, alpha=0.6, zorder=5)

	# Define domain
	if grid == 'northeast':   
		ax.set_extent([-82.5, -66.5, 39.25, 45.25], crs=ccrs.PlateCarree())
		# Increase this number (e.g., 1.4) to stretch it more vertically
		ax.set_aspect(1.25, adjustable='datalim')
	elif grid == 'conus':                
		ax.set_extent([-125, -64, 22, 56], crs=ccrs.PlateCarree())
                # Increase this number (e.g., 1.4) to stretch it more vertically
		ax.set_aspect(1.2, adjustable='datalim')
	elif grid == 'eastcoast':
                ax.set_extent([-82, -57, 25.0, 48.0], crs=ccrs.PlateCarree())
                # Increase this number (e.g., 1.4) to stretch it more vertically
                ax.set_aspect(1.25, adjustable='datalim')
	elif grid == 'easternUS':
               ax.set_extent([-97, -72, 26.0, 47.0], crs=ccrs.PlateCarree())
               # Increase this number (e.g., 1.4) to stretch it more vertically
               ax.set_aspect(1.25, adjustable='datalim')

	# 1. Define the Globe (The 'NCEP Sphere')
	ncep_globe = ccrs.Globe(ellipse=None, semimajor_axis=6371200.0, semiminor_axis=6371200.0)

	# 2. Update the Projection to use this globe
	st4_proj = ccrs.NorthPolarStereo(
               central_longitude=-105.0,
               true_scale_latitude=60.0,
               globe=ncep_globe)

	# Use linspace to guarantee matching dimensions
	# We calculate the start/end in meters based on the Dx/Dy and origin
	dx = 4762.500000
	dy = 4762.500000
	nx = 1121
	ny = 881

	x0, y0 = st4_proj.transform_point(240.976992 - 360, 23.117000, ccrs.PlateCarree())
	#print(f"x0, y0 -> x0: {x0:.2f}, y0: {y0:.2f}")

	# Build coordinate mesh matching st4_proj
	x_coords = x0 + np.arange(nx) * dx
	y_coords = y0 + np.arange(ny) * dy
	X, Y = np.meshgrid(x_coords, y_coords)   # Shape: (881, 1121)

	# THEN check the corner coordinates
	lon_ll, lat_ll = ccrs.PlateCarree().transform_point(X[0, 0], Y[0, 0], st4_proj)
	lon_ur, lat_ur = ccrs.PlateCarree().transform_point(X[-1, -1], Y[-1, -1], st4_proj)

	#print("--- GRID LOCATION CHECK ---")
	#print(f"Calculated Lower-Left Corner:  Lat {lat_ll:.2f}°, Lon {lon_ll:.2f}°")
	#print(f"Calculated Upper-Right Corner: Lat {lat_ur:.2f}°, Lon {lon_ur:.2f}°")

	# Mask NOAA undef / fill values (anything > 1000)
	config['data'] = np.ma.masked_greater(config['data'], 1000.0)

	# Plot the shading
	im = ax.pcolormesh(X, Y, config['data'], 
		     norm=config['norm'], 
		     cmap= config['cmap'],
		     transform=st4_proj,
		     shading='nearest',
		     zorder=3)

	data = config['data']

	print("--- DATA DIAGNOSTICS ---")
	#print("Data type:", data.dtype)
	#print("Data shape:", data.shape)
	print("Min Stage IV value:", np.nanmin(data))
	print("Max Stage IV value:", np.nanmax(data))
	#print("Mean value:", np.nanmean(data))
	#print("Number of NaNs:", np.isnan(data).sum())
	#print("Number of non-zero values:", np.count_nonzero(data))

	if grid == 'conus':
		cbar = plt.colorbar(im, ax=ax, extend='max', ticks=precip_levels, orientation='horizontal', pad=0.05, fraction=0.060, shrink=1.00) # fraction is height, shrink is width
		ax.set_title(config['title'], fontweight='bold', fontsize=23)
		cbar.ax.tick_params(labelsize=20)
	else:
                cbar = plt.colorbar(im, ax=ax, extend='max', ticks=precip_levels, orientation='horizontal', pad=0.05, fraction=0.060, shrink=0.95) # fraction is height, shrink is width
                ax.set_title(config['title'], fontweight='bold', fontsize=18)
                cbar.ax.tick_params(labelsize=16)

	# Ensure the labels are formatted nicely (e.g., no extra decimals)
	cbar.ax.set_xticklabels([f'{l:g}' for l in precip_levels])

#################################################

# Add a title and adjust layout to prevent overlapping
plt.tight_layout()
plt.savefig(f"{MAP_PATH}/{grid}/{var}/{var}_valid{pdy}_{cyc}Z_{duration}h_accum.png", bbox_inches='tight', pad_inches=0.1)
