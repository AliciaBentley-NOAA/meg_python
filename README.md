# meg_python
This repository contains NOAA/NWS/OMD Model Evaluation Group (MEG) scripts that can be used on WCOSS2. The majority of this repository is written in python, with some additional shell scripts.
#=====================================================

This repository can be separated into three sub-directories: 1) gather_data, 2) parse_TCs, and 3) plot_maps.

gather_data: Scripts used to copy forecast and analysis files from com/, dcom/, aws, and HPSS. 

parse_TCs: Scripts used to parse a-deck files into .csv files that can be plotted on a map, Vmax trace, etc.

plot_maps: Scripts used to plot parameters (e.g., PRMSL) from global models (e.g., GFS, AIGEFS, ECMWF)   
