# Author: A Bentley
#
# Run as:
# python calc_aigefsdev_ensmean.py $MODEL $TC_name/ID
# python calc_aigefsdev_ensmean.py AIGEFSDEV MelissaAL132025
#
# ------------------------------------------------------------------

import numpy as np
import sys, os, subprocess
import re, csv
import pandas as pd
from datetime import datetime, timedelta

# Define date range: 2025-10-19 00:00 to 2025-10-31 00:00 (daily at 00 UTC)
start_date = datetime(2025, 10, 19, 0)
end_date = datetime(2025, 10, 31, 0)

# Determine desired model
try:
   model_str = str(sys.argv[1])
except IndexError:
   model_str = None

print(model_str)

if model_str is None:
   print('Model string options: AIGEFSDEV')
   model_str = input('Enter desired model: ')

if str.upper(model_str) == 'AIGEFSDEV':
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
   print('Example: MelissaAL132025')
   TC = input('Enter TC name/number/year: ')

TC_name = TC[:-8]   #AL062018 is 8 characters
TC_number = TC[-8:-4]
YYYY = TC[-4:]
print(TC_name, TC_number, YYYY)

DATA_PATH = f"/lfs/h2/emc/vpppg/noscrub/alicia.bentley/MEG/{TC_name}/data"

current_date = start_date
while current_date <= end_date:
    init_str = current_date.strftime("%Y%m%d%H")
    member_dfs = []
    
    # Loop over ensemble members mem000 to mem030
    for mem_id in range(31):
        mem_str = f"mem{mem_id:03d}"
        
        file_path = f"{DATA_PATH}/{str.lower(model_str)}/{str.lower(TC_name)}_{str.lower(model_str)}_{init_str}_{mem_str}.csv"
        
        if os.path.exists(file_path):
            df = pd.read_csv(
                file_path, 
                header=None, 
                names=["fhr", "valid_date", "lat", "lon", "mslp", "vmax"]
            )
            member_dfs.append(df)
        else:
            print(f"Warning: Missing file {file_path}")

    if member_dfs:
        # Combine all ensemble members
        combined_df = pd.concat(member_dfs)
        
        # Calculate ensemble mean for each forecast hour and valid date
        ensemble_mean = combined_df.groupby(["fhr", "valid_date"], as_index=False).mean()
        
        # Format floating-point precision
        ensemble_mean[["lat", "lon"]] = ensemble_mean[["lat", "lon"]].round(2)
        ensemble_mean[["mslp", "vmax"]] = ensemble_mean[["mslp", "vmax"]].round(1)
        
        # Output filename structure
        output_file = f"{DATA_PATH}/{str.lower(model_str)}/{str.lower(TC_name)}_{str.lower(model_str)}_{init_str}.csv"
        ensemble_mean.to_csv(output_file, index=False, header=False)
        print(f"Successfully generated {output_file}")
    
    current_date += timedelta(days=1)
