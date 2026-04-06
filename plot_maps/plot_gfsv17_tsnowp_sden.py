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
var = "tsnowp"

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
        cmd = f"wgrib2 {filename_gfss} | grep ':TSNOWP'"
        # We use getoutput to keep it concise; it returns a string of the results
        output = subprocess.getoutput(cmd)

        if output:
            print("wgrib2 Output:\n", output)

            # Parse out the index (first column), convert to int, and subtract 1
            apcp_indices = [int(line.split(':')[0]) - 1 for line in output.strip().split('\n')]

            print(f"TSNOWP 0-based Indices: {apcp_indices}")

            # Grab the first TSNOWP index (full accumulation)
            target_idx = apcp_indices[0]

            # Select the specific messages we want
            #sden_start_msg = f_gfss.select(shortName='SDEN', level='surface')[0]

            # Extract the message and data
            tsnowp_start_msg = f_gfss[target_idx]
            tsnowp_start_data = tsnowp_start_msg.data * .03937 * 10.0  # Convert mm to inches and applies 10:1 SLR

            print(f"Extracted: {tsnowp_start_msg.shortName} for {tsnowp_start_msg.leadTime} hours")
            print(f"Max TSNOWP with SDEN: {tsnowp_start_data.max():.2f} inches")

        else:
            print("No TSNOWP found in file. Creating a zero-field for F000.")

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
            tsnowp_start_data = dummy_msg.data * 0.0

            print(f"Zero-field created using {dummy_msg.shortName} dimensions.")
            print(f"Max TSNOWP: {tsnowp_start_data.max():.2f} inches")

# Open GFS GRIB2 file at the end of the snowfall period and extract parameters
filename_gfs = f"/lfs/h2/emc/gfstemp/emc.global/EVS_archive/retrov17_01/gfs.{pdy}/{cyc}/products/atmos/grib2/0p25/gfs.t{cyc}z.pres_a.0p25.f{fhr_str}.grib2"
with grib2io.open(filename_gfs) as f_gfs:

    # Select the specific messages we want
    tsnowp_msg = f_gfs.select(shortName='TSNOWP', level='surface')[0]

    # Select the specific messages we want
    #sden_msg = f_gfs.select(shortName='SDEN', level='surface')[0]

    #print(f"Max SDEN: {np.nanmax(sden_msg.data)}")

    #slr_data = (1.0 / sden_msg.data)
    #slr_fill = np.ma.filled(slr_data, fill_value=10.0)

    #print(f"Min SLR: {slr_fill.min()}")
    #print(f"Max SLR: {slr_fill.max()}")

    # Extract values
    tsnowp_data = tsnowp_msg.data * .03937 * 10.0  # Convert mm to inches and applies 10:1

    # Calculate the difference (e.g., SNOD at end - SNOD at start)
    diff_data = tsnowp_data - tsnowp_start_data

    print(f"Max snowfall: {diff_data.max():.2f} inches")

    lats, lons = tsnowp_msg.latlons()

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
snod_levels = np.array([0.1, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0, 18.0, 24.0, 30.0, 36.0, 48.0])
snod_colors = ['#749DDE', '#588ADC', '#2F74C8', '#2364B9', '#1E559D', '#FFF68F', '#F4C430', '#ED781E', '#E23916', '#C92828', '#D986D9', '#D95DD9']

cmap = mcolors.ListedColormap(snod_colors)
#cmap.set_under('white')
cmap.set_over('#CD0ACD')

norm = mcolors.BoundaryNorm(snod_levels, ncolors=len(snod_colors))

# Update configs with specific 'norm' and 'levels'
plot_configs = [
        {'data': diff_data, 'cmap': cmap, 'norm': norm, 'levels': snod_levels, 'title': f'GFSv17 | {duration}-h Snowfall (TSNOWP with 10:1 SLR) (in.)\nInitialized: {init_dt.strftime("%Y-%m-%d %HZ")} (F{fhr_str}) | Valid: {valid_dt.strftime("%Y-%m-%d %HZ")}'},
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
	ax.add_feature(cfeature.COASTLINE, edgecolor='0.25', linewidth=1.5, zorder=4)
	ax.add_feature(cfeature.BORDERS, edgecolor='0.25', linewidth=1.5, zorder=4)
	ax.add_feature(cfeature.LAKES, facecolor='white', edgecolor='0.25', linewidth=1.0)
	
	# Add the land feature and shade it gray
	ax.add_feature(cfeature.LAND, facecolor='lightgray', edgecolor='none')
	# Add oceans for contrast (optional)
	ax.add_feature(cfeature.OCEAN, facecolor='white', zorder=3)

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

	# Plot the shading
	im = ax.contourf(lons, lats, config['data'], 
		     levels=config['levels'],
		     norm=config['norm'], 
		     cmap= config['cmap'],
		     transform=ccrs.PlateCarree(),
		     extend='max')

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
plt.savefig(f"{MAP_PATH}/{grid}/{var}/gfsv17_{var}_init{pdy}_{cyc}Z_f{fhr}.png", bbox_inches='tight', pad_inches=0.1)
