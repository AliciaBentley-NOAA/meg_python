# Author: A Bentley
#
# Create adeck files from AIGEFS p2.1 dev files on Ursa (moved to WCOSS2)
#
# Run as:
# python create_adeck_aigefsdev_members.py $MODEL $TC_name/ID/YYYY
# python create_adeck_aigefsdev_members.py AIGEFSDEV MelissaAL132025


import numpy as np
import datetime, os, sys, subprocess
from datetime import datetime, timedelta
import re, csv


# Determine desired model
try:
   model_str = str(sys.argv[1])
except IndexError:
   model_str = None

if model_str is None:
   print('Model string options: GFS (AVNO or GFS), EC (EC, ECMWF, or EMX), UK (UK, UKMet, EGRR, or UKX), CMC, HWRF, HMON, NAM')
   print('Model string options (early): AVNI, CMCI, HWFI, HMNI')
   print('Model string options (ensemble mean): GEFSMean, ECENSmean')
   model_str = input('Enter desired model: ')


if str.upper(model_str) == 'GFS':
   model = 'AVNO'
elif str.upper(model_str) == 'RETR':
   model = 'RETR'
elif str.upper(model_str) == 'AIGFS':
   model = 'AGFS'
elif str.upper(model_str) == 'AIGEFSDEV':
   model = 'AVNO'
else:
   model = model_str


if (str.upper(model_str[0:2]) == 'UK' or str.upper(model_str) == 'EGRR') and str.upper(model_str) != 'UKX':
   wind_id = '0'
else:
   wind_id = '34'

# Get TC name and number
try:
   TC = str(sys.argv[2])
except IndexError:
   TC = None

if TC is None:
   print('Enter TC name, number, and year as one string')
   print('Example: FlorenceAL062018')
   TC = input('Enter TC name/number/year: ')

TC_name = TC[:-8]   #AL062018 is 8 characters
TC_number = TC[-8:-4]
TC_basin = TC[-8:-6]
TC_num = TC[-6:-4]
YYYY = TC[-4:]
print(TC_name, TC_number, TC_basin, TC_num, YYYY)

#----------------------------------------------------------------------

# Set path and create data directory (if not already created)
DIR = os.getcwd()

ADECK_DIR = '/lfs/h2/emc/vpppg/noscrub/alicia.bentley/aigefsdev_ursa'

# Define start and end points
# Format: Year, Month, Day, Hour (Cycle)
start_date = datetime(2025, 10, 19, 0)
end_date = datetime(2025, 10, 21, 0)
current_date = start_date

DATA_DIR = os.path.join('/lfs/h2/emc/vpppg/noscrub',os.environ['USER'],'adecks_aigefsdev')

if not os.path.exists(DATA_DIR):
      os.makedirs(DATA_DIR)

cycles=[]
fhrs=[]
lats=[]
lons=[]
vmax=[]
pres=[]
rmw=[]


#This is where I need to loop through mem### directories as well
for m in range(31):
    mem_str = f"mem{m:03d}"
    print(f"mem_str: {mem_str}")

    # Open the *output* file outside the date loop
    with open(DATA_DIR+'/a'+str.lower(TC_number)+YYYY+'_'+mem_str+'.dat', 'w', newline='') as f_out:
        writer = csv.writer(f_out)

        while current_date <= end_date:
            # 1. Format the date into the YYYYMMDDCC string
            # %Y = Year, %m = Month, %d = Day, %H = Hour (Cycle)
            date_str = current_date.strftime("%Y%m%d%H")
            YYYYMMDD = current_date.strftime("%Y%m%d")
    
            # 2. Construct the filename to read in
            filename = f'a'+str.lower(TC_number)+YYYY+'.dat'

            # 3. Perform your logic (e.g., opening the file)
            print(f"Processing: {filename}")

            with open(ADECK_DIR+'/aigfs.'+YYYYMMDD+'/00/ens_tracker/'+mem_str+'/atcf/'+str.lower(TC_number)+YYYY+'/'+filename,'r') as f_in:
                    reader = csv.reader(f_in, skipinitialspace=True)
                    for line in f_in:
                        # Check for Basin (AL) and Storm Number (09)
                        if line.startswith(f"{TC_basin}, {TC_num},"):
                            # 1. Split the line into a list based on your specific separator
                            parts = line.strip().split(', ')
                
                            # 2. Modify the 6th column (index 5)
                            # int("006") becomes 6, then we turn it back to a string
                            parts[5] = str(int(parts[5]))
                
                            # 3. Join them back together with ', ' and add the newline back
                            new_line = ', '.join(parts) + '\n'
                
                            # 4. Write the modified line
                            f_out.write(new_line)

            current_date += timedelta(hours=24)
            print(current_date)

    current_date = start_date

print(f"Done! Created "+DATA_DIR+"/a"+str.lower(TC_number)+YYYY+"_"+mem_str+".dat")
