#!/bin/bash
#===========================================================
# Edit the top section only
#===========================================================

invest_stormID="aal982025"
named_stormID="aal132025"
ADECK_PATH="/lfs/h2/emc/vpppg/noscrub/alicia.bentley/adecks_aigefsdev"

#============================================================

echo "${invest_stormID}" "${named_stormID}" "${ADECK_PATH}"

for i in $(seq -f "mem%03g" 0 30); do
    mv "${ADECK_PATH}/${named_stormID}_${i}.dat" "${ADECK_PATH}/${named_stormID}_${i}.dat_partial"
    sed -i 's/AL, 98,/AL, 13,/g' "${ADECK_PATH}/${invest_stormID}_${i}.dat"
    cat "${ADECK_PATH}/${invest_stormID}_${i}.dat" "${ADECK_PATH}/${named_stormID}_${i}.dat_partial" > "${ADECK_PATH}/${named_stormID}_${i}.dat"
    echo "Finished member ${i}"
done

echo "All ensemble members .dat files were combined!"


