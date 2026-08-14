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
from metpy.plots import USCOUNTIES

#####################################################
var = "precip"

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
start_dt = valid_dt - duration_delta    # Remember: Valid time in NOHRSC filenames is at the *end* of the 6-h period

# Print the results in a readable format
print(f"Initialization Time: {init_dt.strftime('%Y-%m-%d %HZ')}")
print(f"Forecast Lead:       {fcst_hour} hours")
print(f"Start Time:          {start_dt.strftime('%Y-%m-%d %HZ')}")
print(f"Valid Time:          {valid_dt.strftime('%Y-%m-%d %HZ')}")

# Open GFS GRIB2 file at the start of the snowfall period and extract parameters
filename_gfss = f"/lfs/h2/emc/gfstemp/emc.global/EVS_archive/retrov17_01/gfs.{pdy}/{cyc}/products/atmos/grib2/0p25/gfs.t{cyc}z.pres_a.0p25.f{start_fhr_str}.grib2"
with grib2io.open(filename_gfss) as f_gfss:

        # Run wgrib2 and grab lines with APCP
        cmd = f"wgrib2 {filename_gfss} | grep 'APCP'"
        # We use getoutput to keep it concise; it returns a string of the results
        output = subprocess.getoutput(cmd)

        if output:
            print("wgrib2 Output:\n", output)
    
            # Parse out the index (first column), convert to int, and subtract 1
            apcp_indices = [int(line.split(':')[0]) - 1 for line in output.strip().split('\n')]
    
            print(f"APCP 0-based Indices: {apcp_indices}")

            # Grab the second APCP index (the 0-1 day total)
            target_idx = apcp_indices[1]

            # Extract the message and data
            precip_start_msg = f_gfss[target_idx]
            precip_start_data = precip_start_msg.data * 0.0393701 # Convert mm to inches

            print(f"Extracted: {precip_start_msg.shortName} for {precip_start_msg.leadTime} hours")
            print(f"Max Precip: {precip_start_data.max():.2f} inches")

        else:
            print("No APCP found in file. Creating a zero-field for F000.")
            
            # 1. Grab PRMSL (or any surface variable) to get the correct grid dimensions
            # We can use your manual index search or the select method if PRMSL is indexed
            try:
                # PRMSL is almost always the first message or easily found
                dummy_msg = f_gfss.select(shortName='PRMSL')[0]
            except:
                # Fallback: just grab the very first message in the file if select fails
                dummy_msg = f_gfss[0]
            
            # 2. Create a data array of zeros with the same shape as the grid
            # Multiplying the existing data by 0.0 is the safest way to preserve shape
            precip_start_data = dummy_msg.data * 0.0
            
            print(f"Zero-field created using {dummy_msg.shortName} dimensions.")
            print(f"Max Precip: {precip_start_data.max():.2f} inches")

# Open GFS GRIB2 file at the end of the snowfall period and extract parameters
filename_gfs = f"/lfs/h2/emc/gfstemp/emc.global/EVS_archive/retrov17_01/gfs.{pdy}/{cyc}/products/atmos/grib2/0p25/gfs.t{cyc}z.pres_a.0p25.f{fhr_str}.grib2"
with grib2io.open(filename_gfs) as f_gfs:

        # Run wgrib2 and grab lines with APCP
        cmd = f"wgrib2 {filename_gfs} | grep 'APCP'"
        # We use getoutput to keep it concise; it returns a string of the results
        output = subprocess.getoutput(cmd)

        if output:
            print("wgrib2 Output:\n", output)

            # Parse out the index (first column), convert to int, and subtract 1
            apcp_indices = [int(line.split(':')[0]) - 1 for line in output.strip().split('\n')]

            print(f"APCP 0-based Indices: {apcp_indices}")

            # Grab the second APCP index (the 0-1 day total)
            target_idx = apcp_indices[1]

            # Extract the message and data
            precip_msg = f_gfs[target_idx]
            precip_data = precip_msg.data * 0.0393701 # Convert mm to inches

            print(f"Extracted: {precip_msg.shortName} for {precip_msg.leadTime} hours")
            print(f"Max Precip: {precip_data.max():.2f} inches")

        # Calculate the difference (e.g., SNOD at end - SNOD at start)
        diff_data = precip_data - precip_start_data

        lats, lons = precip_msg.latlons()

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

diff_data = diff_data[:, i_sort]

# Finding the values
minimum = np.min(diff_data)
maximum = np.max(diff_data)

# Printing the results
print(f"The minimum precip is: {minimum}")
print(f"The maximum precip is: {maximum}")

#########################################################


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
#snod_levels = np.array([0.01, 0.1, 0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.5, 3, 4, 5, 7, 10, 15, 20])
snod_levels = np.array([0.01, 0.1, 0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.5, 3, 4, 5, 6, 8, 10, 12])

snod_colors = [
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

cmap = mcolors.ListedColormap(snod_colors)
#cmap.set_under('white')
cmap.set_over('tan')

norm = mcolors.BoundaryNorm(snod_levels, ncolors=len(snod_colors))

# Update configs with specific 'norm' and 'levels'
plot_configs = [
	{'data': diff_data, 'cmap': cmap, 'norm': norm, 'levels': snod_levels, 'title': f'GFSv17 | {duration}-h Accumulated Precipitation (in.)\nInitialized: {init_dt.strftime("%Y-%m-%d %HZ")} (F{fhr_str}) | Valid: {valid_dt.strftime("%Y-%m-%d %HZ")}'},
]

# Define the grid locations: [row, col] or [row, span]
# gs[0, 0] = Top Left, gs[0, 1] = Top Right, gs[1, :] = Bottom Center
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
    ax.add_feature(states_clipped, edgecolor='0.25', linewidth=2.5, zorder=4)
    ax.add_feature(cfeature.COASTLINE, edgecolor='0.25', linewidth=1.5, zorder=4)
    ax.add_feature(countries_clipped, edgecolor='0.25', linewidth=1.5, zorder=4)
    ax.add_feature(USCOUNTIES, edgecolor='black', linewidth=0.3, alpha=0.6, zorder=5)

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
		     extend='max',
		     zorder=3)

	# Capture the colorbar in a variable (e.g., 'cbar')
    cbar = plt.colorbar(im, ax=ax, ticks=snod_levels, orientation='horizontal', pad=0.06, fraction=0.061, shrink=0.95) # fraction is height, shrink is width
    ax.set_title(config['title'], fontweight='bold', fontsize=24)

	# Set the label size for the ticks
    cbar.ax.tick_params(labelsize=20)

	# Optional: Ensure the labels are formatted nicely (e.g., no extra decimals)
    cbar.ax.set_xticklabels([f'{l:g}' for l in snod_levels])

#################################################

# Add a title and adjust layout to prevent overlapping
plt.tight_layout()
plt.savefig(f"{MAP_PATH}/{grid}/{var}/gfsv17_{var}_init{pdy}_{cyc}Z_f{fhr}.png", bbox_inches='tight', pad_inches=0.1)
