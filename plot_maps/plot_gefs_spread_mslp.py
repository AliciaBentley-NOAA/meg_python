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
var = "mslp"

print(f"#############################################")

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

# Open GEFS GRIB2 file and extract parameters
filename_gefs = f"{DATA_PATH}/gefs.{pdy}/{cyc}/atmos/geavg.t{cyc}z.pgrb2s.0p25.f{fhr_str}"
with grib2io.open(filename_gefs) as f_gefs:

	# Select the specific messages we want
	mslp_msg = f_gefs.select(shortName='PRMSL', level='mean sea level')[0]

	# Extract values
	mslp_data = mslp_msg.data / 100.0  # Convert Pa to hPa/mb

	# Extract data and coordinates
	lats, lons = mslp_msg.latlons()

# Open GEFS GRIB2 file and extract parameters
filename_gefss = f"{DATA_PATH}/gefs.{pdy}/{cyc}/atmos/gespr.t{cyc}z.pgrb2s.0p25.f{fhr_str}"
with grib2io.open(filename_gefss) as f_gefss:

        # Select the specific messages we want
        mslps_msg = f_gefss.select(shortName='PRMSL', level='mean sea level')[0]

        # Extract values
        mslps_data = mslps_msg.data / 100.0  # Convert Pa to hPa/mb

	# Assuming 'data' is your 2D array
        data_min = np.min(mslps_data)
        data_max = np.max(mslps_data)

        print(f"Minimum Spread Value: {data_min:.2f}")
        print(f"Maximum Spread Value: {data_max:.2f}")


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

mslp_data = mslp_data[:, i_sort]
mslps_data = mslps_data[:, i_sort]

#########################################################


#########################################################

# Create the Plot
if grid == 'northeast':
	fig = plt.figure(figsize=(12, 12))
elif grid == 'conus':
	fig = plt.figure(figsize=(15, 12))
elif grid == 'eastcoast':
        fig = plt.figure(figsize=(13, 12))
elif grid == 'hawaii':
	fig = plt.figure(figsize=(14, 12))
elif grid == 'cpac':
	fig = plt.figure(figsize=(14, 12))

# Define a 2x2 grid
gs = gridspec.GridSpec(1, 1, figure=fig)

# Define the specific normalization (Panel 1)
mslp_norm = mcolors.Normalize(vmin=968, vmax=1052)
mslp_levels = np.arange(968, 1056, 4)

mslps_norm = mcolors.Normalize(vmin=0, vmax=18)
mslps_levels = np.arange(0, 18, 2)

# Take 14 colors from the 'cool' colormap
base_cmap = plt.get_cmap('YlOrRd', 14)
new_colors = base_cmap(np.arange(base_cmap.N))

# Force the first color (index 0) to be transparent
new_colors[0,3] = 0.0  # First color is transparent

# Create the new colormap
white_first_cmap = mcolors.ListedColormap(new_colors)

# Update configs with specific 'norm' and 'levels'
plot_configs = [
	{'data': mslp_data, 'cmap': 'YlOrRd', 'norm': mslps_norm, 'levels': mslps_levels, 'title': f'GEFS mean/spread | Mean Sea Level Pressure (hPa)\nInitialized: {init_dt.strftime("%Y-%m-%d %HZ")} (F{fhr_str}) | Valid: {valid_dt.strftime("%Y-%m-%d %HZ")}'},
]

# Define the grid locations: [row, col] or [row, span]
grid_locs = [gs[0, 0]]

for i, loc in enumerate(grid_locs):
	config = plot_configs[i]

	# Add subplot with projection
	#ax = fig.add_subplot(loc, projection=ccrs.PlateCarree())
	ax = fig.add_subplot(loc, projection=ccrs.PlateCarree(central_longitude=190))

	# Determine the appropriate scale based on the domain
	state_scale = '10m' if grid != "conus" else '50m'

	# Fetch STATES with the lakes strictly cut out
	states_clipped = cfeature.NaturalEarthFeature(category='cultural', name='admin_1_states_provinces_lakes', scale=state_scale, facecolor='none')

	# Fetch COUNTRIES with the lakes strictly cut out (Replaces cfeature.BORDERS)
	countries_clipped = cfeature.NaturalEarthFeature(category='cultural', name='admin_0_countries_lakes', scale=state_scale, facecolor='none')

	# Geographic features
	ax.add_feature(cfeature.LAND, facecolor='lightgray', edgecolor='none', zorder=1)
	ax.add_feature(cfeature.LAKES, facecolor='white', edgecolor='0.25', linewidth=1.0, zorder=2)
	ax.add_feature(states_clipped, edgecolor='0.25', linewidth=1.5, zorder=4)
	ax.add_feature(cfeature.COASTLINE, edgecolor='0.25', linewidth=1.5, zorder=4)
	ax.add_feature(countries_clipped, edgecolor='0.25', linewidth=1.5, zorder=4)

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
	elif grid == 'hawaii':
		ax.set_extent([-164, -148, 14, 25], crs=ccrs.PlateCarree())
		# Increase this number (e.g., 1.4) to stretch it more vertically
		ax.set_aspect(1.2, adjustable='datalim')
	elif grid == 'cpac':
		ax.set_extent([178, 205, 15, 30], crs=ccrs.PlateCarree())
		# Increase this number (e.g., 1.4) to stretch it more vertically
		ax.set_aspect(1.2, adjustable='datalim')

	# Plot the shading
	im = ax.contourf(lons, lats, mslps_data,
                     levels=mslps_levels,
		     norm=config['norm'], 
		     cmap=white_first_cmap,
		     transform=ccrs.PlateCarree(),
		     extend='max',
		     zorder=3)

	# Plot the contour lines
	contours = ax.contour(lons, lats, mslp_data,
                     	      levels=mslp_levels,
			      colors='black', 
			      linewidths=3.0, 
			      transform=ccrs.PlateCarree(),
			      zorder=5)

	# Add labels to the lines (e.g., '1012')
	ax.clabel(contours, inline=True, fontsize=20, fmt='%i', inline_spacing=5)

	# Capture the colorbar in a variable (e.g., 'cbar')
	cbar = plt.colorbar(im, ax=ax, orientation='horizontal', pad=0.06, fraction=0.055)
	ax.set_title(config['title'], fontweight='bold', fontsize=24)

	# Set the label size for the ticks
	cbar.ax.tick_params(labelsize=24)

#################################################

# Add a title and adjust layout to prevent overlapping
plt.tight_layout()
plt.savefig(f"{MAP_PATH}/{grid}/{var}/gefs_spread_{var}_init{pdy}_{cyc}Z_f{fhr}.png", bbox_inches='tight', pad_inches=0.1)
