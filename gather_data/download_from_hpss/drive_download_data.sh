#!/bin/bash
###################################################
# Script to download forecasts/analyses from HPSS
#
# Contributors: Alicia.Bentley@noaa.gov
# NOAA/NWS/NCEP/Environmental Modeling Center
###################################################
module purge
module load envvar/1.0
module load intel/19.1.3.304
module load PrgEnv-intel/8.1.0
module load craype/2.7.10
module load cray-mpich/8.1.9
module load imagemagick/7.0.8-7
module load wgrib2/2.0.8_wmo
#Load Python
module load python/3.8.6
module load proj/7.1.0
module load geos/3.8.1
module use /lfs/h1/mdl/nbm/save/apps/modulefiles
module load python-modules/3.8.6
export PYTHONPATH="${PYTHONPATH}:/lfs/h2/emc/vpppg/noscrub/Alicia.Bentley/python"
counter=0
#===============================================================================================================
#==============================================  BEGIN CHANGES  ================================================
#===============================================================================================================

# **********************************************************
# ****Specify case name, paths, and sections to execute*****
# **********************************************************
# Specify case study name (e.g., dorian2019)
export CASE='GEFSarchive'

# Location of your saved /hpss_scripts directory
export SCRIPTS_PATH='/lfs/h2/emc/vpppg/save/'${USER}'/meg_python/gather_data/download_from_hpss'

# Location you want to save your downloaded forecast/analysis files
export DATA_PATH='/lfs/h2/emc/vpppg/noscrub/'${USER}'/'${CASE}'/data'

# Location to write output from submitted download data jobs (for troubleshooting)
export OUTPUT_PATH=${DATA_PATH}'/../output'

# Select which sections of code to execute (YES/NO)
export GET_ANALYSES=NO
export GET_FORECASTS=YES

# *****************************************
# ****This is the GET_ANALYSES section*****
# *****************************************
# Select which analysis types to download (YES/NO)
export GET_GFS_ANL=NO
export GET_CCPA_ANL=NO
export GET_GDAS_ANL=NO

# Select analyses start, end, and increment to download
export ANL_START=0 	# Start downloading analysis files for the first initialization date if set to 0
export ANL_END=12       # Stop downloading analysis files on the first init. date + 6 hours + X hours (set X to 378 if you want to go 16 days beyond last init date)
export ANL_INC=6 	# Typically 6 hours timestep between requested analysis files

# ******************************************
# ****This is the GET_FORECASTS section*****
# ******************************************
# Select which model forecasts to download (YES/NO)
export GET_GEFS_AVG_FCSTS_ATMOS=NO
export GET_GEFS_SPR_FCSTS_ATMOS=NO
export GET_GEFS_MEM_FCSTS_ATMOS=YES
export GET_GFS_FCSTS_ATMOS=NO
export GET_GFS_FCSTS_WAVE=NO
export GET_GFSv17_FCSTS_ATMOS=NO

# Select forecast start, end, and increment to download (applies to GEFS and GFS forecasts)
export FHR_START=0			 # Typically 0 hours (beginning of forecast)
export FHR_END=24   #192                    # Typically 384 or 240 hours (10-day forecast)
export FHR_INC=6                         # Typically 6-hour timestep between forecast files

# ******************************************
# ****Select initialization dates/hours*****
# ******************************************
# Specify initialization dates to download
for longdate in 20260819
do

# Specify the init. hours to download on each initalization date (typically 00 12)
for hour in 00 12
do

#===============================================================================================================	
#===============================================  END CHANGES  =================================================
#===============================================================================================================

if [ $counter = 0 ]; then
    	echo " "
    	echo "Starting drive_download_data.sh for: "$CASE
   	mkdir -p ${DATA_PATH}
fi

counter=$(($counter+1))
export CYCLE=${longdate}${hour}

