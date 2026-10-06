import sys
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np

# 1. Define paths and date range (June 1 to August 31, 2026)
start_date = datetime(2026, 6, 1)
end_date = datetime(2026, 8, 31)

base_dir = Path("/lfs/h2/emc/vpppg/noscrub/samira.ardani/evs_devonly/v2.0/prep/glwu")
out_dir = Path("/lfs/h2/emc/vpppg/save/alicia.bentley/glwu_means/ndbc")
out_dir.mkdir(parents=True, exist_ok=True)

# 2. Collect all daily NDBC directory paths
daily_ndbc_dirs = []
curr_date = start_date
while curr_date <= end_date:
    pdy = curr_date.strftime("%Y%m%d")
    ndbc_path = base_dir / f"wave.{pdy}" / "ndbc"
    if ndbc_path.exists():
        daily_ndbc_dirs.append(ndbc_path)
    else:
        print(f"Warning: NDBC directory missing, skipping: {ndbc_path}")
    curr_date += timedelta(days=1)

print(f"Found {len(daily_ndbc_dirs)} daily NDBC directories across June–August 2026.")

# Column names matching the standard NDBC 18-variable format
columns = [
    "YY", "MM", "DD", "hh", "mm", "WDIR", "WSPD", "GST", "WVHT",
    "DPD", "APD", "MWD", "PRES", "ATMP", "WTMP", "DEWP", "VIS", "PTDY", "TIDE"
]

# 3. Discover all unique station/buoy IDs across the entire JJA period
station_ids = set()
for d in daily_ndbc_dirs:
    for f in d.glob("*.txt"):
        station_ids.add(f.stem)

# Exclude unwanted inland buoys
excluded_stations = {"45151", "45152"}
station_ids = sorted(list(station_ids - excluded_stations))

print(f"Processing {len(station_ids)} unique NDBC stations...")

# 4. Loop through each buoy ID, gather all observations, and compute the seasonal mean
for st_id in station_ids:
    buoy_frames = []

    for d in daily_ndbc_dirs:
        buoy_file = d / f"{st_id}.txt"
        if buoy_file.exists():
            try:
                # Read file, treating '#' as comments and 'MM' as NaN
                # Using error_bad_lines=False for Pandas < 1.3 compatibility
                df = pd.read_csv(
                    buoy_file,
                    sep=r"\s+",
                    comment="#",
                    names=columns,
                    na_values=["MM"],
                    error_bad_lines=False,
                    engine="python"
                )
                if not df.empty:
                    buoy_frames.append(df)
            except Exception as e:
                print(f"Error reading {buoy_file}: {e}")

    if not buoy_frames:
        print(f"No valid data found for buoy {st_id}")
        continue

    # Combine all daily data frames for this buoy
    all_data = pd.concat(buoy_frames, ignore_index=True)

    # List of meteorological columns to average (excluding year/month/day/hour time columns)
    met_cols = [c for c in columns if c not in ["YY", "MM", "DD", "hh", "mm"]]

    # Convert columns to numeric (coercing non-numerics to NaN)
    for col in met_cols:
        all_data[col] = pd.to_numeric(all_data[col], errors="coerce")

    # Compute JJA mean for all variables (ignoring NaNs automatically)
    jja_means = all_data[met_cols].mean(numeric_only=True)

    # 5. Write the formatted output file for this buoy
    out_file = out_dir / f"{st_id}_JJA_2026_mean.txt"
    with open(out_file, "w") as f:
        f.write(f"# JJA 2026 Seasonal Mean for Station {st_id}\n")
        f.write(f"# Total Observations Read: {len(all_data)}\n")
        f.write("# Variable Mean_Value Units/Description\n")
        f.write("------------------------------------------\n")
        for col, val in jja_means.items():
            if pd.isna(val):
                f.write(f"{col:<8} MM\n")
            else:
                f.write(f"{col:<8} {val:.3f}\n")

    print(f"Saved: {out_file.name}")

print("Done processing all buoy seasonal averages!")
