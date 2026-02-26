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
mkdir -p ${DATA_PATH}/untar_analyses/untar_gdas

export YYYY=`echo $CYCLE | cut -c 1-4`
export YYYYMM=`echo $CYCLE | cut -c 1-6`
export YYYYMMDD=`echo $CYCLE | cut -c 1-8`
export HH=`echo $CYCLE | cut -c 9-10`

file="${DATA_PATH}/${CASE}_valid_dates.txt"
#lines=`cat ${file}`
#echo ${file}

while IFS= read -r line; do
        echo "Reading the next line of "${file}
	export VALID="`echo $line`"
        echo $VALID
	export VYYYY=`echo ${VALID} | cut -c 1-4`
	export VYYYYMM=`echo ${VALID} | cut -c 1-6`
	export VYYYYMMDD=`echo ${VALID} | cut -c 1-8`
	export VHH=`echo ${VALID} | cut -c 9-10`

mkdir -p ${DATA_PATH}/untar_analyses/untar_gdas/gdas.${VYYYYMMDD}/${VHH}
mkdir -p ${DATA_PATH}/gdas.${VYYYYMMDD}/${VHH}/atmos
#echo ${DATA_PATH}/gdas.${VYYYYMMDD}/${VHH}/atmos

export GDAS_CHANGE_DATE5=2022112900	
export GDAS_CHANGE_DATE4=2022062700
export GDAS_CHANGE_DATE3=2020022600
export GDAS_CHANGE_DATE2=2019061200
export GDAS_CHANGE_DATE1=2017072000
export GDAS_CHANGE_DATE0=2016051000

if ((${VALID} >= ${GDAS_CHANGE_DATE5})) ; then
	GDAS_ARCHIVE=/NCEPPROD/hpssprod/runhistory/rh${VYYYY}/${VYYYYMM}/${VYYYYMMDD}/com_obsproc_v1.1_gdas.${VYYYYMMDD}_${VHH}.obsproc_gdas.tar
	GDAS_FILENAME=./gdas.${VYYYYMMDD}/${VHH}/atmos/gdas.t${VHH}z.prepbufr

elif (((${VALID} >= ${GDAS_CHANGE_DATE4}) && (${VALID} < ${GDAS_CHANGE_DATE5}))) ; then
        GDAS_ARCHIVE=/NCEPPROD/hpssprod/runhistory/rh${VYYYY}/${VYYYYMM}/${VYYYYMMDD}/com_obsproc_v1.0_gdas.${VYYYYMMDD}_${VHH}.obsproc_gdas.tar
	GDAS_FILENAME=./gdas.${VYYYYMMDD}/${VHH}/atmos/gdas.t${VHH}z.prepbufr

elif (((${VALID} >= ${GDAS_CHANGE_DATE3}) && (${VALID} < ${GDAS_CHANGE_DATE4}))) ; then
        GDAS_ARCHIVE=/NCEPPROD/hpssprod/runhistory/rh${VYYYY}/${VYYYYMM}/${VYYYYMMDD}/com_gfs_prod_gdas.${VYYYYMMDD}_${VHH}.gdas.tar
	GDAS_FILENAME=./gdas.${VYYYYMMDD}/${VHH}/atmos/gdas.t${VHH}z.prepbufr

elif (((${VALID} >= ${GDAS_CHANGE_DATE2}) && (${VALID} < ${GDAS_CHANGE_DATE3}))) ; then
	GDAS_ARCHIVE=/NCEPPROD/hpssprod/runhistory/rh${VYYYY}/${VYYYYMM}/${VYYYYMMDD}/gpfs_dell1_nco_ops_com_gfs_prod_gdas.${VYYYYMMDD}_${VHH}.gdas.tar
        GDAS_FILENAME=./gdas.${VYYYYMMDD}/${VHH}/gdas.t${VHH}z.prepbufr

elif (((${VALID} >= ${GDAS_CHANGE_DATE1}) && (${VALID} < ${GDAS_CHANGE_DATE2}))) ; then
	GDAS_ARCHIVE=/NCEPPROD/hpssprod/runhistory/rh${VYYYY}/${VYYYYMM}/${VYYYYMMDD}/gpfs_hps_nco_ops_com_gfs_prod_gdas.${VALID}.tar
        GDAS_FILENAME=./gdas.t${VHH}z.prepbufr

elif (((${VALID} >= ${GDAS_CHANGE_DATE0}) && (${VALID} < ${GDAS_CHANGE_DATE1}))) ; then
	GDAS_ARCHIVE=/NCEPPROD/hpssprod/runhistory/rh${VYYYY}/${VYYYYMM}/${VYYYYMMDD}/com2_gfs_prod_gdas.${VALID}.tar
	GDAS_FILENAME=./gdas1.t${VHH}z.prepbufr

elif ((${VALID} < ${GDAS_CHANGE_DATE0})) ; then
	GDAS_ARCHIVE=/NCEPPROD/hpssprod/runhistory/rh${VYYYY}/${VYYYYMM}/${VYYYYMMDD}/com_gfs_prod_gdas.${VALID}.tar
	GDAS_FILENAME=./gdas1.t${VHH}z.prepbufr

fi

echo $GDAS_ARCHIVE
echo $GDAS_FILENAME


#-----------------------------------------------------------------------------------------
# Creating a job to download data on a particular valid date (VALID)
#-----------------------------------------------------------------------------------------

cat > ${DATA_PATH}/untar_analyses/untar_gdas/gdas.${VYYYYMMDD}/${VHH}/htar_gdas_anl_${VALID}.sh <<EOF
#!/bin/bash
#PBS -N gdas_htar
#PBS -o ${OUTPUT_PATH}/out_htar_gdas_anl_${VALID}.out
#PBS -e ${OUTPUT_PATH}/out_htar_gdas_anl_${VALID}.err
#PBS -l select=1:ncpus=1:mem=4GB
#PBS -q dev_transfer
#PBS -l walltime=02:00:00
#PBS -A VERF-DEV

cd ${DATA_PATH}/untar_analyses/untar_gdas/gdas.${VYYYYMMDD}/${VHH}

if [[ -s ${DATA_PATH}//gdas.${VYYYYMMDD}/${VHH}/atmos/gdas.t${VHH}z.prepbufr ]] ; then
	echo ${VALID}" GDAS analysis already exists"
else
	echo "Extracting "${VALID}" GDAS analysis"
	htar -xvf $GDAS_ARCHIVE $GDAS_FILENAME
	sleep 3
	cp ${GDAS_FILENAME} ${DATA_PATH}/gdas.${VYYYYMMDD}/${VHH}/atmos/gdas.t${VHH}z.prepbufr
fi

exit

EOF

#-----------------------------------------------------------------------

qsub ${DATA_PATH}/untar_analyses/untar_gdas/gdas.${VYYYYMMDD}/${VHH}/htar_gdas_anl_${VALID}.sh
sleep 3

done < ${file}

exit

