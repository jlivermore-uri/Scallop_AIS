#!/usr/bin/env python
# coding: utf-8

# In[1]:


import numpy as np
import os, random
import pandas as pd
import matplotlib.pyplot as plt
get_ipython().run_line_magic('matplotlib', 'inline')
import math
pd.set_option('display.max_rows',None)
pd.options.display.max_columns=100


# In[2]:


# Set up data paths
# AIS
AIS_path = os.path.join(
    os.path.expanduser('~'),'Dropbox','My PC (DESKTOP-3PRD0P2)','Documents','CEC_project','Data_CEC_Project','AIS','FV_only','No_St_Water_Bathy'
)

new_AIS_path = os.path.join(
    os.path.expanduser('~'),'Dropbox','My PC (DESKTOP-3PRD0P2)','Documents','CEC_project','Data_CEC_Project','AIS','FV_only','With_Dec_Code'
)

# VMS
VMS_path = os.path.join(
    os.path.expanduser('~'),'Dropbox','My PC (DESKTOP-3PRD0P2)','Documents','CEC_project','Data_CEC_Project','VMS','ST19-001'
)

# Load AIS_GARFO_MATCHED file
GARFO_path = os.path.join(
    os.path.expanduser('~'),'Dropbox','My PC (DESKTOP-3PRD0P2)','Documents','CEC_project','Data_CEC_Project'
)
GARFO_dat = pd.read_csv(os.path.join(GARFO_path,'AIS_GARFO_MATCHED_2015_2018.csv'))


# In[3]:


# Merge AIS data with AIS_GARFO_MATCHED_2015_2018.csv info to pull in vessel permit number
startnum = 0
totalFiles = 1375

for filename in os.listdir(AIS_path):
    if filename.endswith("_bathy_no_state.csv"):
        print(os.path.join(AIS_path, filename)) 
        loopDat = pd.read_csv(os.path.join(AIS_path, filename))
        yearMon = filename[4:11]
        yearMon2 = yearMon.replace('_','-')
        year = int(filename[4:8])
        
        # Merge AIS to GARFO file by MMSI (or call sign?)
        loopDat['Year'] = year
        aisGARFO = pd.merge(loopDat, GARFO_dat, how='inner', left_on=['MMSI','Year'], right_on=['MMSI','PERMIT YEAR'])
        
        # Then merge that file to VMS by permit number and simplified time
        # Need to develop another temporal lookup because multiple trips may occur in a VMS file (monthly files)
        filename2 = yearMon2 + '_wo_202126_file.csv'
        vms = pd.read_csv(os.path.join(VMS_path, filename2))
        vms_simp = vms[['permit', 'utc_Date', 'decl_code']]
        vms_simp['Dec'] = vms_simp['decl_code'].str.slice(stop=3)
        del vms_simp['decl_code']

        # Found that lots of people keep their VMS on while in port so difficult to parse start and end of a trip 
        # Instead creating a simplified column of times in both datasets and merging on that
        vms_simp['utc_Date'] = pd.to_datetime(vms_simp['utc_Date'], infer_datetime_format=True)
        aisGARFO['Datetime'] = pd.to_datetime(aisGARFO['Datetime'], infer_datetime_format=True)
        aisGARFO['datetime1min'] = aisGARFO['Datetime'].dt.floor('Min')
        aisGARFO['PERMIT'] = aisGARFO['PERMIT'].apply(str)
        
        # Need to do a left join pulling in VMS declaration code at minutes available and then use ffill to back fill between rows
        aisVMS = pd.merge(aisGARFO, vms_simp, how='left', left_on=['datetime1min','PERMIT'], right_on=['utc_Date','permit'])
        aisVMS = aisVMS.sort_values(['PERMIT', 'Datetime'], ascending= True)
        aisVMS[['permit','Dec']] = aisVMS[['permit','Dec']].fillna(method='ffill')
        aisVMS['PERMIT'] = aisVMS['PERMIT'].apply(str)
        aisVMS['permit'] = aisVMS['permit'].apply(str)
        aisVMS['Permit_check'] = (aisVMS['PERMIT']==aisVMS['permit'])
        aisVMS = aisVMS[(aisVMS['Permit_check'] == True)].copy(deep=True)
        
        # Clean up joint AIS-VMS file with permit number to only needed columns
        aisVMS_clean = aisVMS[['Datetime', 'MMSI' , 'VesselName', 'CallSign_x', 'Width', 'Length', 'SOG', 'COG', 'Depth_m', 
                         'LON', 'LAT', 'Year_x', 'PERMIT', 'Dec']]
        aisVMS_clean = aisVMS_clean.rename(columns={'CallSign_x':'Callsign', 'Year_x':'Year', 'PERMIT':'Permit', 'Dec':'Dec_code'})
        
        # Save date file
        newFilename = filename.replace('_bathy_no_state.csv','_w_dec.csv')
        out_path=os.path.join(new_AIS_path,newFilename)
        aisVMS_clean.to_csv(out_path)
        
        startnum = startnum + 1
        progress = (startnum/totalFiles)*100
        print('Progress: ', progress, '% complete')
        


# In[ ]:




