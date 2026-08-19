#!/bin/bash

# --- User Defined Variables ---
YYYYMMDD="20260807"

# --- Outer Loop: Iterate through the Cycles ---
for HH in 00 12; do   # 00 12

# --- Define Paths ---
# Using ${HH} in both the path and the filename pattern
SOURCE_DIR="/lfs/h1/ops/prod/com/aigefs/v1.0/aigefs.${YYYYMMDD}/${HH}"
DEST_DIR="/lfs/h2/emc/vpppg/noscrub/alicia.bentley/tc_lala/aigefs.${YYYYMMDD}/${HH}/atmos"

# Create the destination directory if it doesn't exist
mkdir -p "$DEST_DIR"

echo "----------------------------------------------------------"
echo "Copying GEFS ${HH}z data for ${YYYYMMDD}"
echo "Source: $SOURCE_DIR"
echo "Dest:   $DEST_DIR"
echo "----------------------------------------------------------"

# Loop from 0 to 240 in increments of 6
for h in $(seq 216 12 264); do
    # Format the forecast hour to be 3 digits (e.g., 000, 006, 012)
    HHH=$(printf "%03d" $h)

    for member in $(seq 0 1 30); do
        printf -v mem_name "mem%03d" "$member"
 
        # Construct the filename
        FILE="aigefs.t${HH}z.sfc.f${HHH}.grib2"
    
        if [ -f "$SOURCE_DIR/$mem_name/model/atmos/grib2/$FILE" ]; then
            cp "$SOURCE_DIR/$mem_name/model/atmos/grib2/$FILE" "${DEST_DIR}/${mem_name}_${FILE}"
            echo "Copied: ${mem_name}_$FILE"
        else
            echo "MISSING: $SOURCE_DIR/$mem_name/model/atmos/grib2/$FILE"
        fi

    done #member
done #h

echo "Finished ${HH}z cycle on ${YYYYMMDD}."

done #HH

echo "=========================================================="
echo " All AIGEFS members and cycles (00, 12) have been processed."
echo "=========================================================="
