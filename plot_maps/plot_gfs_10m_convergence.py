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
import metpy.calc as mpcalc
from metpy.units import units

#####################################################
var = "10m_convergence"

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
	mslp_msg = f_gfs.select(shortName='PRMSL', level='mean sea level')[0]
	u10_msg = f_gfs.select(shortName='UGRD', level='10 m above ground')[0]
	v10_msg = f_gfs.select(shortName='VGRD', level='10 m above ground')[0]

	# MetPy requires explicit physical units for grid calculations
	u10_units = u10_msg.data * (units.m / units.s)
	v10_units = v10_msg.data * (units.m / units.s)

	# Extract values
	mslp_data = mslp_msg.data / 100.0  # Convert Pa to hPa/mb
	u10_kts = u10_msg.data * 1.94384  # Convert m/s into kts
	v10_kts = v10_msg.data * 1.94384  # Convert m/s into kts

	# Extract data and coordinates
	lats, lons = mslp_msg.latlons()

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
u10_kts = u10_kts[:, i_sort]
v10_kts = v10_kts[:, i_sort]
u10_units = u10_units[:, i_sort]
v10_units = v10_units[:, i_sort]

# --- 1. Fast Grid Deltas ---
# Extract 1D lat/lon coordinate vectors (fastest approach for MetPy)
if lats.ndim == 2:
    lats_1d = lats[:, 0]
    lons_1d = lons[0, :]
else:
    lats_1d = lats
    lons_1d = lons

# Calculate dx and dy grid spacing from lat/lon arrays
dx, dy = mpcalc.lat_lon_grid_deltas(lons_1d, lats_1d)
print(f"Calculated dx and dy grid spacing")

# Divergence = dU/dx + dV/dy (units of 1/s)
divergence = mpcalc.divergence(u10_units, v10_units, dx=dx, dy=dy)

# Convergence is the negative of divergence
# Scale by 1e5 so values are easier to work with (e.g., 2 to 10 x 10^-5 s^-1)
convergence = -divergence.to('1/s').magnitude * 1e5

# --- 3. Optional: Smooth the Field ---
# Raw 10-m wind fields from 0.25-degree models can be noisy.
# Apply a light Gaussian filter for smoother contour lines.
convergence_smoothed = mpcalc.smooth_gaussian(convergence, n=6)
print(f"Successfully smoothed convergence!")

# --- 3. Crop to Plotting Domain BEFORE Contouring ---
# Example: Crop to US Domain (Lat: 20 to 55 N, Lon: -130 to -60 W / 230 to 300 E)
# Adjust these index slices or masks to match your map extent!
lat_mask = (lats_1d >= 20) & (lats_1d <= 55)
lon_mask = (lons_1d >= -130) & (lons_1d <= -60) if (lons_1d < 0).any() else (lons_1d >= 230) & (lons_1d <= 300)

# Slice 2D arrays down to regional domain
lats_trim = lats[np.outer(lat_mask, lon_mask)].reshape(np.sum(lat_mask), np.sum(lon_mask))
lons_trim = lons[np.outer(lat_mask, lon_mask)].reshape(np.sum(lat_mask), np.sum(lon_mask))
conv_trim = convergence_smoothed[lat_mask][:, lon_mask]

# Mask out values below threshold so Matplotlib ignores them completely
#conv_masked = np.where(conv_trim >= 4.0, conv_trim, np.nan)

# Sub-sample array by taking every 2nd point to dramatically speed up path generation
#lons_plot = lons_trim[::2, ::2]
#lats_plot = lats_trim[::2, ::2]
#conv_plot = conv_masked[::2, ::2]

#----------------------------------------------------------

# Thin the grid for wind barbs (0.25-degree GFS is dense!) ---
# Adjust skip based on your map domain:
# CONUS domain: skip = 12 to 15
# Regional / State domain: skip = 5 to 8
skip = 3

lats_sub = lats[::skip, ::skip]
lons_sub = lons[::skip, ::skip]
u10_sub = u10_kts[::skip, ::skip]
v10_sub = v10_kts[::skip, ::skip]

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
elif grid == 'westcoast':
    fig = plt.figure(figsize=(13, 12))
elif grid == 'alaska':
        fig = plt.figure(figsize=(12, 12))
elif grid == 'easternUS':
    fig = plt.figure(figsize=(13, 12))
elif grid == 'florida':
        fig = plt.figure(figsize=(12, 12))

# Define a 2x2 grid
gs = gridspec.GridSpec(1, 1, figure=fig)

# Define the specific normalization (Panel 1)
#mslp_norm = mcolors.Normalize(vmin=968, vmax=1052)
#mslp_levels = np.arange(968, 1056, 4)
mslp_norm = mcolors.Normalize(vmin=952, vmax=1052)
mslp_levels = np.arange(952, 1056, 4)
mslp_levels_lines = np.arange(932, 1060, 4)

