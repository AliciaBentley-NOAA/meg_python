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
mkdir -p ${DATA_PATH}/untar_analyses/untar_ccpa

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

mkdir -p ${DATA_PATH}/untar_analyses/untar_ccpa/ccpa.${VYYYYMMDD}/${VHH}
mkdir -p ${DATA_PATH}/ccpa.${VYYYYMMDD}/${VHH}
#echo ${DATA_PATH}/ccpa.${VYYYYMMDD}/${VHH}

export CCPA_CHANGE_DATE4=2022062000	
export CCPA_CHANGE_DATE3=2020021800
export CCPA_CHANGE_DATE2=2019081200
export CCPA_CHANGE_DATE1=2016032000

if ((${VALID} >= ${CCPA_CHANGE_DATE4})) ; then
	CCPA_ARCHIVE=/NCEPPROD/hpssprod/runhistory/rh${VYYYY}/${VYYYYMM}/${VYYYYMMDD}/com_ccpa_v4.2_ccpa.${VYYYYMMDD}.tar
	CCPA_FILENAME=./${VHH}/ccpa.t${VHH}z.06h.1p0.conus.gb2

elif (((${VALID} >= ${CCPA_CHANGE_DATE3}) && (${VALID} < ${CCPA_CHANGE_DATE4}))) ; then
        CCPA_ARCHIVE=/NCEPPROD/hpssprod/runhistory/rh${VYYYY}/${VYYYYMM}/${VYYYYMMDD}/com_ccpa_prod_ccpa.${VYYYYMMDD}.tar
	CCPA_FILENAME=./${VHH}/ccpa.t${VHH}z.06h.1p0.conus.gb2

elif (((${VALID} >= ${CCPA_CHANGE_DATE2}) && (${VALID} < ${CCPA_CHANGE_DATE3}))) ; then
	CCPA_ARCHIVE=/NCEPPROD/hpssprod/runhistory/rh${VYYYY}/${VYYYYMM}/${VYYYYMMDD}/gpfs_dell1_nco_ops_com_ccpa_prod_ccpa.${VYYYYMMDD}.tar 
        CCPA_FILENAME=./${VHH}/ccpa.t${VHH}z.06h.1p0.conus.gb2

elif (((${VALID} >= ${CCPA_CHANGE_DATE1}) && (${VALID} < ${CCPA_CHANGE_DATE2}))) ; then
	CCPA_ARCHIVE=/NCEPPROD/hpssprod/runhistory/rh${VYYYY}/${VYYYYMM}/${VYYYYMMDD}/com2_ccpa_prod_ccpa.${VYYYYMMDD}.tar
        CCPA_FILENAME=./${VHH}/ccpa.t${VHH}z.06h.1p0.conus.gb2

elif ((${VALID} < ${CCPA_CHANGE_DATE1})) ; then
	CCPA_ARCHIVE=/NCEPPROD/hpssprod/runhistory/rh${VYYYY}/${VYYYYMM}/${VYYYYMMDD}/com_gens_prod_gefs.${VYYYYMMDD}_${VHH}.ccpa.tar
        CCPA_FILENAME=./ccpa/ccpa_conus_1.0d_t${VHH}z_06h_gb2

fi

#echo $CCPA_ARCHIVE
#echo $CCPA_FILENAME


#-----------------------------------------------------------------------------------------
# Creating a job to download data on a particular valid date (VALID)
#-----------------------------------------------------------------------------------------

cat > ${DATA_PATH}/untar_analyses/untar_ccpa/ccpa.${VYYYYMMDD}/${VHH}/htar_ccpa_anl_${VALID}.sh <<EOF
#!/bin/bash
#PBS -N ccpa_htar
#PBS -o ${OUTPUT_PATH}/out_htar_ccpa_anl_${VALID}.out
#PBS -e ${OUTPUT_PATH}/out_htar_ccpa_anl_${VALID}.err
#PBS -l select=1:ncpus=1:mem=4GB
#PBS -q dev_transfer
#PBS -l walltime=02:00:00
#PBS -A VERF-DEV

cd ${DATA_PATH}/untar_analyses/untar_ccpa/ccpa.${VYYYYMMDD}/${VHH}

if [[ -s ${DATA_PATH}/ccpa.${VYYYYMMDD}/${VHH}/ccpa.t${VHH}z.06h.1p0.conus.gb2 ]] ; then
	echo ${VALID}" CCPA analysis already exists"
else
	echo "Extracting "${VALID}" CCPA analysis"
	htar -xvf $CCPA_ARCHIVE $CCPA_FILENAME
	sleep 3
	mv ${CCPA_FILENAME} ${DATA_PATH}/ccpa.${VYYYYMMDD}/${VHH}/ccpa.t${VHH}z.06h.1p0.conus.gb2
fi

exit

EOF

#-----------------------------------------------------------------------

qsub ${DATA_PATH}/untar_analyses/untar_ccpa/ccpa.${VYYYYMMDD}/${VHH}/htar_ccpa_anl_${VALID}.sh
sleep 3

done < ${file}

exit

