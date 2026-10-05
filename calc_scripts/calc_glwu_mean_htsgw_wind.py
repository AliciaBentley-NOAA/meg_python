import sys
from datetime import datetime, timedelta
from pathlib import Path
import grib2io
import numpy as np

#=========================================================================

output_path_arg = str(sys.argv[1])    # /lfs/h2/emc/vpppg/save/alicia.bentley/glwu_means
cyc_arg = str(sys.argv[2]).zfill(2)   # Ensures '1' becomes '01', while '01' stays '01'

# 1. Define date range (June 1 to August 31, 2026)
start_date = datetime(2026, 6, 1)
end_date = datetime(2026, 8, 31)

# 2. Define input base path and output destination
base_dir = Path("/lfs/h2/emc/vpppg/noscrub/samira.ardani/evs_devonly/v2.0/prep/glwu")
out_dir = Path(output_path_arg)

# Ensure output directory exists
out_dir.mkdir(parents=True, exist_ok=True)
output_filepath = out_dir / f"glwu.grlc_2p5km.JJA_2026_mean.t{cyc_arg}z.f000.grib2"

# 3. Collect file paths for each day from June 1 to August 31
file_list = []
curr_date = start_date
while curr_date <= end_date:
    pdy = curr_date.strftime("%Y%m%d")
    filepath = (
        base_dir
        / f"wave.{pdy}"
        / "glwu"
        / "grid2obs"
        / f"glwu.grlc_2p5km.{pdy}.t{cyc_arg}z.f000.grib2"
    )
    if filepath.exists():
        file_list.append(filepath)
    else:
        print(f"Warning: File missing, skipping: {filepath}")
    curr_date += timedelta(days=1)

if not file_list:
    print("Error: No files found to process.")
    sys.exit(1)

print(f"Found {len(file_list)} valid GRIB2 files at {cyc_arg}Z across June–August 2026.")

# 4. Use the first file as a metadata template
template_file = grib2io.open(str(file_list[0]))
template_htsgw = template_file.select(shortName="HTSGW")[0]
template_wind = template_file.select(shortName="WIND")[0]

htsgw_list = []
wind_list = []

# 5. Read HTSGW and WIND data across all valid files
for fp in file_list:
    with grib2io.open(str(fp)) as gfile:
        try:
            htsgw_msg = gfile.select(shortName="HTSGW")[0]
            wind_msg = gfile.select(shortName="WIND")[0]

            htsgw_list.append(htsgw_msg.data)
            wind_list.append(wind_msg.data)
        except IndexError:
            print(f"Warning: Shortname HTSGW or WIND missing in {fp}")

template_file.close()

# 6. Compute mean across the time axis (axis 0)
# Convert input lists into masked arrays to respect native bitmap/missing values
htsgw_stack = np.ma.masked_invalid(np.array(htsgw_list))
wind_stack = np.ma.masked_invalid(np.array(wind_list))

# Calculate mean along axis 0 (returns a np.ma.MaskedArray)
htsgw_avg = np.ma.mean(htsgw_stack, axis=0)
wind_avg = np.ma.mean(wind_stack, axis=0)

# 7. Write the averaged data to the output GRIB2 file
with grib2io.open(str(output_filepath), mode="w") as out_gfile:
    # Assign masked array directly so grib2io encodes the bitmap correctly
    template_htsgw.data = htsgw_avg
    template_wind.data = wind_avg

    # Write HTSGW and WIND messages to the output GRIB2 file
    out_gfile.write(template_htsgw)
    out_gfile.write(template_wind)

print(f"Successfully generated average GRIB2 file: {output_filepath}")
