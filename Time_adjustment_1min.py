#!/usr/bin/env python
# coding: utf-8

# In[1]:


# Resample data to 1 minute intervals - linear interpolation between points
# Downsample to 1 sec and then pull out 1 min intervals
# This will correct variance in time


# In[2]:


# Testing model configurations with training data
import numpy as np
import os, random
import pandas as pd
import matplotlib.pyplot as plt
get_ipython().run_line_magic('matplotlib', 'inline')
import math
pd.set_option('display.max_rows',None)


# In[3]:


# Load all tables
data_path = os.path.join(
    os.path.expanduser('~'),'Dropbox','My PC (DESKTOP-3PRD0P2)','Documents','CEC_project','Data_CEC_Project','Training_Data'
)


# In[4]:


# Create function to calculate change in COG in case it passes through 0 between points - ENDED UP NOT USING THIS
def cogCalc(startCOG,endCOG):
    change = abs(endCOG-startCOG)
    change2 = 360 - change
    minChange = min(change,change2)
    return minChange


# In[6]:


for filename in os.listdir(data_path):
    if filename.endswith("_bathy_no_state.csv"):
        print(os.path.join(data_path, filename))        
        loopDat0=pd.read_csv(os.path.join(data_path, filename))
        loopDat0=loopDat0.rename(columns={'GEAR.NAME': 'GEAR'})
        
        mmsi=loopDat0['MMSI'].values[0]
        callsign=loopDat0['CallSign'].values[0]
        hullnum=loopDat0['HULLNUM'].values[0]
        permit=loopDat0['PERMIT'].values[0]
        gear=loopDat0['GEAR'].values[0]
        tripid=loopDat0['TRIP_ID'].values[0]
        deccode=loopDat0['Declaration_code'].values[0]
        if isinstance(deccode,str):
            fmp=deccode[:3]
        else:
            fmp='NA'
        
        length=loopDat0['Length'].values[0]
        
        loopDat=loopDat0.drop_duplicates()
        loopDat=loopDat0.drop_duplicates('Datetime',keep='last')

        loopDat0['Datetime']=pd.to_datetime(loopDat0['Datetime'], infer_datetime_format=True)
        loopDat0.set_index('Datetime',inplace=True)

        if fmp=='DOF':
            gear=='TRAWL,OTTER,BOTTOM,FISH'
        
        loopDat = loopDat0[(loopDat0['GEAR'] == gear)].copy(deep=True)
        loopDat=loopDat[~loopDat.index.duplicated(keep='last')]
        
        # Upsample to one-second intervals (linear interpolation for SOG, depth, LAT and LON)
        one_min_dat = loopDat[['SOG','Depth_m','LON','LAT']].resample('1S').interpolate(method='linear')
        
#         one_min_dat=pd.DataFrame()
#         one_min_dat['SOG']=loopDat.SOG.resample('1S').interpolate(method='linear')
#         one_min_dat['Depth_m']=loopDat.Depth_m.resample('1S').interpolate(method='linear')
#         one_min_dat['LON']=loopDat.LON.resample('1S').interpolate(method='linear')
#         one_min_dat['LAT']=loopDat.LAT.resample('1S').interpolate(method='linear')
      
        # Upsample to one-second intervals on COG 
        one_min_dat['COG'] = loopDat.COG.resample('1S').ffill()        

        # Upsample to one-second intervals for fishing status
        one_min_dat['NEFOP_Fishing'] = loopDat.NEFOP_Fishing.resample('1S').ffill()
        
        # Keep only rows at minute marks
        one_min_dat = one_min_dat[one_min_dat.index.second == 0].copy(deep=True) 

        # Save other variables (non-changing)
        # Make a copy 
        one_min_dat['Trip_ID'] = tripid
        one_min_dat['GEAR'] = gear
        one_min_dat['Declaration_code'] = deccode
        one_min_dat['FMP'] = fmp
        one_min_dat['Length'] = length
        one_min_dat['PERMIT'] = permit
        one_min_dat['MMSI'] = mmsi
        one_min_dat['CallSign'] = callsign
        one_min_dat['HULLNUM'] = hullnum

        # Save trip file
        if gear == 'DREDGE, CLAM, HYDRAULIC':
            g = '_clam'
        elif gear == 'DREDGE, SCALLOP,SEA':
            g = '_scal'
        elif gear == 'GILL NET,DRIFT-SINK, FISH' or gear == 'GILL NET, FIXED OR ANCHORED,SINK, OTHER/NK SPECIES' or gear == 'GILL NET,DRIFT-FLOATING, FISH':
            g = '_gill'
        elif gear == 'TRAWL,OTTER,BOTTOM,FISH' or gear == 'TRAWL,OTTER,BOTTOM,HADDOCK SEPARATOR' or gear == 'TRAWL,OTTER,BOTTOM,SCALLOP' or gear == 'TRAWL,OTTER,BOTTOM,TWIN' or gear == 'TRAWL,OTTER,MIDWATER' or gear == 'TRAWL,OTTER,MIDWATER PAIRED':
            g = '_traw'
            
        out_path = os.path.join(data_path,filename[0:11] + '_1min' + g + '.csv')
        one_min_dat.to_csv(out_path)
        


# In[7]:


one_min_dat.head()


# In[ ]:




