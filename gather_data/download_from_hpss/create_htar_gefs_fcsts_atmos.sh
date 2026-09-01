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

mkdir -p ${DATA_PATH}/untar_fcsts/untar_gefs/gefs.${YYYYMMDD}/${HH}
mkdir -p ${DATA_PATH}/gefs.${YYYYMMDD}/${HH}/atmos
#echo ${DATA_PATH}/gefs.${YYYYMMDD}/${HH}/atmos

export FHHH_temp='`echo $line`'
export FHHH_same='${FHHH}'

file="${DATA_PATH}/${CASE}_fhrs.txt"

#################################################################################################
#----------------------- Info. to download ops GEFS forecasts ------------------------------------
export GEFS_CHANGE_DATE6=2022112900
export GEFS_CHANGE_DATE5=2022062700
export GEFS_CHANGE_DATE4=2021031812
export GEFS_CHANGE_DATE3=2020022600
export GEFS_CHANGE_DATE2=2019061200
export GEFS_CHANGE_DATE1=2017072000
export GEFS_CHANGE_DATE0=2016051000

if ((${CYCLE} >= ${GEFS_CHANGE_DATE6})) ; then
        GEFS_ARCHIVE=/NCEPPROD/hpssprod/runhistory/5year/rh${YYYY}/${YYYYMM}/${YYYYMMDD}/com_gefs_v12.3_gefs.${YYYYMMDD}_${HH}.atmos_pgrb2sp25.tar
        GEFS_FILENAME=./atmos/pgrb2sp25/geavg.t${HH}z.pgrb2s.0p25.f${FHHH_same}

elif (((${CYCLE} >= ${GEFS_CHANGE_DATE5}) && (${CYCLE} < ${GEFS_CHANGE_DATE6}))) ; then
        GEFS_ARCHIVE=/NCEPPROD/hpssprod/runhistory/rh${YYYY}/${YYYYMM}/${YYYYMMDD}/com_gfs_v16.2_gfs.${YYYYMMDD}_${HH}.gfs_pgrb2.tar
        GEFS_FILENAME=./gfs.${YYYYMMDD}/${HH}/atmos/gfs.t${HH}z.pgrb2.0p25.f${FHHH_same}

elif (((${CYCLE} >= ${GEFS_CHANGE_DATE4}) && (${CYCLE} < ${GEFS_CHANGE_DATE5}))) ; then
        GEFS_ARCHIVE=/NCEPPROD/hpssprod/runhistory/rh${YYYY}/${YYYYMM}/${YYYYMMDD}/com_gfs_prod_gfs.${YYYYMMDD}_${HH}.gfs_pgrb2.tar
        GEFS_FILENAME=./gfs.${YYYYMMDD}/${HH}/atmos/gfs.t${HH}z.pgrb2.0p25.f${FHHH_same}

elif (((${CYCLE} >= ${GEFS_CHANGE_DATE3}) && (${CYCLE} < ${GEFS_CHANGE_DATE4}))) ; then
        GEFS_ARCHIVE=/NCEPPROD/hpssprod/runhistory/rh${YYYY}/${YYYYMM}/${YYYYMMDD}/com_gfs_prod_gfs.${YYYYMMDD}_${HH}.gfs_pgrb2.tar
        GEFS_FILENAME=./gfs.${YYYYMMDD}/${HH}/gfs.t${HH}z.pgrb2.0p25.f${FHHH_same}

elif (((${CYCLE} >= ${GEFS_CHANGE_DATE2}) && (${CYCLE} < ${GEFS_CHANGE_DATE3}))) ; then
        GEFS_ARCHIVE=/NCEPPROD/hpssprod/runhistory/rh${YYYY}/${YYYYMM}/${YYYYMMDD}/gpfs_dell1_nco_ops_com_gfs_prod_gfs.${YYYYMMDD}_${HH}.gfs_pgrb2.tar
        GEFS_FILENAME=./gfs.${YYYYMMDD}/${HH}/gfs.t${HH}z.pgrb2.0p25.f${FHHH_same}

elif (((${CYCLE} >= ${GEFS_CHANGE_DATE1}) && (${CYCLE} < ${GEFS_CHANGE_DATE2}))) ; then
        GEFS_ARCHIVE=/NCEPPROD/hpssprod/runhistory/rh${YYYY}/${YYYYMM}/${YYYYMMDD}/gpfs_hps_nco_ops_com_gfs_prod_gfs.${CYCLE}.pgrb2_0p25.tar
        GEFS_FILENAME=./gfs.t${HH}z.pgrb2.0p25.f${FHHH_same}

elif ((${CYCLE} < ${GEFS_CHANGE_DATE1})) ; then
        GEFS_ARCHIVE=/NCEPPROD/hpssprod/runhistory/rh${YYYY}/${YYYYMM}/${YYYYMMDD}/com2_gfs_prod_gfs.${CYCLE}.pgrb2_0p25.tar
        GEFS_FILENAME=./gfs.t${HH}z.pgrb2.0p25.f${FHHH_same}
fi

#-----------------------------------------------------------------------------------------
# Creating a job to download data on a particular ops GEFS forecast cycle (CYCLE)
#-----------------------------------------------------------------------------------------

cat > ${DATA_PATH}/untar_fcsts/untar_gefs/gefs.${YYYYMMDD}/${HH}/htar_gefs_fcst_atmos.sh <<EOF
#!/bin/bash
#PBS -N gefs_htar
#PBS -o ${OUTPUT_PATH}/out_htar_gefs_fcst_atmos_${YYYYMMDD}_${HH}.out
#PBS -e ${OUTPUT_PATH}/out_htar_gefs_fcst_atmos_${YYYYMMDD}_${HH}.err
#PBS -l select=1:ncpus=1:mem=4GB
#PBS -q dev_transfer
#PBS -l walltime=02:00:00
#PBS -A VERF-DEV

cd ${DATA_PATH}/untar_fcsts/untar_gefs/gefs.${YYYYMMDD}/${HH}

file="${DATA_PATH}/${CASE}_fhrs.txt"

while IFS= read -r line ; do
        #echo "Reading the next line of "${file}
        export FHHH=${FHHH_temp}

	if [[ -s ${DATA_PATH}/gefs.${YYYYMMDD}/${HH}/atmos/geavg.t${HH}z.pgrb2s.0p25.f${FHHH_same} ]] ; then
		echo ${CYCLE} "F"${FHHH_same}" GEFS hires forecast (geavg) already exists"
	else
        	echo "Extracting "${CYCLE}" ops GEFS hires forecast (geavg) file "${FHHH_same}
        	htar -xvf $GEFS_ARCHIVE $GEFS_FILENAME
        	sleep 3
        	mv $GEFS_FILENAME ${DATA_PATH}/gefs.${YYYYMMDD}/${HH}/atmos/geavg.t${HH}z.pgrb2s.0p25.f${FHHH_same}
	fi

done < ${file}
        
exit

EOF

#-----------------------------------------------------------------------

qsub ${DATA_PATH}/untar_fcsts/untar_gefs/gefs.${YYYYMMDD}/${HH}/htar_gefs_fcst_atmos.sh
sleep 3

#----------------------------------------------------------------------------------------

exit
