#!/usr/bin/env python

import numpy as np
import datetime as dt
import time, os, sys, subprocess
from datetime import datetime, timedelta

DIR = os.getcwd()

cycle = str(sys.argv[1])
fhrb = int(sys.argv[2])
fhre = int(sys.argv[3])
step = int(sys.argv[4])
case = str(sys.argv[5])
fhrs = np.arange(fhrb,int(fhre+step),step)

f = open(DIR+'/'+case+'_fhrs.txt',"w+")

for k in range(len(fhrs)):
    if (fhrs[k] < 10):
        numzeros = str("00")
    elif ((fhrs[k] >= 10) and (fhrs[k] < 100)):
        numzeros = str("0")
    elif (fhrs[k] >= 100):
        numzeros = str("")

#    print(numzeros+str(fhrs[k]))
    f.write(numzeros+str(fhrs[k])+"\n")

f.close()
