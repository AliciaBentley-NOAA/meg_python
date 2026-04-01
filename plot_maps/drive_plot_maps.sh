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
export CASE='feb2025cold'
export initdate="20250219"
export cyc="00"
export fhr="024"

# Current domain options: conus, eastcoast, northeast, easternUS, southeastUS
export DOMAIN='conus'

#If plotting precip or snowfall, choose a duration (typically 24 or 36)
export duration='72'

#If plotting NOHRSC, select a valid time
export vdate="20260126" #Note to self, for 24 hour files, this is 1 day before the end of the period 
export vhour="12"

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

export PLOT_GFSv17_FCSTS=YES

export PLOT_NOHRSC_ANALYSIS=NO

#===============================================================================================================
#===============================================================================================================
#===============================================================================================================

# ********************************************
# *****Specify paths to scripts and maps******
# ********************************************
# Location of your saved GFS/GEFS evaluation /plot_maps directory
export SCRIPTS_PATH='/lfs/h2/emc/vpppg/save/'${USER}'/meg_python/plot_maps'

# Location of downloaded forecast/analysis files
#export DATA_PATH='/lfs/h2/emc/vpppg/noscrub/alicia.bentley/feb2026'
#export DATA_PATH='/lfs/h2/emc/vpppg/noscrub/alicia.bentley/GFSv16archive/data/'
export DATA_PATH='/lfs/h2/emc/vpppg/noscrub/emc.vpppg/verification/global/eval/model_data/gfs/prod'
#export DATA_PATH='/lfs/h2/emc/vpppg/noscrub/emc.vpppg/verification/global/archive/obs_data/nohrsc_accum24hr'


# Location to plot maps
export MAP_PATH='/lfs/h2/emc/vpppg/noscrub/'${USER}'/'${CASE}'/maps'
mkdir -p ${MAP_PATH}

#===============================================================================================================        
#===============================================  END CHANGES  =================================================
#===============================================================================================================

if [ $PLOT_GFS_FCSTS = YES ]; then
        echo "Kickoff ${CASE} scripts to plot GFS forecasts (Init.: ${initdate}${cyc} F${fhr} for ${DOMAIN})"
#        python ${SCRIPTS_PATH}/plot_gfs_500Z.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
#        python ${SCRIPTS_PATH}/plot_gfs_mslp.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
        python ${SCRIPTS_PATH}/plot_gfs_2m_temperature.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
#        python ${SCRIPTS_PATH}/plot_gfs_snod_contourf.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH $duration
#        python ${SCRIPTS_PATH}/plot_gfs_weasd_contourf.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH $duration
#        python ${SCRIPTS_PATH}/plot_gfs_weasd_verticalcolorbar.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH $duration
#        python ${SCRIPTS_PATH}/plot_gfs_hybrid1_mixing_ratios.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
	sleep 1
fi

if [ $PLOT_AIGFS_FCSTS = YES ]; then
        echo "Kickoff ${CASE} scripts to plot AIGFS forecasts (Init.: ${initdate}${cyc} F${fhr} for ${DOMAIN})"
#        python ${SCRIPTS_PATH}/plot_aigfs_500Z.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
        python ${SCRIPTS_PATH}/plot_aigfs_mslp.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
        sleep 1
fi

if [ $PLOT_ECMWF_FCSTS = YES ]; then
        echo "Kickoff ${CASE} scripts to plot ECMWF forecasts (Init.: ${initdate}${cyc} F${fhr} for ${DOMAIN})"
#        python ${SCRIPTS_PATH}/plot_ecmwf_hires_500Z.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
#        python ${SCRIPTS_PATH}/plot_ecmwf_hires_mslp.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
	python ${SCRIPTS_PATH}/plot_ecmwf_hires_snow.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH $duration
        sleep 1
fi

if [ $PLOT_GEFS_FCSTS = YES ]; then
        echo "Kickoff ${CASE} scripts to plot GEFS forecasts (Init.: ${initdate}${cyc} F${fhr} for ${DOMAIN})"
#        python ${SCRIPTS_PATH}/plot_gefs_mean_500Z.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
        python ${SCRIPTS_PATH}/plot_gefs_spread_500Z.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
#        python ${SCRIPTS_PATH}/plot_gefs_spread_mslp.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
        sleep 1
fi

if [ $PLOT_AIGEFS_FCSTS = YES ]; then
        echo "Kickoff ${CASE} scripts to plot AIGEFS forecasts (Init.: ${initdate}${cyc} F${fhr} for ${DOMAIN})"
#        python ${SCRIPTS_PATH}/plot_aigefs_mean_500Z.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
        python ${SCRIPTS_PATH}/plot_aigefs_spread_500Z.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
#        python ${SCRIPTS_PATH}/plot_aigefs_spread_mslp.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
        sleep 1
fi

if [ $PLOT_HGEFS_FCSTS = YES ]; then
        echo "Kickoff ${CASE} scripts to plot HGEFS forecasts (Init.: ${initdate}${cyc} F${fhr} for ${DOMAIN})"
#        python ${SCRIPTS_PATH}/plot_hgefs_mean_500Z.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
        python ${SCRIPTS_PATH}/plot_hgefs_spread_500Z.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
#        python ${SCRIPTS_PATH}/plot_hgefs_spread_mslp.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
        sleep 1
fi

if [ $PLOT_GFSv17_FCSTS = YES ]; then
        echo "Kickoff ${CASE} scripts to plot GFSv17 forecasts (Init.: ${initdate}${cyc} F${fhr} for ${DOMAIN})"
#        python ${SCRIPTS_PATH}/plot_gfsv17_500Z.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
#        python ${SCRIPTS_PATH}/plot_gfsv17_mslp.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
        python ${SCRIPTS_PATH}/plot_gfsv17_2m_temperature.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
#        python ${SCRIPTS_PATH}/plot_gfsv17_snod_contourf.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH $duration
#	python ${SCRIPTS_PATH}/plot_gfsv17_weasd_contourf.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH $duration
#        python ${SCRIPTS_PATH}/plot_gfsv17_hybrid1_mixing_ratios.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
	sleep 1
fi

if [ $PLOT_NOHRSC_ANALYSIS = YES ]; then
	export DATA_PATH='/lfs/h2/emc/vpppg/noscrub/emc.vpppg/verification/global/archive/obs_data/nohrsc_accum24hr'
	echo "Kickoff ${CASE} scripts to plot NOHRSC analysis (${duration}-h Period Valid: ${vdate}${vhour} for ${DOMAIN})"
#        python ${SCRIPTS_PATH}/plot_nohrsc_6h_files.py $vdate $vhour $DOMAIN $DATA_PATH $MAP_PATH $duration
        python ${SCRIPTS_PATH}/plot_nohrsc_24h_files.py $vdate $vhour $DOMAIN $DATA_PATH $MAP_PATH $duration
	sleep 1
fi


exit
