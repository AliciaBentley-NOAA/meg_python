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

#=================================================================================
#=================================================================================
# CASE name for data
export CASE='glwu_means'
export cyc='01'

# Location of your MEG calc scripts and where to save your finished plots
export SCRIPTS_PATH='/lfs/h2/emc/vpppg/save/'${USER}'/meg_python/calc_scripts'

# Location of downloaded forecast/analysis files
export DATA_PATH='/lfs/h2/emc/vpppg/save/alicia.bentley/'${CASE}

#=================================================================================
#=================================================================================

echo "Kickoff ${CASE} scripts to calc mean GLWU values (Cycle: ${cyc} F000 in ${DATA_PATH})"
python ${SCRIPTS_PATH}/calc_glwu_mean_htsgw_wind.py $DATA_PATH $cyc

exit
