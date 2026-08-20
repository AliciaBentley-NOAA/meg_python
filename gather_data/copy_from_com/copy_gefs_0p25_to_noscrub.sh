#!/bin/bash

# --- User Defined Variables ---
YYYYMMDD="20260806"

# --- Outer Loop: Iterate through the Cycles ---
for product in avg spr; do   #avg spr
for HH in 00 12; do   # 00 12

# --- Define Paths ---
# Using ${HH} in both the path and the filename pattern
SOURCE_DIR="/lfs/h1/ops/prod/com/gefs/v12.3/gefs.${YYYYMMDD}/${HH}/atmos/pgrb2sp25"
DEST_DIR="/lfs/h2/emc/vpppg/noscrub/alicia.bentley/tc_lala/gefs.${YYYYMMDD}/${HH}/atmos"

# Create the destination directory if it doesn't exist
mkdir -p "$DEST_DIR"

echo "----------------------------------------------------------"
echo "Copying GEFS ${HH}z data for ${YYYYMMDD}"
echo "Source: $SOURCE_DIR"
echo "Dest:   $DEST_DIR"
echo "----------------------------------------------------------"

# Loop from 0 to 240 in increments of 6
for h in $(seq 240 12 264); do
    # Format the forecast hour to be 3 digits (e.g., 000, 006, 012)
    HHH=$(printf "%03d" $h)
    
    # Construct the filename (e.g., gfs.t00z.pgrb2.0p25.f000)
    FILE="ge${product}.t${HH}z.pgrb2s.0p25.f${HHH}"
    
    if [ -f "$SOURCE_DIR/$FILE" ]; then
        cp "$SOURCE_DIR/$FILE" "$DEST_DIR/"
        echo "Copied: $FILE"
    else
        echo "MISSING: $SOURCE_DIR/$FILE"
    fi
done #h

echo "Finished ${HH}z cycle."

done #HH
done #product

echo "=========================================================="
echo " All GEFS cycles (00, 12) have been processed."
echo "=========================================================="
