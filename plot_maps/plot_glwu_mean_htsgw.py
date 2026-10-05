import time, os, sys
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import grib2io
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET

#====================================
var = "htsgw_mean"
    
cyc = str(sys.argv[1])             # 12 
fhr = str(sys.argv[2])             # 024 (3 digits) 
grid = str(sys.argv[3])            # conus
DATA_PATH = str(sys.argv[4])       # /lfs/h2/emc/vpppg/noscrub/alicia.bentley/feb2026
MAP_PATH = str(sys.argv[5])        # /lfs/h2/emc/vpppg/noscrub/alicia.bentley/feb2026/maps

show_colorbar="yes"

print("cyc:", cyc)
print("fhr:", fhr)
print("grid:", grid)

init_hour = int(cyc)

# Create maps directory
Path(f"{MAP_PATH}/{grid}/{var}").mkdir(parents=True, exist_ok=True)

#====================================

# 1. Open the GLWU GRIB2 file
filename = f"{DATA_PATH}/glwu.grlc_2p5km.JJA_2026_mean.t{cyc}z.f{fhr}.grib2"
gfile = grib2io.open(filename)

# 2. Select the HTSGW message
# Discipline 10 (Oceanographic), Category 0 (Waves), Number 3 (Significant Height of Waves)
msg = gfile.select(shortName="HTSGW")[0]

# Extract data values and lat/lon coordinates
data = msg.data
lats, lons = msg.latlons()

# Adjust longitudes from [0, 360] to [-180, 180] for Cartopy if needed
lons = np.where(lons > 180, lons - 360, lons)

# Extract timing metadata
lead_time_td = msg.leadTime                        # timedelta object
fcst_time = int(lead_time_td.total_seconds() / 3600)  # forecast lead time in hours

# 3. Set up the plot using Cartopy
fig = plt.figure(figsize=(12, 8), dpi=150)
ax = plt.axes(projection=ccrs.PlateCarree())

# Add geography
ax.add_feature(cfeature.LAND, facecolor="lightgray", zorder=1)
ax.add_feature(cfeature.COASTLINE, linewidth=0.8, zorder=3)
ax.add_feature(cfeature.LAKES, edgecolor="black", facecolor="none", linewidth=0.5, zorder=3)
ax.add_feature(cfeature.BORDERS, linestyle=":", linewidth=0.8, zorder=3)
ax.add_feature(cfeature.STATES, linestyle=":", linewidth=0.5, zorder=3)

# Define domain bounds
lon_min, lon_max = -92.5, -75.5
lat_min, lat_max = 40.5, 49.5
ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=ccrs.PlateCarree())
# Force a custom aspect ratio
ax.set_aspect(1.3)

# 4. Mask both invalid/NaN values and land grid points (where wave height is 0 or negative)
data_masked = np.ma.masked_where((np.isnan(data)) | (data <= 0.0), data)

# Convert from meters to feet (1 meter = 3.28084 feet)
data_feet = data_masked * 3.28084

# Plot using pcolormesh (adjusted vmin and vmax for feet)
mesh = ax.pcolormesh(
    lons,
    lats,
    data_feet,
    cmap="Spectral_r",
    transform=ccrs.PlateCarree(),
    zorder=2,
    vmin=0.001,  
    vmax=6,    # Adjusted vmax for wave height in feet (e.g., 12 ft ~ 3.6 m)
)

# 6. Colorbar and Gridlines
# Pass 1: Draw 1-degree gridlines with NO labels
gl1 = ax.gridlines(
    crs=ccrs.PlateCarree(),
    draw_labels=False,
    linestyle="--",
    alpha=0.5,
    zorder=4,
)
gl1.xlocator = mticker.MultipleLocator(1.0)
gl1.ylocator = mticker.MultipleLocator(1.0)

# Pass 2: Draw labels every 2 degrees (alpha=0 prevents duplicate lines)
gl2 = ax.gridlines(
    crs=ccrs.PlateCarree(),
    draw_labels=True,
    linestyle="--",
    alpha=0.0,
    zorder=4,
)
gl2.xlocator = mticker.MultipleLocator(2.0)
gl2.ylocator = mticker.MultipleLocator(1.0)
gl2.top_labels = False
gl2.right_labels = False

# Colorbar definition
cbar = plt.colorbar(mesh, ax=ax, orientation="vertical", pad=0.02, shrink=0.7)
cbar.set_label("Significant Wave Height (ft)", fontsize=11)

# Title with both Initialization and Valid times
plt.title(
    f"Mean GLWU Significant Wave Height (HTSGW)\n"
    f"Initialized: {cyc}Z cycles (F{fcst_time:03d}) | Valid: June-August 2026",
    fontsize=11,
    loc="left",
)

plt.tight_layout()
plt.savefig(f"{MAP_PATH}/{grid}/{var}/glwu_{var}_JJA_2026_mean_{cyc}Z_f{fhr}.png", bbox_inches="tight")
print(f"Saved plot to {MAP_PATH}/{grid}/{var}/glwu_{var}_JJA_2026_mean_{cyc}Z_f{fhr}.png")
