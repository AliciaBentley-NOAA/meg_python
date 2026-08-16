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
var = "500Z"

print(f"#############################################")

pdy = str(sys.argv[1])             # 20251120
cyc = str(sys.argv[2])             # 12
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

# Open ECMWF file and extract parameters from valid date
filename_ecmwf = f"{DATA_PATH}/ecmwf_aifs.{pdy}/{cyc}/atmos/{init_YYYY}{init_MM}{init_DD}{init_HH}0000-{new_hour}h-oper-fc.grib2"
print(filename_ecmwf)

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

filename_ecmwf_clean = get_uncompressed_grib(filename_ecmwf)

with grib2io.open(filename_ecmwf_clean) as f_ecmwf:

	hgt500_msg = f_ecmwf.select(shortName='HGT', level='500 mb')[0]

	# Extract values
	hgt500_data = hgt500_msg.data / 10.0  # Convert m to dam

	# Extract lats and lons from the first message (they share the same grid)
	lats, lons = hgt500_msg.latlons()

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

hgt500_data = hgt500_data[:, i_sort]

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
hgt500_norm = mcolors.Normalize(vmin=474, vmax=600)
hgt500_levels = np.arange(474, 606, 6)

# Update configs with specific 'norm' and 'levels'
plot_configs = [
        {'data': hgt500_data, 'cmap': 'gist_rainbow_r', 'norm': hgt500_norm, 'levels': hgt500_levels, 'title': f'EC-AIFS | 500-hPa Geopotential Height (dam)\nInitialized: {init_dt.strftime("%Y-%m-%d %HZ")} (F{fhr_str}) | Valid: {valid_dt.strftime("%Y-%m-%d %HZ")}'},
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
    ax.add_feature(states_clipped, edgecolor='0.25', linewidth=1.5, zorder=4)
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

    # Check if we are on the third panel and apply special cmap
    current_cmap = config['cmap']

    # Plot the shading 
    im = ax.contourf(lons, lats, config['data'],
		levels=config['levels'],
		norm=config['norm'], 
		cmap=current_cmap,
		transform=ccrs.PlateCarree(),
		extend='both',
		zorder=3)

    # Plot the contour lines
    contours = ax.contour(lons, lats, config['data'],
		levels=config['levels'],
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
plt.savefig(f"{MAP_PATH}/{grid}/{var}/ecaifs_{var}_init{pdy}_{cyc}Z_f{fhr}.png", bbox_inches='tight', pad_inches=0.1)
