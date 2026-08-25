#-------------------------------------------------
##############################
To produce ops GFS .csv files:
##############################
1) cd /lfs/h2/emc/vpppg/save/alicia.bentley/meg_python/parse_TCs
2) python parse_adeck_nhc.py GFS LalaCP012026

#-------------------------------------------------
##############################
To produce ops AIGFS .csv files:
##############################
1) cd /lfs/h2/emc/vpppg/save/alicia.bentley/meg_python/parse_TCs
2) python create_adeck_ai.py AIGFS LalaCP012026 (DO NOT INCLUDE THE I)
3) python create_adeck_ai.py AIGFS LalaCP932026 (TC number before it was named)
4) cd /lfs/h2/emc/vpppg/noscrub/alicia.bentley/adecks_ai
5) mv acp012026.dat acp012026.dat_partial
6) sed -i 's/CP, 93,/CP, 01,/g' acp932026.dat
7) cat acp932026.dat acp012026.dat_partial > acp012026.dat
8) cd /lfs/h2/emc/vpppg/save/alicia.bentley/meg_python/parse_TCs
9) python parse_adeck_ai.py AGFS LalaCP012026

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