echo "*********************"
if [ $GET_ANALYSES = YES ]; then
        echo "Creating lists of valid dates (for analysis files)"
        python ${SCRIPTS_PATH}/list_valid_dates.py ${CYCLE} ${ANL_START} ${ANL_END} ${ANL_INC} ${CASE}
        mv ${SCRIPTS_PATH}/${CASE}_valid_dates.txt ${DATA_PATH}/${CASE}_valid_dates.txt
	sleep 3
	echo "*********************"
	if [ $GET_GFS_ANL = YES ]; then
   		echo "Copy/submit script to download GFS analysis data"
   		${SCRIPTS_PATH}/create_htar_gfs_anl.sh
   		sleep 3
	fi
	echo "*********************"
	if [ $GET_CCPA_ANL = YES ]; then
   		echo "Copy/submit script to download CCPA analysis data"
   		${SCRIPTS_PATH}/create_htar_ccpa_anl.sh
   		sleep 3
	fi
        echo "*********************"
	if [ $GET_GDAS_ANL = YES ]; then
		echo "Copy/submit script to download GDAS analysis data"
		${SCRIPTS_PATH}/create_htar_gdas_anl.sh
		sleep 3
	fi
export GET_ANALYSES=NO
fi

echo "*********************"
if [ $GET_FORECASTS = YES ]; then
	if [ $counter = 1 ]; then
		echo "Create list of forecast hours (${FHR_START} ${FHR_END} ${FHR_INC})"
      		python ${SCRIPTS_PATH}/list_fhrs.py ${CYCLE} ${FHR_START} ${FHR_END} ${FHR_INC} ${CASE}
        	mv ${SCRIPTS_PATH}/${CASE}_fhrs.txt ${DATA_PATH}/${CASE}_fhrs.txt
		sleep 3
	fi	
	echo "*********************"
	if [ $GET_GEFS_AVG_FCSTS_ATMOS = YES ]; then
		echo "Create/submit script to download ops GEFS avg (mean) forecasts (Init.: ${CYCLE})"
		${SCRIPTS_PATH}/create_htar_gefs_avg_fcsts_atmos.sh
		sleep 3
	fi
        echo "*********************"
        if [ $GET_GEFS_SPR_FCSTS_ATMOS = YES ]; then
                echo "Create/submit script to download ops GEFS spr (spread) forecasts (Init.: ${CYCLE})"
                ${SCRIPTS_PATH}/create_htar_gefs_spr_fcsts_atmos.sh
                sleep 3
        fi
        if [ $GET_GEFS_MEM_FCSTS_ATMOS = YES ]; then
                echo "Create/submit script to download ops GEFS member forecasts (Init.: ${CYCLE})"
		for mem in c00 p01 p02 p03 p04 p05 p06 p07 p08 p09 p10 p11 p12 p13 p14 p15 p16 p17 p18 p19 p20 p21 p22 p23 p24 p25 p26 p27 p28 p29 p30
		do
			echo "Submitting job for member ${mem}..."
                	${SCRIPTS_PATH}/create_htar_gefs_mem_${mem}_fcsts_atmos.sh 
                	sleep 1
		done
        fi
        echo "*********************"
        if [ $GET_GFSv17_FCSTS_ATMOS = YES ]; then
                echo "Create/submit script to download GFSv17 atmos forecasts (Init.: ${CYCLE})"
                ${SCRIPTS_PATH}/create_htar_gfsv17_fcsts_atmos.sh
                sleep 3
        fi
	echo "*********************"
        if [ $GET_GFS_FCSTS_ATMOS = YES ]; then
                echo "Create/submit script to download ops GFS atmos forecasts (Init.: ${CYCLE})"
                ${SCRIPTS_PATH}/create_htar_gfs_fcsts_atmos.sh
                sleep 3
        fi
        echo "*********************"
        if [ $GET_GFS_FCSTS_WAVE = YES ]; then
                echo "Create/submit script to download ops GFS wave forecasts (Init.: ${CYCLE})"
                ${SCRIPTS_PATH}/create_htar_gfs_fcsts_wave.sh
                sleep 3
        fi
fi

done
done

exit