# Define positive convergence levels (units of 10^-5 s^-1)
# e.g., 2, 4, 6, 8, 10, 12...
conv_levels = np.arange(2, 20, 2)

# Update configs with specific 'norm' and 'levels'
plot_configs = [
	{'data': mslp_data, 'cmap': 'gist_rainbow', 'norm': mslp_norm, 'levels': mslp_levels, 'title': f'GFS MSLP (hPa); 10-m wind (kt)/convergence (10^-5 s^-1) \nInitialized: {init_dt.strftime("%Y-%m-%d %HZ")} (F{fhr_str}) | Valid: {valid_dt.strftime("%Y-%m-%d %HZ")}'},
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
    elif grid == 'southeastUS':
        #ax.set_extent([-89, -76, 19.0, 34.0], crs=ccrs.PlateCarree())
        ax.set_extent([-86, -81, 21.0, 32.0], crs=ccrs.PlateCarree())
        # Increase this number (e.g., 1.4) to stretch it more vertically
        ax.set_aspect(1.25, adjustable='datalim')
    elif grid == 'westcoast':
        ax.set_extent([-148, -116, 29.0, 61.0], crs=ccrs.PlateCarree())
        # Increase this number (e.g., 1.4) to stretch it more vertically
        ax.set_aspect(1.25, adjustable='datalim')
    elif grid == 'alaska':
        ax.set_extent([-180, -130, 50.0, 70.0], crs=ccrs.PlateCarree())
        # Increase this number (e.g., 1.4) to stretch it more vertically
        ax.set_aspect(1.6, adjustable='datalim')
    elif grid == 'easternUS':
        ax.set_extent([-97, -72, 25.0, 48.0], crs=ccrs.PlateCarree())
        # Increase this number (e.g., 1.4) to stretch it more vertically
        ax.set_aspect(1.25, adjustable='datalim')
    elif grid == 'florida':
        ax.set_extent([-86, -81, 23.0, 34.0], crs=ccrs.PlateCarree())
        # Increase this number (e.g., 1.4) to stretch it more vertically
        ax.set_aspect(1.25, adjustable='datalim')

	# Check if we are on the third panel and apply special cmap
    #current_cmap = config['cmap']
    current_cmap = copy.copy(plt.get_cmap(config['cmap']))
    current_cmap.set_under('firebrick')
    current_cmap.set_over('deeppink')

	# Plot the shading
    im = ax.contourf(lons, lats, config['data'], 
		     levels=config['levels'],
		     norm=config['norm'], 
		     cmap=current_cmap,
		     transform=ccrs.PlateCarree(),
		     extend='both')

	# Plot the contour lines
    contours = ax.contour(lons, lats, config['data'], 
			      levels=mslp_levels_lines, 
			      colors='black', 
			      linewidths=2.0, 
			      transform=ccrs.PlateCarree())
	# Add labels to the lines (e.g., '1012')
	# Reduce padding (default is 4) to allow more labels to fit in tight spaces
    ax.clabel(contours, contours.levels[::2], inline=True, fontsize=18, fmt='%i', inline_spacing=8)

    # Plot positive convergence as solid red line contours
    print(f"About to plot convergence contours!")
    cs = ax.contour(
        lons_trim, lats_trim, conv_trim, 
        levels=conv_levels, 
        colors='red', 
        linewidths=1.5,
        transform=ccrs.PlateCarree()
    )
    # Add inline numerical labels on the contour lines
    #ax.clabel(cs, inline=True, fmt='%d', fontsize=9, inline_spacing=10)
    print(f"Successfully plotted convergence contours!")

    ax.barbs(
        lons_sub, lats_sub, u10_sub, v10_sub,
        length=7.5,
        linewidth=1.0,
        color='black',
        barbcolor='black',
        flagcolor='black',
        transform=ccrs.PlateCarree()
    )

	# Capture the colorbar in a variable (e.g., 'cbar')
    if grid == 'alaska':
        cbar = plt.colorbar(im, ax=ax, orientation='horizontal', pad=0.06, fraction=0.045)
    else:
        cbar = plt.colorbar(im, ax=ax, orientation='horizontal', pad=0.06, fraction=0.055)

    ax.set_title(config['title'], fontweight='bold', fontsize=24)

	# Set the label size for the ticks
    cbar.ax.tick_params(labelsize=24)

    print(f"All that is left is tight_layout() and savefig")
#################################################

# Add a title and adjust layout to prevent overlapping
plt.tight_layout()
plt.savefig(f"{MAP_PATH}/{grid}/{var}/gfsv16_{var}_init{pdy}_{cyc}Z_f{fhr}.png", bbox_inches='tight', pad_inches=0.1)
