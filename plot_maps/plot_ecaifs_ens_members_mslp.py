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

init_YYYY = init_dt.strftime("%Y") #Result: '2026'
init_MM = init_dt.strftime("%m")  # Result: '02'
init_DD = init_dt.strftime("%d")    # Result: '28'
init_HH = init_dt.strftime("%H")  # Result: '06'

# Create maps directory
Path(f"{MAP_PATH}/{grid}/{var}").mkdir(parents=True, exist_ok=True)

####################################################

# Use f-string to format with leading zeros (e.g., 000, 006)
fhr_str = f"{fhr}"
fcst_hour= int(fhr)

# Add the forecast lead time
forecast_delta = timedelta(hours=fcst_hour)
valid_dt = init_dt + forecast_delta

valid_MM = valid_dt.strftime("%m")  # Result: '02'
valid_DD = valid_dt.strftime("%d")  # Result: '26'
valid_HH = valid_dt.strftime("%H")  # Result: '06'

# Print the results in a readable format
print(f"Initialization Time: {init_dt.strftime('%Y-%m-%d %HZ')}")
print(f"Forecast Lead:       {fcst_hour} hours")
print(f"Valid Time:          {valid_dt.strftime('%Y-%m-%d %HZ')}")

new_hour = int(fhr)
print(f"new_hour: {new_hour}")

#-----------------------------------------------------------

def get_uncompressed_grib(input_path):
    """Converts AEC compressed GRIB2 (Template 5.42) to simple uncompressed GRIB2."""
    output_path = input_path.replace(".grib2", "_uncompressed.grib2")

    # Only run wgrib2 conversion if uncompressed file doesn't exist yet
    if not os.path.exists(output_path):
        cmd = f"wgrib2 {input_path} -set_grib_type simple -grib_out {output_path}"
        subprocess.run(cmd, shell=True, check=True)

    return output_path

#-----------------------------------------------------------

# Open EC AIFS ENS file and extract parameters from valid date
filename_ecmwf = f"{DATA_PATH}/ecmwf_aifs_ens.{pdy}/{cyc}/atmos/{init_YYYY}{init_MM}{init_DD}{init_HH}0000-{new_hour}h-enfo-pf.grib2"
print(filename_ecmwf)
filename_uncompressed = f"{DATA_PATH}/ecmwf_aifs_ens.{pdy}/{cyc}/atmos/{init_YYYY}{init_MM}{init_DD}{init_HH}0000-{new_hour}h-enfo-pf_uncompressed.grib2"
print(filename_uncompressed)

if not os.path.exists(filename_uncompressed):
	print(f"Uncompressing ECAIFS ENS grib2 file.")
	filename_ecmwf_clean = get_uncompressed_grib(filename_ecmwf)
else:
	print(f"'{filename_uncompressed}' exists.")
	filename_ecmwf_clean = filename_uncompressed

with grib2io.open(filename_ecmwf_clean) as f_ecmwf:

        # Select ALL ensemble members for MSLP (returns a list of messages)
        mslp_msgs = f_ecmwf.select(shortName='PRES', level='mean sea level')
        print(f"Found {len(mslp_msgs)} ensemble members.")

        # Stack into a 3D NumPy array of shape (num_members, ny, nx)
        ensemble_stack = np.array([msg.data / 100.0 for msg in mslp_msgs])

        # Ensemble Mean
        mslp_mean = np.mean(ensemble_stack, axis=0)

        # Ensemble Spread / Standard Deviation (in dam)
        # ddof=1 uses sample standard deviation (N-1 degrees of freedom)
        mslp_spread = np.std(ensemble_stack, axis=0, ddof=1)

        # Extract lats and lons from the first message (they share the same grid)
        lats, lons = mslp_msgs[0].latlons()

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

mslp_data = mslp_mean[:, i_sort]
mslps_data = mslp_spread[:, i_sort]

#########################################################

# Create the Plot
if grid == 'northeast':
	fig = plt.figure(figsize=(12, 12))
elif grid == 'conus':
	fig = plt.figure(figsize=(15, 12))
elif grid == 'hawaii':
	fig = plt.figure(figsize=(14, 12))

# Define a 2x2 grid
gs = gridspec.GridSpec(1, 1, figure=fig)

# Define the specific normalization (Panel 1)
mslp_norm = mcolors.Normalize(vmin=968, vmax=1052)
mslp_levels = np.arange(968, 1056, 4)

colors = [
    "#ffffff00", # 0 - 2  (White)
    "#ffe89c",   # 2 - 4  (Pale Yellow)
    "#fdca62",   # 4 - 6  (Yellow)
    "#fa9238",   # 6 - 8  (Orange)
    "#f1522e",   # 8 - 10 (Red-Orange)
    "#e02927",   # 10 - 12 (Red)
    "#cd0a28",   # 12 - 14 (Crimson)
    "#b10026",   # 14 - 16 (Dark Red)
]
over_color = "#66001b"  # > 16 (Deep Maroon)

