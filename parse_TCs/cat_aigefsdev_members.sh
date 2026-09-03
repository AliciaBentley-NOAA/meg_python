#!/bin/bash

ADECK_PATH="/lfs/h2/emc/vpppg/noscrub/alicia.bentley/adecks_aigefsdev"
echo ${ADECK_PATH}

for i in $(seq -f "mem%03g" 0 30); do
    mv ${ADECK_PATH}"/aal132025_${i}.dat" ${ADECK_PATH}"/aal132025_${i}.dat_partial"
    sed -i 's/AL, 98,/AL, 13,/g' ${ADECK_PATH}"/aal982025_${i}.dat"
    cat ${ADECK_PATH}"/aal982025_${i}.dat" ${ADECK_PATH}"/aal132025_${i}.dat_partial" > ${ADECK_PATH}"/aal132025_${i}.dat"
    echo "Finished member "${i}
done

echo "All ensemble members combined .dat files were processed!"


