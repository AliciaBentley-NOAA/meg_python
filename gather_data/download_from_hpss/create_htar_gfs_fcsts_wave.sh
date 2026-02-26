#!/bin/bash
##############################################
# Script for submitting jobs on WCOSS2
# that download data from HPSS
##############################################

echo data path: ${DATA_PATH}
echo output path: ${OUTPUT_PATH}
echo CYCLE: ${CYCLE}
#echo fhr_inc: ${FHR_INC}
#echo fhr_start: ${FHR_START}
#echo fhr_end: ${FHR_END}

mkdir -p ${OUTPUT_PATH}

export YYYY=`echo $CYCLE | cut -c 1-4`
export YYYYMM=`echo $CYCLE | cut -c 1-6`
export YYYYMMDD=`echo $CYCLE | cut -c 1-8`
export HH=`echo $CYCLE | cut -c 9-10`

mkdir -p ${DATA_PATH}/untar_fcsts/untar_gfs/gfs.${YYYYMMDD}/${HH}
mkdir -p ${DATA_PATH}/gfs.${YYYYMMDD}/${HH}/wave
#echo ${DATA_PATH}/gfs.${YYYYMMDD}/${HH}/wave

export FHHH_temp='`echo $line`'
export FHHH_same='${FHHH}'

file="${DATA_PATH}/${CASE}_fhrs.txt"

#################################################################################################
#----------------------- Info. to download ops GFS forecasts ------------------------------------
export GFS_CHANGE_DATE6=2022112900
export GFS_CHANGE_DATE5=2022062700
export GFS_CHANGE_DATE4=2021031812
export GFS_CHANGE_DATE3=2020022600
export GFS_CHANGE_DATE2=2019061200
export GFS_CHANGE_DATE1=2017072000
export GFS_CHANGE_DATE0=2016051000

if ((${CYCLE} >= ${GFS_CHANGE_DATE6})) ; then
        GFS_ARCHIVE=/NCEPPROD/hpssprod/runhistory/rh${YYYY}/${YYYYMM}/${YYYYMMDD}/com_gfs_v16.3_gfs.${YYYYMMDD}_${HH}.gfswave_output.tar
        GFS_FILENAME=./gfs.${YYYYMMDD}/${HH}/wave/gridded/gfswave.t${HH}z.global.0p25.f${FHHH_same}.grib2

elif (((${CYCLE} >= ${GFS_CHANGE_DATE5}) && (${CYCLE} < ${GFS_CHANGE_DATE6}))) ; then
        GFS_ARCHIVE=/NCEPPROD/hpssprod/runhistory/rh${YYYY}/${YYYYMM}/${YYYYMMDD}/com_gfs_v16.2_gfs.${YYYYMMDD}_${HH}.gfswave_output.tar
        GFS_FILENAME=./gfs.${YYYYMMDD}/${HH}/wave/gridded/gfswave.t${HH}z.global.0p25.f${FHHH_same}.grib2

elif (((${CYCLE} >= ${GFS_CHANGE_DATE4}) && (${CYCLE} < ${GFS_CHANGE_DATE5}))) ; then
        GFS_ARCHIVE=/NCEPPROD/hpssprod/runhistory/rh${YYYY}/${YYYYMM}/${YYYYMMDD}/com_gfs_prod_gfs.${YYYYMMDD}_${HH}.gfswave_output.tar
        GFS_FILENAME=./gfs.${YYYYMMDD}/${HH}/wave/gridded/gfswave.t${HH}z.global.0p25.f${FHHH_same}.grib2

elif (((${CYCLE} >= ${GFS_CHANGE_DATE3}) && (${CYCLE} < ${GFS_CHANGE_DATE4}))) ; then
        GFS_ARCHIVE=/NCEPPROD/hpssprod/runhistory/rh${YYYY}/${YYYYMM}/${YYYYMMDD}/com_gfs_prod_gfs.${YYYYMMDD}_${HH}.gfs_pgrb2.tar
        GFS_FILENAME=./gfs.${YYYYMMDD}/${HH}/gfs.t${HH}z.pgrb2.0p25.f${FHHH_same}