# Build custom colormap and norm
cmap_spread = mcolors.ListedColormap(colors)
cmap_spread.set_over(over_color)

mslps_levels = np.arange(0, 18, 2)
mslps_norm = mcolors.BoundaryNorm(mslps_levels, ncolors=cmap_spread.N, clip=False)
#mslps_norm = mcolors.Normalize(vmin=0, vmax=18)

# Update configs with specific 'norm' and 'levels'
plot_configs = [
        {'data': mslp_data, 'cmap': 'YlOrRd', 'norm': mslps_norm, 'levels': mslps_levels, 'title': f'EC-AIFS ENS members/spread | Mean Sea Level Pressure (hPa)\nInitialized: {init_dt.strftime("%Y-%m-%d %HZ")} (F{fhr_str}) | Valid: {valid_dt.strftime("%Y-%m-%d %HZ")}'},
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
	states_clipped = cfeature.NaturalEarthFeature(
		category='cultural',
		name='admin_1_states_provinces_lakes', # <--- The crucial _lakes suffix
		scale=state_scale,
		facecolor='none'
	)

	# Fetch COUNTRIES with the lakes strictly cut out (Replaces cfeature.BORDERS)
	countries_clipped = cfeature.NaturalEarthFeature(
		category='cultural',
		name='admin_0_countries_lakes', # <--- The crucial _lakes suffix
		scale=state_scale,
		facecolor='none'
	)

	# Geographic features
	ax.add_feature(cfeature.LAND, facecolor='lightgray', edgecolor='none', zorder=1)
	ax.add_feature(cfeature.LAKES, facecolor='white', edgecolor='0.25', linewidth=1.0, zorder=2)
	ax.add_feature(states_clipped, edgecolor='0.25', linewidth=3.5, zorder=4)
	ax.add_feature(cfeature.COASTLINE, edgecolor='0.25', linewidth=1.5, zorder=4)
	ax.add_feature(countries_clipped, edgecolor='0.25', linewidth=1.5, zorder=4)

	# Define domain
	if grid == 'northeast':   
		ax.set_extent([-82, -67, 38.75, 45.75], crs=ccrs.PlateCarree())
		# Increase this number (e.g., 1.4) to stretch it more vertically
		ax.set_aspect(1.25, adjustable='datalim')
	elif grid == 'conus':                
		ax.set_extent([-125, -64, 22, 57], crs=ccrs.PlateCarree())
                # Increase this number (e.g., 1.4) to stretch it more vertically
		ax.set_aspect(1.2, adjustable='datalim')
	elif grid == 'hawaii':
		ax.set_extent([-164, -148, 14, 25], crs=ccrs.PlateCarree())
		# Increase this number (e.g., 1.4) to stretch it more vertically
		ax.set_aspect(1.2, adjustable='datalim')

	# Plot the shading
	im = ax.contourf(lons, lats, mslps_data,
                     levels=mslps_levels,
		     norm=config['norm'], 
		     cmap=cmap_spread,
		     transform=ccrs.PlateCarree(),
		     extend='max',
		     zorder=3)

	# Overlay individual member spaghetti lines
	num_members = ensemble_stack.shape[0]
	for i in range(num_members):
		ax.contour(lons, lats, ensemble_stack[i],
			levels=[1004],
			colors='blue',
			linewidths=2.2,
			alpha=0.6,
			transform=ccrs.PlateCarree(),
			zorder=5)

	# Plot the contour lines
	contours = ax.contour(lons, lats, mslp_data,
                     	      levels=[1004],
			      colors='red', 
			      linewidths=3.0, 
			      transform=ccrs.PlateCarree(),
			      zorder=5)

	# Add labels to the lines (e.g., '1012')
	ax.clabel(contours, inline=True, fontsize=20, fmt='%i', inline_spacing=5)

	# Capture the colorbar in a variable (e.g., 'cbar')
	cbar = plt.colorbar(im, ax=ax, ticks=mslps_levels, orientation='horizontal', pad=0.06, fraction=0.055)
	ax.set_title(config['title'], fontweight='bold', fontsize=24)

	# Set the label size for the ticks
	cbar.ax.tick_params(labelsize=24)

#################################################

# Add a title and adjust layout to prevent overlapping
plt.tight_layout()
plt.savefig(f"{MAP_PATH}/{grid}/{var}/ecaifs_ens_members_{var}_init{pdy}_{cyc}Z_f{fhr}.png", bbox_inches='tight', pad_inches=0.1)
