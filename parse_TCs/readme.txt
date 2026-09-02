#-------------------------------------------------
#######################################
To produce ops GFS or GEFS .csv files:
#######################################
1) cd /lfs/h2/emc/vpppg/save/alicia.bentley/meg_python/parse_TCs
2) python parse_adeck_nhc.py GFS LalaCP012026
3) python parse_adeck_nhc.py GEFS LalaCP012026

#-------------------------------------------------
###########################################
To produce ops AIGFS or AIGEFS .csv files:
###########################################
1) cd /lfs/h2/emc/vpppg/save/alicia.bentley/meg_python/parse_TCs
2) python create_adeck_ai.py AIGFS LalaCP012026
3) python create_adeck_ai.py AIGFS LalaCP932026 (TC number before it was named)
4) cd /lfs/h2/emc/vpppg/noscrub/alicia.bentley/adecks_ai
5) mv acp012026.dat acp012026.dat_partial
6) sed -i 's/CP, 93,/CP, 01,/g' acp932026.dat
7) cat acp932026.dat acp012026.dat_partial > acp012026.dat
8) cd /lfs/h2/emc/vpppg/save/alicia.bentley/meg_python/parse_TCs
9) python parse_adeck_ai.py AIGFS LalaCP012026
10) python parse_adeck_ai.py AIGEFS LalaCP012026

#-------------------------------------------------
###########################################
To produce ops AIGEFS prototype .csv files:
###########################################
1) cd /lfs/h2/emc/vpppg/save/alicia.bentley/meg_python/parse_TCs
2) python create_adeck_aigefsdev_members.py AIGEFSDEV MelissaAL132025
3) python create_adeck_aigefsdev_members.py AIGEFSDEV MelissaAL982025 (TC number before it was named)
Add some script here to create AIGEFSDEV mean file from individual member files (run on both AL13 and AL98)

cd /lfs/h2/emc/vpppg/noscrub/alicia.bentley/adecks_aigefsdev
mv aal132025.dat aal132025.dat_partial
sed -i 's/AL, 98,/AL, 13,/g' aal982025.dat
cat aal982025.dat aal132025.dat_partial > aal132025.dat
cd /lfs/h2/emc/vpppg/save/alicia.bentley/meg_python/parse_TCs
python parse_adeck_ai.py AIGFS LalaCP012026
python parse_adeck_ai.py AIGEFS LalaCP012026


#-------------------------------------------------
#############################
To produce GFSv17 .csv files:
#############################
1) cd /lfs/h2/emc/vpppg/save/alicia.bentley/meg_python/parse_TCs
2) python create_adeck_gfsv17.py RETR LalaCP012026
3) python create_adeck_gfsv17.py RETR LalaCP932026 (TC number before it was named)
4) cd /lfs/h2/emc/vpppg/noscrub/alicia.bentley/adecks_gfsv17
5) mv acp012026.dat acp012026.dat_partial
6) sed -i 's/CP, 93,/CP, 01,/g' acp932026.dat
7) cat acp932026.dat acp012026.dat_partial > acp012026.dat  
8) cd /lfs/h2/emc/vpppg/save/alicia.bentley/meg_python/parse_TCs
9) python parse_adeck_gfsv17.py RETR LalaCP012026

#-------------------------------------------------
##############################
To make plots using .csv files
##############################
1) cd /lfs/h2/emc/vpppg/save/alicia.bentley/meg_python/plot_maps/
2) vi drive_plot_maps.sh (change TC name and uncomment TC options)
3) ./drive_plot_maps.sh