elif (((${CYCLE} >= ${GFS_CHANGE_DATE2}) && (${CYCLE} < ${GFS_CHANGE_DATE3}))) ; then
        GFS_ARCHIVE=/NCEPPROD/hpssprod/runhistory/rh${YYYY}/${YYYYMM}/${YYYYMMDD}/gpfs_dell1_nco_ops_com_gfs_prod_gfs.${YYYYMMDD}_${HH}.gfs_pgrb2.tar
        GFS_FILENAME=./gfs.${YYYYMMDD}/${HH}/gfs.t${HH}z.pgrb2.0p25.f${FHHH_same}

elif (((${CYCLE} >= ${GFS_CHANGE_DATE1}) && (${CYCLE} < ${GFS_CHANGE_DATE2}))) ; then
        GFS_ARCHIVE=/NCEPPROD/hpssprod/runhistory/rh${YYYY}/${YYYYMM}/${YYYYMMDD}/gpfs_hps_nco_ops_com_gfs_prod_gfs.${CYCLE}.pgrb2_0p25.tar
        GFS_FILENAME=./gfs.t${HH}z.pgrb2.0p25.f${FHHH_same}

elif ((${CYCLE} < ${GFS_CHANGE_DATE1})) ; then
        GFS_ARCHIVE=/NCEPPROD/hpssprod/runhistory/rh${YYYY}/${YYYYMM}/${YYYYMMDD}/com2_gfs_prod_gfs.${CYCLE}.pgrb2_0p25.tar
        GFS_FILENAME=./gfs.t${HH}z.pgrb2.0p25.f${FHHH_same}
fi

#-----------------------------------------------------------------------------------------
# Creating a job to download data on a particular ops GFS forecast cycle (CYCLE)
#-----------------------------------------------------------------------------------------

cat > ${DATA_PATH}/untar_fcsts/untar_gfs/gfs.${YYYYMMDD}/${HH}/htar_gfs_fcst_wave.sh <<EOF
#!/bin/bash
#PBS -N gfs_htar
#PBS -o ${OUTPUT_PATH}/out_htar_gfs_fcst_wave_${YYYYMMDD}_${HH}.out
#PBS -e ${OUTPUT_PATH}/out_htar_gfs_fcst_wave_${YYYYMMDD}_${HH}.err
#PBS -l select=1:ncpus=1:mem=4GB
#PBS -q dev_transfer
#PBS -l walltime=02:00:00
#PBS -A VERF-DEV

cd ${DATA_PATH}/untar_fcsts/untar_gfs/gfs.${YYYYMMDD}/${HH}

file="${DATA_PATH}/${CASE}_fhrs.txt"

while IFS= read -r line ; do
        #echo "Reading the next line of "${file}
        export FHHH=${FHHH_temp}

	if [[ -s ${DATA_PATH}/gfs.${YYYYMMDD}/${HH}/wave/gfswave.t${HH}z.global.0p25.f${FHHH_same}.grib2 ]] ; then
		echo ${CYCLE} "F"${FHHH_same}" GFS wave forecast already exists"
	else
        	echo "Extracting "${CYCLE}" ops GFS forecast file "${FHHH_same}
        	htar -xvf $GFS_ARCHIVE $GFS_FILENAME
        	sleep 3
        	mv $GFS_FILENAME ${DATA_PATH}/gfs.${YYYYMMDD}/${HH}/wave/gfswave.t${HH}z.global.0p25.f${FHHH_same}.grib2
	fi

done < ${file}
        
exit

EOF

#-----------------------------------------------------------------------

qsub ${DATA_PATH}/untar_fcsts/untar_gfs/gfs.${YYYYMMDD}/${HH}/htar_gfs_fcst_wave.sh
sleep 3

#----------------------------------------------------------------------------------------

exit
