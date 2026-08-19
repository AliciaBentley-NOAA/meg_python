#!/bin/bash

# --- User Defined Variables ---
YYYY="2026"
MM="08"
DD="16"

# Combine them for use in paths
YYYYMMDD="${YYYY}${MM}${DD}"

# --- Outer Loop: Iterate through the Cycles ---
for HH in 00 12; do

# --- Define Paths ---
# Using ${HH} in both the path and the filename pattern
SOURCE_DIR="/lfs/h1/ops/prod/dcom/${YYYYMMDD}/wgrbbul/ecmwf_hres"
DEST_DIR="/lfs/h2/emc/vpppg/noscrub/alicia.bentley/tc_lala/ecmwf.${YYYYMMDD}/${HH}/atmos"

# Create the destination directory if it doesn't exist
mkdir -p "$DEST_DIR"

echo "----------------------------------------------------------"
echo "Copying ECMWF ${HH}z data for ${YYYYMMDD}"
echo "Source: $SOURCE_DIR"
echo "Dest:   $DEST_DIR"
echo "----------------------------------------------------------"

# Loop from 0 to 240 in increments of 6
for h in $(seq 0 6 246); do
    # Format the forecast hour to be 3 digits (e.g., 000, 006, 012)
    HHH=$(printf "%03d" $h)

    # --- CALCULATE VALID DATE ---
        # 1. Create a timestamp for the START of the cycle
        # 2. Add 'h' hours to it
        # 3. Format it back to YYYYMMDD
        VALID_MMDD=$(date -d "${YYYYMMDD} ${HH} + ${h} hours" +%m%d)
        VALID_HH=$(date -d "${YYYYMMDD} ${HH} + ${h} hours" +%H)

    # Construct the filename
    if [ "$h" -eq 0 ]; then
        #FILE="HSD${MM}${DD}${HH}00${VALID_MMDD}${VALID_HH}011"
        FILE="HPD${MM}${DD}${HH}00${VALID_MMDD}${VALID_HH}011"
    else
        #FILE="HSD${MM}${DD}${HH}00${VALID_MMDD}${VALID_HH}001"  #contains surface variables
        FILE="HPD${MM}${DD}${HH}00${VALID_MMDD}${VALID_HH}001"   #contains pressure variables like 500-mb geopotential height
    fi

    if [ -f "$SOURCE_DIR/$FILE" ]; then
        cp "$SOURCE_DIR/$FILE" "$DEST_DIR/"
        echo "Copied: $FILE"
    else
        echo "MISSING: $SOURCE_DIR/$FILE"
    fi
done

echo "Finished ${HH}z cycle."

done

echo "=========================================================="
echo " All ECMWF cycles (00, 12) have been processed."
echo "=========================================================="
