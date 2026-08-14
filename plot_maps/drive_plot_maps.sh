#!/bin/bash
###################################################
# Script to drive MEG plotting scripts
#
# Contributors: Alicia.Bentley@noaa.gov
# NOAA/NWS/Office of Modeling and Development
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
export CASE='alb_flood'
export cyc="12"
export initdate="20260726"
export fhr="084"  #240,216,192,168,144,120,096,072,048,024
                  #228,204,180,156,132,108,084,060,036,012

# Current domain options: conus, wpc, eastcoast, northeast, easternUS, southeastUS, westcoast, florida
export DOMAIN='northeast'

#If plotting precip or snowfall, choose a duration (typically 24 or 36)
export duration='24'   #72, 48, 36, 24, 12, 6

#If plotting Stage IV, CCPA, NOHRSC, URMA, or RAP analysis, select a valid time
export vdate="20260730" #This is the last time in the period covered
export vhour="00"  #00, 06, 12, 18

#If plotting TC track/intensity
export longname="IanAL092022"

# *************************************************************
# ****Specify which models to plot, forecast hours, domains****
# *************************************************************
# Select which models to plot (YES/NO)
export PLOT_GEFS_FCSTS=NO
export PLOT_AIGEFS_FCSTS=NO
export PLOT_HGEFS_FCSTS=NO
export PLOT_ECENS_FCSTS=NO

export PLOT_GFS_FCSTS=NO
export PLOT_AIGFS_FCSTS=NO
export PLOT_ECMWF_FCSTS=NO
export PLOT_ECAIFS_FCSTS=YES

export PLOT_GFSv17_FCSTS=NO

export PLOT_ST4_ANALYSIS=NO
export PLOT_CCPA_ANALYSIS=NO
export PLOT_NOHRSC_ANALYSIS=NO
export PLOT_URMA_ANALYSIS=NO
export PLOT_RAP_ANALYSIS=NO

export PLOT_GFS_TC_FCSTS=NO
export PLOT_GFSv17_TC_FCSTS=NO

#===============================================================================================================
#===============================================================================================================
#===============================================================================================================

# ********************************************
# *****Specify paths to scripts and maps******
# ********************************************
# Location of your saved GFS/GEFS evaluation /plot_maps directory
export SCRIPTS_PATH='/lfs/h2/emc/vpppg/save/'${USER}'/meg_python/plot_maps'

# Location of downloaded forecast/analysis files
export DATA_PATH='/lfs/h2/emc/vpppg/noscrub/alicia.bentley/'${CASE}
#export DATA_PATH='/lfs/h2/emc/vpppg/noscrub/alicia.bentley/GFSv16archive/data'
#export DATA_PATH='/lfs/h2/emc/vpppg/noscrub/alicia.bentley/GFSv17archive/data'
#export DATA_PATH='/lfs/h2/emc/vpppg/noscrub/emc.vpppg/verification/global/eval/model_data/gfs/prod'
#export DATA_PATH='/lfs/h2/emc/gfstemp/emc.global/EVS_archive/retrov17_01'

# Location to plot maps
export MAP_PATH='/lfs/h2/emc/vpppg/noscrub/'${USER}'/'${CASE}'/maps'
mkdir -p ${MAP_PATH}

#===============================================================================================================        
#===============================================  END CHANGES  =================================================
#===============================================================================================================

if [ $PLOT_GFS_FCSTS = YES ]; then
        echo "======================================="
        echo "Kickoff ${CASE} scripts to plot GFS forecasts (Init.: ${initdate}${cyc} F${fhr} for ${DOMAIN})"
#        python ${SCRIPTS_PATH}/plot_gfs_orography.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
#        python ${SCRIPTS_PATH}/plot_gfs_orography_verticalcolorbar.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
#        python ${SCRIPTS_PATH}/plot_gfs_500Z.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
        python ${SCRIPTS_PATH}/plot_gfs_mslp.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
#        python ${SCRIPTS_PATH}/plot_gfs_10m_wind_mslp.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
#	 python ${SCRIPTS_PATH}/plot_gfs_10m_wind_ascent.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
#        python ${SCRIPTS_PATH}/plot_gfs_10m_convergence.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
#        python ${SCRIPTS_PATH}/plot_gfs_2m_temperature.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
#        python ${SCRIPTS_PATH}/plot_gfs_2m_dewpoint.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
#        python ${SCRIPTS_PATH}/plot_gfs_cape_sfc_based.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
#	 python ${SCRIPTS_PATH}/plot_gfs_precip.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH $duration
#	 python ${SCRIPTS_PATH}/plot_gfs_precip_verticalcolorbar.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH $duration
#        python ${SCRIPTS_PATH}/plot_gfs_snod_contourf.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH $duration
#        python ${SCRIPTS_PATH}/plot_gfs_weasd_contourf.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH $duration
#        python ${SCRIPTS_PATH}/plot_gfs_weasd_verticalcolorbar.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH $duration
#        python ${SCRIPTS_PATH}/plot_gfs_hybrid1_mixing_ratios.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
	sleep 1
