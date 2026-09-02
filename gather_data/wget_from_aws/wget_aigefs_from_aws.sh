#!/bin/bash

# Configuration
CYCLE_DATE="20260819"
CYCLE_HOUR="12"
BASE_URL="https://noaa-nws-graphcastgfs-pds.s3.amazonaws.com/EAGLE_ensemble"

# List of forecast hours
# seq -f "%03g" <start> <increment> <end>
# FHOURS=($(seq -f "%03g" 0 6 192))
FHOURS=($(seq -f "%03g" 0 6 12))

# Loop through members mem000 to mem030
for mem in $(seq -f "%03g" 0 30); do
    MEMBER="mem${mem}"
    
    # Loop through forecast hours
    for fhr in "${FHOURS[@]}"; do
        FILE_NAME="aigefs.t${CYCLE_HOUR}z.pres.f${fhr}.grib2"
        FILE_URL="${BASE_URL}/aigefs.${CYCLE_DATE}/${CYCLE_HOUR}/${MEMBER}/model/atmos/grib2/${FILE_NAME}"
        
        # Define output directory structure to keep files organized
        OUT_DIR="./aigefs.${CYCLE_DATE}/${CYCLE_HOUR}/${MEMBER}"
        mkdir -p "${OUT_DIR}"
        
        echo "Downloading ${MEMBER} f${fhr}..."
        
        # Download file using wget (-q for quiet, -N to skip if already downloaded)
        wget -N -P "${OUT_DIR}" "${FILE_URL}"
    done
done

echo "Download complete!"
