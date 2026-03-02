#!/bin/bash
###################################################
# Script to plot GFS forecast map comparisons
#
# Contributors: Alicia.Bentley@noaa.gov
# NOAA/NWS/NCEP/Environmental Modeling Center
###################################################
module reset
module load prod_envir/2.0.6
module load intel/19.1.3.304
module load python/3.8.6
module use /lfs/h1/mdl/nbm/save/apps/modulefiles
module load python-modules/3.8.6
export PYTHONPATH="${PYTHONPATH}:/lfs/h2/emc/vpppg/noscrub/Alicia.Bentley/python"
module load proj/7.1.0
module load geos/3.8.1
module load libjpeg-turbo/2.1.0
module load imagemagick/7.0.8-7
module load wgrib2/2.0.8_wmo
module load libjpeg/9c
module load grib_util/1.2.4

#===============================================================================================================
export CASE='feb2026'
export initdate="20260223"
export cyc="06"
export fhr="000"
export DOMAIN='eastcoast'

echo $CASE $initdate $cyc $fhr $DOMAIN

# *************************************************************
# ****Specify which models to plot, forecast hours, domains****
# *************************************************************
# Select which models to plot (YES/NO)
export PLOT_GFS_FCSTS=YES
export PLOT_AIGFS_FCSTS=NO
export PLOT_ECMWF_FCSTS=NO

export PLOT_GEFS_FCSTS=NO
export PLOT_AIGEFS_FCSTS=NO
export PLOT_HGEFS_FCSTS=NO

#===============================================================================================================
#===============================================================================================================
#===============================================================================================================

# ********************************************
# *****Specify paths to scripts and maps******
# ********************************************
# Location of your saved GFS/GEFS evaluation /plot_maps directory
export SCRIPTS_PATH='/lfs/h2/emc/vpppg/save/'${USER}'/meg_python/plot_maps'

# Location of downloaded forecast/analysis files
export DATA_PATH='/lfs/h2/emc/vpppg/noscrub/alicia.bentley/feb2026'

# Location to plot maps
export MAP_PATH='/lfs/h2/emc/vpppg/noscrub/'${USER}'/'${CASE}'/maps'
mkdir -p ${MAP_PATH}

#===============================================================================================================        
#===============================================  END CHANGES  =================================================
#===============================================================================================================

if [ $PLOT_GFS_FCSTS = YES ]; then
        echo "Kickoff scripts to plot GFS forecasts (Init.: ${initdate}${cyc} F${fhr} for ${DOMAIN})"
#        python ${SCRIPTS_PATH}/plot_gfs_500Z.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
        python ${SCRIPTS_PATH}/plot_gfs_mslp.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
        sleep 1
fi

if [ $PLOT_AIGFS_FCSTS = YES ]; then
        echo "Kickoff scripts to plot AIGFS forecasts (Init.: ${initdate}${cyc} F${fhr} for ${DOMAIN})"
        python ${SCRIPTS_PATH}/plot_aigfs_500Z.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
        sleep 1
fi

if [ $PLOT_ECMWF_FCSTS = YES ]; then
        echo "Kickoff scripts to plot ECMWF forecasts (Init.: ${initdate}${cyc} F${fhr} for ${DOMAIN})"
        python ${SCRIPTS_PATH}/plot_ecmwf_hires_500Z.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
        sleep 1
fi

if [ $PLOT_GEFS_FCSTS = YES ]; then
        echo "Kickoff scripts to plot GEFS forecasts (Init.: ${initdate}${cyc} F${fhr} for ${DOMAIN})"
#        python ${SCRIPTS_PATH}/plot_gefs_mean_500Z.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
        python ${SCRIPTS_PATH}/plot_gefs_spread_500Z.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
        sleep 1
fi

if [ $PLOT_AIGEFS_FCSTS = YES ]; then
        echo "Kickoff scripts to plot AIGEFS forecasts (Init.: ${initdate}${cyc} F${fhr} for ${DOMAIN})"
#        python ${SCRIPTS_PATH}/plot_aigefs_mean_500Z.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
        python ${SCRIPTS_PATH}/plot_aigefs_spread_500Z.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
        sleep 1
fi

if [ $PLOT_HGEFS_FCSTS = YES ]; then
        echo "Kickoff scripts to plot HGEFS forecasts (Init.: ${initdate}${cyc} F${fhr} for ${DOMAIN})"
#        python ${SCRIPTS_PATH}/plot_hgefs_mean_500Z.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
        python ${SCRIPTS_PATH}/plot_hgefs_spread_500Z.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
        sleep 1
fi

exit