fi

if [ $PLOT_AIGFS_FCSTS = YES ]; then
        echo "======================================="
        echo "Kickoff ${CASE} scripts to plot AIGFS forecasts (Init.: ${initdate}${cyc} F${fhr} for ${DOMAIN})"
#        python ${SCRIPTS_PATH}/plot_aigfs_500Z.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
        python ${SCRIPTS_PATH}/plot_aigfs_mslp.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
#        python ${SCRIPTS_PATH}/plot_aigfs_precip.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH $duration
        sleep 1
fi

if [ $PLOT_ECMWF_FCSTS = YES ]; then
        echo "======================================="
        echo "Kickoff ${CASE} scripts to plot ECMWF forecasts (Init.: ${initdate}${cyc} F${fhr} for ${DOMAIN})"
#        python ${SCRIPTS_PATH}/plot_ecmwf_hires_500Z.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
        python ${SCRIPTS_PATH}/plot_ecmwf_hires_mslp.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
#	 python ${SCRIPTS_PATH}/plot_ecmwf_hires_snow.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH $duration
#        python ${SCRIPTS_PATH}/plot_ecmwf_hires_precip.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH $duration
        sleep 1
fi

if [ $PLOT_ECAIFS_FCSTS = YES ]; then
        echo "======================================="
        echo "Kickoff ${CASE} scripts to plot ECAIFS forecasts (Init.: ${initdate}${cyc} F${fhr} for ${DOMAIN})"
        python ${SCRIPTS_PATH}/plot_ecaifs_precip.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH $duration
        sleep 1
fi

if [ $PLOT_GEFS_FCSTS = YES ]; then
        echo "======================================="
        echo "Kickoff ${CASE} scripts to plot GEFS forecasts (Init.: ${initdate}${cyc} F${fhr} for ${DOMAIN})"
#        python ${SCRIPTS_PATH}/plot_gefs_mean_500Z.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
        python ${SCRIPTS_PATH}/plot_gefs_mean_precip.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH $duration $vdate $vhour
#        python ${SCRIPTS_PATH}/plot_gefs_spread_500Z.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
#        python ${SCRIPTS_PATH}/plot_gefs_spread_mslp.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
        sleep 1
fi

if [ $PLOT_AIGEFS_FCSTS = YES ]; then
        echo "======================================="
        echo "Kickoff ${CASE} scripts to plot AIGEFS forecasts (Init.: ${initdate}${cyc} F${fhr} for ${DOMAIN})"
#        python ${SCRIPTS_PATH}/plot_aigefs_mean_500Z.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
        python ${SCRIPTS_PATH}/plot_aigefs_mean_precip.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH $duration $vdate $vhour
#        python ${SCRIPTS_PATH}/plot_aigefs_spread_500Z.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
#        python ${SCRIPTS_PATH}/plot_aigefs_spread_mslp.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
        sleep 1
fi

if [ $PLOT_HGEFS_FCSTS = YES ]; then
        echo "======================================="
        echo "Kickoff ${CASE} scripts to plot HGEFS forecasts (Init.: ${initdate}${cyc} F${fhr} for ${DOMAIN})"
#        python ${SCRIPTS_PATH}/plot_hgefs_mean_500Z.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
        python ${SCRIPTS_PATH}/plot_hgefs_mean_precip.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH $duration $vdate $vhour
#        python ${SCRIPTS_PATH}/plot_hgefs_spread_500Z.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
#        python ${SCRIPTS_PATH}/plot_hgefs_spread_mslp.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
        sleep 1
fi

if [ $PLOT_ECENS_FCSTS = YES ]; then
        echo "======================================="
        echo "Kickoff ${CASE} scripts to plot ECENS forecasts (Init.: ${initdate}${cyc} F${fhr} for ${DOMAIN})"
#        python ${SCRIPTS_PATH}/plot_ecens_spread_500Z.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
        python ${SCRIPTS_PATH}/plot_ecens_mean_precip.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH $duration
        sleep 1
fi

if [ $PLOT_GFSv17_FCSTS = YES ]; then
        echo "======================================="
        echo "Kickoff ${CASE} scripts to plot GFSv17 forecasts (Init.: ${initdate}${cyc} F${fhr} for ${DOMAIN})"
        export DATA_PATH='/lfs/h2/emc/gfstemp/emc.global/EVS_archive/retrov17_01'
#        python ${SCRIPTS_PATH}/plot_gfsv17_500Z.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
        python ${SCRIPTS_PATH}/plot_gfsv17_mslp.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
