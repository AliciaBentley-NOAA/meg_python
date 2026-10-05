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
var = "htsgw_ndbc_buoys"
    
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

#Create the datetime object
# strptime converts the string to a datetime object
init_dt = datetime.strptime(init_str, "%Y%m%d").replace(hour=init_hour)

# Create maps directory
Path(f"{MAP_PATH}/{grid}/{var}").mkdir(parents=True, exist_ok=True)

#====================================

# 1. Open the GLWU GRIB2 file
filename = f"{DATA_PATH}/wave.{pdy}/glwu/grid2obs/glwu.grlc_2p5km.{pdy}.t{cyc}z.f{fhr}.grib2"
gfile = grib2io.open(filename)

# 2. Select the HTSGW message
# Discipline 10 (Oceanographic), Category 0 (Waves), Number 3 (Significant Height of Waves)
msg = gfile.select(shortName="HTSGW")[0]

# Extract data values and lat/lon coordinates
data = msg.data
lats, lons = msg.latlons()

# Adjust longitudes from [0, 360] to [-180, 180] for Cartopy if needed
lons = np.where(lons > 180, lons - 360, lons)

# 3. Set up the plot using Cartopy
fig = plt.figure(figsize=(12, 8), dpi=150)
ax = plt.axes(projection=ccrs.PlateCarree())

# Add geography
ax.add_feature(cfeature.LAND, facecolor="lightgray", zorder=1)
ax.add_feature(cfeature.COASTLINE, linewidth=0.8, zorder=3)
ax.add_feature(
    cfeature.LAKES, edgecolor="black", facecolor="none", linewidth=0.5, zorder=3
)
ax.add_feature(cfeature.BORDERS, linestyle=":", linewidth=0.8, zorder=3)
ax.add_feature(cfeature.STATES, linestyle=":", linewidth=0.5, zorder=3)

# Define domain bounds
lon_min, lon_max = -92.5, -75.5
lat_min, lat_max = 40.5, 49.5
ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=ccrs.PlateCarree())
# Force a custom aspect ratio
ax.set_aspect(1.3)

# 4. Plot the wave height field
# Mask invalid/missing values (grib2io sets bitmap missing values to np.nan or large values)
data_masked = np.ma.masked_invalid(data)

mesh = ax.pcolormesh(
    lons,
    lats,
    data_masked,
    cmap="Spectral_r",
    transform=ccrs.PlateCarree(),
    zorder=2,
    vmin=0,
    vmax=4,
)

# 5. Read and Plot NDBC Buoy Locations & IDs
xml_file = "/lfs/h2/emc/vpppg/noscrub/emc.vpppg/verification/EVS_fix/ndbc_stations/ndbc_stations.xml"

station_lons = []
station_lats = []
station_ids = []

with open(xml_file, "r") as f:
    for line in f:
        line = line.strip()
        if not line.startswith("<station"):
            continue
        try:
            station = ET.fromstring(line)
            st_id = station.get("id")
            lat = float(station.get("lat"))
            lon = float(station.get("lon"))

            if lon > 180:
                lon -= 360

            # Filter to domain
            if lon_min <= lon <= lon_max and lat_min <= lat <= lat_max:
                station_ids.append(st_id)
                station_lons.append(lon)
                station_lats.append(lat)
        except ET.ParseError:
            continue

# Plot buoy markers
ax.scatter(
    station_lons,
    station_lats,
    color="black",
    marker="o",
    s=25,
    edgecolor="white",
    linewidth=0.8,
    transform=ccrs.PlateCarree(),
    zorder=5,
)

# Plot buoy station IDs underneath markers
for st_id, lon, lat in zip(station_ids, station_lons, station_lats):
    ax.text(
        lon,
        lat - 0.12,
        st_id,
        fontsize=7,
        fontweight="bold",
        color="black",
        ha="center",
        va="top",
        transform=ccrs.PlateCarree(),
        zorder=5,
        bbox=dict(boxstyle="round,pad=0.15", facecolor="white", alpha=0.6, edgecolor="none")
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
cbar.set_label("Significant Wave Height (m)", fontsize=11)

# Extract timing metadata directly from the grib2io message object
ref_time = msg.refDate
fcst_time = int(msg.leadTime.total_seconds() / 3600)

plt.title(
    f"GLWU Significant Wave Height (HTSGW)\nInit. Date/Time: {ref_time} | Forecast Hour: {fcst_time}",
    fontsize=11,
    loc="left",
)

plt.tight_layout()
plt.savefig(f"{MAP_PATH}/{grid}/{var}/glwu_{var}_init{pdy}_{cyc}Z_f{fhr}.png", bbox_inches="tight")
print(f"Saved plot to {MAP_PATH}/{grid}/{var}/glwu_{var}_init{pdy}_{cyc}Z_f{fhr}.png")
