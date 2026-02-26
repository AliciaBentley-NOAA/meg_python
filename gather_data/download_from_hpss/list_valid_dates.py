#!/usr/bin/env python

import numpy as np
import datetime as dt
import time, os, sys, subprocess
from datetime import datetime, timedelta

DIR = os.getcwd()

cycle = str(sys.argv[1])
YYYY = int(cycle[0:4])
MM   = int(cycle[4:6])
DD   = int(cycle[6:8])
HH   = int(cycle[8:10])
date_str = datetime(YYYY,MM,DD,HH)
#print(date_str)

fhrb = int(sys.argv[2])
fhre = int(sys.argv[3])
step = int(sys.argv[4])
case = str(sys.argv[5])
fhrs = np.arange(fhrb,int((fhre)+(step*2)),step)

valid_list = [date_str + dt.timedelta(hours = int(x)) for x in fhrs]

f = open(DIR+'/'+case+'_valid_dates.txt',"w+")

for k in range(len(valid_list)):
       f.write(valid_list[k].strftime("%Y%m%d%H")+" \n")

f.close()