#        python ${SCRIPTS_PATH}/plot_gfsv17_diff_mslp.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
#        python ${SCRIPTS_PATH}/plot_gfsv17_2m_temperature.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
#        python ${SCRIPTS_PATH}/plot_gfsv17_diff_2mT.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
#        python ${SCRIPTS_PATH}/plot_gfsv17_2m_dewpoint.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
#        python ${SCRIPTS_PATH}/plot_gfsv17_diff_2mTd.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
#        python ${SCRIPTS_PATH}/plot_gfsv17_cape_sfc_based.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
#	 python ${SCRIPTS_PATH}/plot_gfsv17_diff_cape.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
#        python ${SCRIPTS_PATH}/plot_gfsv17_precip.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH $duration
#        python ${SCRIPTS_PATH}/plot_gfsv17_snod_contourf.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH $duration
# 	 python ${SCRIPTS_PATH}/plot_gfsv17_weasd_contourf.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH $duration
#	 python ${SCRIPTS_PATH}/plot_gfsv17_tsnowp_sden.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH $duration
#        python ${SCRIPTS_PATH}/plot_gfsv17_freezing_rain.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH $duration
#        python ${SCRIPTS_PATH}/plot_gfsv17_hybrid1_mixing_ratios.py $initdate $cyc $fhr $DOMAIN $DATA_PATH $MAP_PATH
	sleep 1
fi

if [ $PLOT_ST4_ANALYSIS = YES ]; then
        echo "======================================="
        export DATA_PATH='/lfs/h2/emc/vpppg/noscrub/alicia.bentley/alb_flood'
        echo "Kickoff ${CASE} scripts to plot Stage IV analysis (${duration}-h Period Valid: ${vdate}${vhour} for ${DOMAIN})"
        python ${SCRIPTS_PATH}/plot_stageiv_6h_files.py $vdate $vhour $DOMAIN $DATA_PATH $MAP_PATH $duration
        python ${SCRIPTS_PATH}/plot_stageiv_6h_files_verticalcolorbar.py $vdate $vhour $DOMAIN $DATA_PATH $MAP_PATH $duration
        sleep 1 
fi 

if [ $PLOT_CCPA_ANALYSIS = YES ]; then
        echo "======================================="
        export DATA_PATH='/lfs/h2/emc/vpppg/noscrub/emc.vpppg/verification/global/archive/obs_data/ccpa_accum6hr'
        echo "Kickoff ${CASE} scripts to plot CCPA analysis (${duration}-h Period Valid: ${vdate}${vhour} for ${DOMAIN})"
        python ${SCRIPTS_PATH}/plot_ccpa_6h_files.py $vdate $vhour $DOMAIN $DATA_PATH $MAP_PATH $duration
        sleep 1
fi

if [ $PLOT_NOHRSC_ANALYSIS = YES ]; then
        echo "======================================="
#	export DATA_PATH='/lfs/h2/emc/vpppg/noscrub/emc.vpppg/verification/global/archive/obs_data/nohrsc_accum24hr'
	echo "Kickoff ${CASE} scripts to plot NOHRSC analysis (${duration}-h Period Valid: ${vdate}${vhour} for ${DOMAIN})"
        python ${SCRIPTS_PATH}/plot_nohrsc_6h_files.py $vdate $vhour $DOMAIN $DATA_PATH $MAP_PATH $duration
#        python ${SCRIPTS_PATH}/plot_nohrsc_24h_files.py $vdate $vhour $DOMAIN $DATA_PATH $MAP_PATH $duration
	sleep 1
fi

if [ $PLOT_URMA_ANALYSIS = YES ]; then
        echo "======================================="
        export DATA_PATH='/lfs/h2/emc/vpppg/noscrub/alicia.bentley/urma_data'
	echo "Kickoff ${CASE} scripts to plot URMA analysis (Valid: ${vdate}${vhour} for ${DOMAIN})"
#        python ${SCRIPTS_PATH}/plot_urma_2m_temperature.py $vdate $vhour $DOMAIN $DATA_PATH $MAP_PATH
        python ${SCRIPTS_PATH}/plot_urma_2m_dewpoint.py $vdate $vhour $DOMAIN $DATA_PATH $MAP_PATH
	sleep 1
fi

if [ $PLOT_RAP_ANALYSIS = YES ]; then
        echo "======================================="
        export DATA_PATH='/lfs/h2/emc/vpppg/noscrub/alicia.bentley/rap_data'
        echo "Kickoff ${CASE} scripts to plot RAP analysis (Valid: ${vdate}${vhour} for ${DOMAIN})"
        python ${SCRIPTS_PATH}/plot_rap_cape_sfc_based.py $vdate $vhour $DOMAIN $DATA_PATH $MAP_PATH
        sleep 1
fi

if [ $PLOT_GFS_TC_FCSTS = YES ]; then
        echo "======================================="
        echo "Kickoff ${CASE} scripts to plot GFS TC forecasts for ${longname}"
        python ${SCRIPTS_PATH}/plot_TC_samemodel.py GFS $longname
	sleep 1
fi

if [ $PLOT_GFSv17_TC_FCSTS = YES ]; then
        echo "======================================="
        echo "Kickoff ${CASE} scripts to plot GFS TC forecasts for ${longname}"
        python ${SCRIPTS_PATH}/plot_TC_samemodel.py RETR $longname
        sleep 1
fi

exit
