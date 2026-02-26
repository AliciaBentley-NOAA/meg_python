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
mkdir -p ${DATA_PATH}/untar_analyses/untar_gfs

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

mkdir -p ${DATA_PATH}/untar_analyses/untar_gfs/gfs.${VYYYYMMDD}/${VHH}
mkdir -p ${DATA_PATH}/gfs.${VYYYYMMDD}/${VHH}/atmos
#echo ${DATA_PATH}/gfs.${VYYYYMMDD}/${VHH}/atmos

export GFS_CHANGE_DATE6=2022112900
export GFS_CHANGE_DATE5=2022062700	
export GFS_CHANGE_DATE4=2021031812
export GFS_CHANGE_DATE3=2020022600
export GFS_CHANGE_DATE2=2019061200
export GFS_CHANGE_DATE1=2017072000
export GFS_CHANGE_DATE0=2016051000

if ((${VALID} >= ${GFS_CHANGE_DATE6})) ; then
	GFS_ARCHIVE=/NCEPPROD/hpssprod/runhistory/rh${VYYYY}/${VYYYYMM}/${VYYYYMMDD}/com_gfs_v16.3_gfs.${VYYYYMMDD}_${VHH}.gfs_pgrb2.tar
	GFS_FILENAME=./gfs.${VYYYYMMDD}/${VHH}/atmos/gfs.t${VHH}z.pgrb2.1p00.anl

elif (((${VALID} >= ${GFS_CHANGE_DATE5}) && (${VALID} < ${GFS_CHANGE_DATE6}))) ; then
	GFS_ARCHIVE=/NCEPPROD/hpssprod/runhistory/rh${VYYYY}/${VYYYYMM}/${VYYYYMMDD}/com_gfs_v16.2_gfs.${VYYYYMMDD}_${VHH}.gfs_pgrb2.tar
	GFS_FILENAME=./gfs.${VYYYYMMDD}/${VHH}/atmos/gfs.t${VHH}z.pgrb2.1p00.anl

elif (((${VALID} >= ${GFS_CHANGE_DATE4}) && (${VALID} < ${GFS_CHANGE_DATE5}))) ; then
	GFS_ARCHIVE=/NCEPPROD/hpssprod/runhistory/rh${VYYYY}/${VYYYYMM}/${VYYYYMMDD}/com_gfs_prod_gfs.${VYYYYMMDD}_${VHH}.gfs_pgrb2.tar
        GFS_FILENAME=./gfs.${VYYYYMMDD}/${VHH}/atmos/gfs.t${VHH}z.pgrb2.1p00.anl

elif (((${VALID} >= ${GFS_CHANGE_DATE3}) && (${VALID} < ${GFS_CHANGE_DATE4}))) ; then
	GFS_ARCHIVE=/NCEPPROD/hpssprod/runhistory/rh${VYYYY}/${VYYYYMM}/${VYYYYMMDD}/com_gfs_prod_gfs.${VYYYYMMDD}_${VHH}.gfs_pgrb2.tar
        GFS_FILENAME=./gfs.${VYYYYMMDD}/${VHH}/gfs.t${VHH}z.pgrb2.1p00.f000

elif (((${VALID} >= ${GFS_CHANGE_DATE2}) && (${VALID} < ${GFS_CHANGE_DATE3}))) ; then
	GFS_ARCHIVE=/NCEPPROD/hpssprod/runhistory/rh${VYYYY}/${VYYYYMM}/${VYYYYMMDD}/gpfs_dell1_nco_ops_com_gfs_prod_gfs.${VYYYYMMDD}_${VHH}.gfs_pgrb2.tar
        GFS_FILENAME=./gfs.${VYYYYMMDD}/${VHH}/gfs.t${VHH}z.pgrb2.1p00.f000

elif (((${VALID} >= ${GFS_CHANGE_DATE1}) && (${VALID} < ${GFS_CHANGE_DATE2}))) ; then
	GFS_ARCHIVE=/NCEPPROD/hpssprod/runhistory/rh${VYYYY}/${VYYYYMM}/${VYYYYMMDD}/gpfs_hps_nco_ops_com_gfs_prod_gfs.${VALID}.pgrb2_1p00.tar
        GFS_FILENAME=./gfs.t${VHH}z.pgrb2.1p00.anl

elif (((${VALID} >= ${GFS_CHANGE_DATE0}) && (${VALID} < ${GFS_CHANGE_DATE1}))) ; then
        GFS_ARCHIVE=/NCEPPROD/hpssprod/runhistory/rh${VYYYY}/${VYYYYMM}/${VYYYYMMDD}/com2_gfs_prod_gfs.${VALID}.pgrb2_1p00.tar
	GFS_FILENAME=./gfs.t${VHH}z.pgrb2.1p00.anl               

elif ((${VALID} < ${GFS_CHANGE_DATE0})) ; then
	GFS_ARCHIVE=/NCEPPROD/hpssprod/runhistory/rh${VYYYY}/${VYYYYMM}/${VYYYYMMDD}/com_gfs_prod_gfs.${VALID}.pgrb2_0p25.tar
	GFS_FILENAME=./gfs.t${VHH}z.pgrb2.0p25.anl

fi

#echo $GFS_ARCHIVE
#echo $GFS_FILENAME


#-----------------------------------------------------------------------------------------
# Creating a job to download data on a particular valid date (VALID)
#-----------------------------------------------------------------------------------------

cat > ${DATA_PATH}/untar_analyses/untar_gfs/gfs.${VYYYYMMDD}/${VHH}/htar_gfs_anl_${VALID}.sh <<EOF
#!/bin/bash
#PBS -N gfs_htar
#PBS -o ${OUTPUT_PATH}/out_htar_gfs_anl_${VALID}.out
#PBS -e ${OUTPUT_PATH}/out_htar_gfs_anl_${VALID}.err
#PBS -l select=1:ncpus=1:mem=4GB
#PBS -q dev_transfer
#PBS -l walltime=02:00:00
#PBS -A VERF-DEV

cd ${DATA_PATH}/untar_analyses/untar_gfs/gfs.${VYYYYMMDD}/${VHH}

if [[ -s ${DATA_PATH}/gfs.${VYYYYMMDD}/${VHH}/atmos/gfs.t${VHH}z.pgrb2.1p00.anl ]] ; then
	echo ${VALID}" GFS analysis already exists"
else
	echo "Extracting "${VALID}" GFS analysis"
	htar -xvf $GFS_ARCHIVE $GFS_FILENAME
	sleep 3
	if test ${GFS_FILENAME} = "./gfs.t${VHH}z.pgrb2.0p25.anl" ; then
		echo ${VALID}" GFS analysis file is only avaiable in 0p25"
		mv ${GFS_FILENAME} ${DATA_PATH}/gfs.${VYYYYMMDD}/${VHH}/atmos/gfs.t${VHH}z.pgrb2.0p25.anl
	else
                echo ${VALID}" GFS analysis file is avaiable in 1p00"
		mv ${GFS_FILENAME} ${DATA_PATH}/gfs.${VYYYYMMDD}/${VHH}/atmos/gfs.t${VHH}z.pgrb2.1p00.anl
	fi
fi

exit

EOF

#-----------------------------------------------------------------------

qsub ${DATA_PATH}/untar_analyses/untar_gfs/gfs.${VYYYYMMDD}/${VHH}/htar_gfs_anl_${VALID}.sh
sleep 3

done < ${file}

exit

