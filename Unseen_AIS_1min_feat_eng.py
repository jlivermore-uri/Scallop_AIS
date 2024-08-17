#!/usr/bin/env python
# coding: utf-8

# In[1]:


# Prepping the AIS data for unseen vessels and unseen trips for seen vessels
import numpy as np
import os, random
import pandas as pd
import matplotlib.pyplot as plt
get_ipython().run_line_magic('matplotlib', 'inline')
import math
from geopy.distance import geodesic
from shapely.geometry import Point

pd.set_option('display.max_rows',None)
pd.options.display.max_columns=100


# In[2]:


in_path = os.path.join(
    os.path.expanduser('~'),'Dropbox','My PC (DESKTOP-3PRD0P2)','Documents','CEC_project','Data_CEC_Project','AIS','FV_only','With_Dec_Code'
)

out_path = os.path.join(
    os.path.expanduser('~'),'Dropbox','My PC (DESKTOP-3PRD0P2)','Documents','CEC_project','Data_CEC_Project','AIS','FV_only','Unseen'
)

moon_path = os.path.join(
    os.path.expanduser('~'),'Dropbox','My PC (DESKTOP-3PRD0P2)','Documents','CEC_project','Data_CEC_Project','Training_Data'
)

vtr_path = os.path.join(
    os.path.expanduser('~'),'Dropbox','My PC (DESKTOP-3PRD0P2)','Documents','CEC_project','Data_CEC_Project','VTR'
)


# Read in moon phase data
moon_dat = pd.read_csv(os.path.join(moon_path,'Moon_phase.csv'))
moon_dat['Date'] = pd.to_datetime(moon_dat['Date'],infer_datetime_format=True)
moon_dat['Date'] = moon_dat['Date'].astype(str)


# In[3]:


# Function for calculating distance that will take care of start and end points with NaN values
def robust_dist(lat1,lon1,lat2,lon2):
    if np.isnan([lat1,lon1,lat2,lon2]).any():
        return np.nan
    else:
        return geodesic((lon1,lat1,),(lon2,lat2)).km


# In[4]:


# Read in list of seen trips because we may have some boats with some observer coverage that needs to be excluded
# from the unseen dataset. Unseen dataset should be unseen boats and unseen trips on seen boats only. 
data_path = os.path.join(
    os.path.expanduser('~'),'Dropbox','My PC (DESKTOP-3PRD0P2)','Documents','CEC_project','Data_CEC_Project','Training_Data'
)
scal = pd.read_csv(os.path.join(data_path, 'all_scallop_trained.csv'))
trawl = pd.read_csv(os.path.join(data_path, 'all_trawl_trained.csv'))
clam = pd.read_csv(os.path.join(data_path, 'all_clam_trained.csv'))
gill = pd.read_csv(os.path.join(data_path, 'all_gill_trained.csv'))
scal = scal[['Datetime','PERMIT']]
gill = gill[['Datetime','PERMIT']]
trawl = trawl[['Datetime','PERMIT']]
clam = clam[['Datetime','PERMIT']]
allTrained = scal.append(gill, ignore_index = True)
allTrained = allTrained.append(clam, ignore_index = True)
allTrained = allTrained.append(trawl, ignore_index = True)
allTrained = allTrained.rename(columns={'PERMIT': 'Permit'})
checks = allTrained['Permit'].astype(str) + " " + allTrained['Datetime'].astype(str)    


# In[5]:


# Loop through all AIS files 

##############################################
# Recalibrate to 1 min increments
##############################################

for filename in os.listdir(in_path):
    if filename.endswith("w_dec.csv"):
        print(os.path.join(in_path, filename))        
        loopDat0=pd.read_csv(os.path.join(in_path, filename))
        
        # Need to split into individual trips
        loopDat0['Boat']=loopDat0['MMSI'].ne(loopDat0['MMSI'].shift()).cumsum()
        
        numBoats = len(pd.unique(loopDat0['Boat']))
        
        AIS_dfs=[]
        
        for i in range(1, numBoats):
            
            tripDat = loopDat0[(loopDat0['Boat'] == i)].copy(deep=True)

            # Save non-changing values
            mmsi=tripDat['MMSI'].values[0]
            callsign=tripDat['Callsign'].values[0]
            permit=tripDat['Permit'].values[0]
            deccode=tripDat['Dec_code'].values[0]
            length=tripDat['Length'].values[0]

            tripDat['Datetime']=pd.to_datetime(tripDat['Datetime'], infer_datetime_format=True)
            tripDat.set_index('Datetime',inplace=True)
            tripDat = tripDat.loc[~tripDat.index.duplicated(), :]

            # Upsample to one-second intervals (linear interpolation for SOG, depth, LAT and LON)
            one_min_dat = tripDat[['SOG','Depth_m','LON','LAT']].resample('1S').interpolate(method='linear')

            # Upsample to one-second intervals on COG 
            one_min_dat['COG'] = tripDat.COG.resample('1S').ffill()        

            # Keep only rows at minute marks
            one_min_dat = one_min_dat[one_min_dat.index.second == 0].copy(deep=True) 

            # Save other variables (non-changing)
            one_min_dat['Declaration_code'] = deccode
            one_min_dat['Length'] = length
            one_min_dat['Permit'] = permit
            one_min_dat['MMSI'] = mmsi
            one_min_dat['CallSign'] = callsign

            # Reset datetime to a column (assign new index)
            one_min_dat.reset_index(inplace=True)

            # Pull trip year to search correct VTR files in next step
            tripYear = filename[4:8]

            ##############################################
            # Pull in VTR to get the gear type
            ##############################################
            vtr_file = os.path.join(vtr_path,'VTR_' + str(tripYear) + '.csv')
            vtr = pd.read_csv(vtr_file)

            # Create new VTR number column because currently split across 2 columns (see cells below for confirmation)
            # Pull eVTR numbers (14 digits) from Supplier trip id column and paper VTR numbers (8 digits) from Serial num column
            #vtr['VTR_num'] = np.where(vtr['Serial num'] > 99999999, vtr['Supplier trip id'], vtr['Serial num'])
            # There are some rows with columns that the VTR number still has the wrong number of digits!!! May have to correct this issue
            # when merging with landings. 

            # Subset to the permit
            ves_vtr = vtr[(vtr['Fed ves permit'] == permit)].copy(deep=True)

            # Pull in columns (gear, lat and lon (for truth comparison later)
            ves_vtr['Start_date'] = ves_vtr['Start month'].astype(str) + '-' + ves_vtr['Start day'].astype(str) + '-' + ves_vtr['Start year'].astype(str)
            ves_vtr['Start_date'] = pd.to_datetime(ves_vtr['Start_date'], infer_datetime_format=True)
            ves_vtr['Date land'] = pd.to_datetime(ves_vtr['Date land'], infer_datetime_format=True)
#             ves_vtr['Lat sec'] = ves_vtr['Lat sec'].replace('-', '0')
#             ves_vtr['Lon sec'] = ves_vtr['Lon sec'].replace('-', '0')
#             ves_vtr['Lat min'] = ves_vtr['Lat min'].replace('-', '0')
#             ves_vtr['Lon min'] = ves_vtr['Lon min'].replace('-', '0')
#             ves_vtr['Latitude'] = ves_vtr['Latitude'].replace('-', '0')
#             ves_vtr['Longitude'] = ves_vtr['Longitude'].replace('-', '0')
#             ves_vtr['Lat_DD'] = ves_vtr['Latitude'].astype(float) + ves_vtr['Lat min'].astype(float)/60 + ves_vtr['Lat sec'].astype(float)/(60*60)
#             ves_vtr['Lon_DD'] = -1*(ves_vtr['Longitude'].astype(float) + ves_vtr['Lon min'].astype(float)/60 + ves_vtr['Lon sec'].astype(float)/(60*60))
            ves_vtr = ves_vtr[['Start_date','Date land','Gear name','State postal','Port name','Fed ves permit',
                               'Supplier cf id','Supplier dea id','Supplier trip id','Serial num']]
            ves_vtr = ves_vtr.rename(columns={'Start_date': 'VTR_Start_date', 'Date land': 'VTR_Land_date', 'Gear name': 'VTR_Gear', 
                                              'State postal': 'VTR_Land_st', 'Port name': 'VTR_Land_port', 'Fed ves permit': 'Permit', 
                                              'Supplier cf id': 'VTR_CF_id', 'Supplier dea id': 'VTR_Dealer_id'})

            # There are multiple rows per VTR now because there's a row per species
            ves_vtr['VTR_Gear'] = ves_vtr['VTR_Gear'].astype(str)
            ves_vtr['VTR_Land_st'] = ves_vtr['VTR_Land_st'].astype(str)
            ves_vtr['VTR_Land_port'] = ves_vtr['VTR_Land_port'].astype(str)
            ves_vtr['VTR_CF_id'] = ves_vtr['VTR_CF_id'].astype(str)
            ves_vtr = ves_vtr.drop_duplicates(keep='first', ignore_index=True)

            vtr_ais = pd.merge(one_min_dat, ves_vtr, how='inner', on='Permit')
            vtr_ais = vtr_ais[(vtr_ais['Datetime']>=vtr_ais['VTR_Start_date']) & (vtr_ais['Datetime']<=vtr_ais['VTR_Land_date'])]
            
            # Clean up the gear types to simplified forms in a new column
            ves_vtr['VTR_Gear'] = ves_vtr['VTR_Gear'].astype(str)
            ves_vtr['Gear'] = ves_vtr['VTR_Gear']
            ves_vtr['Gear'] = np.where((ves_vtr['VTR_Gear']=='OTTER TRAWL, BOTTOM,FISH'), 'trawl', ves_vtr['Gear'])   
            ves_vtr['Gear'] = np.where((ves_vtr['VTR_Gear']=='OTTER TRAWL, BOTTOM,SHRIMP'), 'trawl', ves_vtr['Gear'])   
            ves_vtr['Gear'] = np.where((ves_vtr['VTR_Gear']=='OTTER TRAWL, RUHLE'), 'trawl', ves_vtr['Gear'])   
            ves_vtr['Gear'] = np.where((ves_vtr['VTR_Gear']=='OTTER TRAWL, MIDWATER'), 'trawl', ves_vtr['Gear'])   
            ves_vtr['Gear'] = np.where((ves_vtr['VTR_Gear']=='GILL NET, SINK'), 'gillnet', ves_vtr['Gear'])   
            ves_vtr['Gear'] = np.where((ves_vtr['VTR_Gear']=='OTTER TRAWL, BOTTOM,OTHER'), 'trawl', ves_vtr['Gear'])   
            ves_vtr['Gear'] = np.where((ves_vtr['VTR_Gear']=='DREDGE, SCALLOP,SEA'), 'scallop', ves_vtr['Gear'])   
            ves_vtr['Gear'] = np.where((ves_vtr['VTR_Gear']=='GILL NET, RUNAROUND'), 'gillnet', ves_vtr['Gear'])   
            ves_vtr['Gear'] = np.where((ves_vtr['VTR_Gear']=='DREDGE, SCALLOP-CHAIN MAT'), 'scallop', ves_vtr['Gear'])   
            ves_vtr['Gear'] = np.where((ves_vtr['VTR_Gear']=='GILL NET, DRIFT,LARGE MESH'), 'gillnet', ves_vtr['Gear'])   
            ves_vtr['Gear'] = np.where((ves_vtr['VTR_Gear']=='DREDGE, OCEAN QUAHOG/SURF CLAM'), 'clam', ves_vtr['Gear'])   
            ves_vtr['Gear'] = np.where((ves_vtr['VTR_Gear']=='OTTER TRAWL, BEAM'), 'trawl', ves_vtr['Gear'])   
            ves_vtr['Gear'] = np.where((ves_vtr['VTR_Gear']=='OTTER TRAWL, BOTTOM,SCALLOP'), 'scallop', ves_vtr['Gear'])               
            ves_vtr['Gear'] = np.where((ves_vtr['VTR_Gear']=='PAIR TRAWL, MIDWATER'), 'trawl', ves_vtr['Gear'])   
            ves_vtr['Gear'] = np.where((ves_vtr['VTR_Gear']=='GILL NET, DRIFT,SMALL MESH'), 'gillnet', ves_vtr['Gear'])               
            ves_vtr['Gear'] = np.where((ves_vtr['VTR_Gear']=='GILL NET, OTHER'), 'gillnet', ves_vtr['Gear'])   
            ves_vtr['Gear'] = np.where((ves_vtr['VTR_Gear']=='DREDGE,SCALLOP,CHAIN MAT,MOD'), 'scallop', ves_vtr['Gear'])               
            ves_vtr['Gear'] = np.where((ves_vtr['VTR_Gear']=='PAIR TRAWL, BOTTOM'), 'trawl', ves_vtr['Gear'])               
            ves_vtr['Gear'] = np.where((ves_vtr['VTR_Gear']=='DREDGE,SCALLOP,TURTLE DEFLECT'), 'scallop', ves_vtr['Gear'])               
            
            # Merge still has multiples because some trips have more than one VTR - this shouldn't be an issue because when 
            # we merge to landings later on, all landings will only be accounted for once. They will merge to one VTR or the
            # other in cases where there are 2 VTR's per trip, but the location info is going to be the same.
            
            # Clean up VTRs more and merge to AIS
            ves_vtr = ves_vtr.drop_duplicates(subset=ves_vtr.columns.difference(['VTR_num']))
            ves_vtr['VTR_Land_st'] = ves_vtr['VTR_Land_st'].astype(str)
            ves_vtr['VTR_Land_port'] = ves_vtr['VTR_Land_port'].astype(str)
            ves_vtr['VTR_CF_id'] = ves_vtr['VTR_CF_id'].astype(str)
            ves_vtr = ves_vtr.drop_duplicates(keep='first', ignore_index=True)
            vtr_ais = pd.merge(one_min_dat, ves_vtr, how='inner', on='Permit')
            # Drop data where temporal mismatch occurs 
            vtr_ais = vtr_ais[(vtr_ais['Datetime']>=vtr_ais['VTR_Start_date']) & (vtr_ais['Datetime']<=vtr_ais['VTR_Land_date'])]
            
            # Sort by Permit, then by VTR # (or proxy/unique ID), then by datetime before running feature engineering steps
            vtr_ais.sort_values(by = ['Permit', 'Serial num', 'Datetime'], axis=0, inplace=True, kind='quicksort', ignore_index=True)
            
            if len(vtr_ais) >= 1:

                ##############################################
                # Then engineer all features (all window lengths should be odd numbers of points (with a midpoint))
                ##############################################
                window_points = 15 
                window_minutes = window_points - 1
                assert window_minutes % 2 == 0
                half_minutes = window_minutes // 2
                
                # Flag rows at the start of each new trip (can do by VTR number)
                vtr_ais['Prev_trip_num'] = vtr_ais['Serial num'].shift(1)
                vtr_ais['New_trip_check'] = np.where((vtr_ais['Prev_trip_num'] == vtr_ais['Serial num']), 0, 1)        
                
                # Make first values in a new trip NaNs so that rolling calculations are not including values from
                # the previous trip. The New_VTR_check column can be used for this purpose. 
                vtr_ais['SOG'] = np.where((vtr_ais['New_trip_check'] == 1), float('NaN'), vtr_ais['SOG'])  
                vtr_ais['COG'] = np.where((vtr_ais['New_trip_check'] == 1), float('NaN'), vtr_ais['COG'])  
                vtr_ais['Depth_m'] = np.where((vtr_ais['New_trip_check'] == 1), float('NaN'), vtr_ais['Depth_m'])  
                vtr_ais['LAT'] = np.where((vtr_ais['New_trip_check'] == 1), float('NaN'), vtr_ais['LAT'])  
                vtr_ais['LON'] = np.where((vtr_ais['New_trip_check'] == 1), float('NaN'), vtr_ais['LON'])  

                # Add columns for change in time, speed, and depth
                vtr_ais.reset_index(inplace=True)
                vtr_ais['Datetime'] = pd.to_datetime(vtr_ais['Datetime'], infer_datetime_format=True)
                vtr_ais['d_SOG'] = vtr_ais['SOG'] - vtr_ais['SOG'].shift(1)
                vtr_ais['d_Time'] = vtr_ais['Datetime'] - vtr_ais['Datetime'].shift(1)
                vtr_ais['d_Depth'] = vtr_ais['Depth_m'] - vtr_ais['Depth_m'].shift(1)

                # Average and SD of SOG
                vtr_ais['SOG_Avg'] = vtr_ais['SOG'].rolling(window=window_points, center=True, min_periods=1).mean()
                vtr_ais['SOG_Std'] = vtr_ais['SOG'].rolling(window=window_points, center=True, min_periods=1).std()

                # Average and SD of Depth
                vtr_ais['Depth_Avg'] = vtr_ais['Depth_m'].rolling(window=window_points, center=True, min_periods=1).mean()
                vtr_ais['Depth_Std'] = vtr_ais['Depth_m'].rolling(window=window_points, center=True, min_periods=1).std()

                # Distance between points
                vtr_ais['Prev_LAT'] = vtr_ais['LAT'].shift(1)
                vtr_ais['Prev_LON'] = vtr_ais['LON'].shift(1)
                vtr_ais['Start_LAT'] = vtr_ais['LAT'].shift(half_minutes)
                vtr_ais['Start_LON'] = vtr_ais['LON'].shift(half_minutes)
                vtr_ais['End_LAT'] = vtr_ais['LAT'].shift(-half_minutes)
                vtr_ais['End_LON'] = vtr_ais['LON'].shift(-half_minutes)
                vtr_ais['Km_bw_pts']= vtr_ais.apply(lambda x: robust_dist(x['Prev_LAT'], x['Prev_LON'], x['LAT'], x['LON']),axis=1)

                # Start-end distance (as crow flies)
                vtr_ais['Crow_flies_km']= vtr_ais.apply(lambda x: robust_dist(x['Start_LAT'], x['Start_LON'], x['End_LAT'], x['End_LON']),axis=1)

                vtr_ais = vtr_ais.drop(columns=['Prev_LAT', 'Prev_LON', 'Start_LAT', 'Start_LON', 'End_LAT', 
                                                'End_LON', 'Prev_trip_num'])

                # Total distance traveled
                vtr_ais['Total_km_trav'] = vtr_ais['Km_bw_pts'].rolling(window=window_points,center=True,min_periods=1).sum()

                # COG change column
                # Course over ground is 0 to 360, at due North we'll run into a 360 degree change potentially so we're calculating 2 
                # ways and using the minimum of the two
                vtr_ais['d_COG'] = abs(vtr_ais['COG'] - vtr_ais['COG'].shift(1))
                vtr_ais['d_COG'] = np.minimum(vtr_ais['d_COG'], 360 - vtr_ais['d_COG'])

                # Start-end COG change
                vtr_ais['d_COG_StartEnd'] = abs(vtr_ais['COG'].shift(half_minutes) - vtr_ais['COG'].shift(-half_minutes))
                vtr_ais['d_COG_StartEnd'] = np.minimum(vtr_ais['d_COG_StartEnd'], 360 - vtr_ais['d_COG_StartEnd'])

                # Mean COG change overall steps (this is actually absolute average deviation)
                vtr_ais['COG_Avg_Abs_d'] = vtr_ais['d_COG'].rolling(window=window_points,center=True).mean()

                # Add dummy variables for month, year, moon phase, etc.
                vtr_ais['Datetime'] = pd.to_datetime(vtr_ais['Datetime'])
                vtr_ais['Month'] = vtr_ais['Datetime'].dt.month
                vtr_ais['Year'] = vtr_ais['Datetime'].dt.year
                vtr_ais['Weekday'] = vtr_ais['Datetime'].dt.weekday
                vtr_ais['Date'] = vtr_ais['Datetime'].dt.date
                vtr_ais['Date'] = vtr_ais['Date'].astype(str)   

                # Merge with moon phase file by date
                vtr_ais = pd.merge(vtr_ais,moon_dat,on='Date')

                # Remove trips that are in the training dataset by creating a time and permit check to 
                # match to from the training data!
                vtr_ais['Unseen_check'] = vtr_ais['Permit'].astype(str) + " " + vtr_ais['Datetime'].astype(str)                                  
                unseenDat = vtr_ais[~vtr_ais['Unseen_check'].isin(checks)]
                
                # Remove unseen check column after checking
                unseenDat = unseenDat.drop('Unseen_check', axis=1)
                
                if len(unseenDat) > 0:
                    # Append back to day's AIS file
                    AIS_dfs.append(unseenDat)
                
        if len(AIS_dfs) > 0:
            AIS_dfs = pd.concat(AIS_dfs)
            # Save day AIS file
            save_AIS_path=os.path.join(out_path,filename[0:14] + '_unseen_boats.csv')
            AIS_dfs.to_csv(save_AIS_path)
        


# In[ ]:


# dat=vtr['Serial num'].astype(str).str.len()
# dat.plot(kind='kde')
# # Confirms that serial num column has values with 8 digits or 16 (eVTRs have 14 and paper have 8)
# # This column contains paper VTR numbers and autogenerated numbers for eVTRs


# In[ ]:


# dat=vtr['Supplier trip id'].astype(str).str.len()
# dat.plot(kind='kde')
# # Confirms that supplier trip id column has values with 7 digits and 14 (eVTRs have 14 and paper have 8)
# # This column contains eVTR numbers and autogenerated numbers for paper VTRs


# In[ ]:


# dat=vtr['VTR_num'].astype(str).str.len()
# dat.plot(kind='kde')
# # After correction 


# In[4]:


# Loop through the generated files and sort out by gear used (these will be the model input files)
all_trawl = []
all_clam = []
all_scallop = []
all_gillnet = []

for newFile in os.listdir(out_path):
    if newFile.endswith("unseen_boats.csv"):
        print(newFile)       
        loopDay=pd.read_csv(os.path.join(out_path, newFile))
        trawl = loopDay[(loopDay['Gear'] == 'trawl')].copy(deep=True)
        clam = loopDay[(loopDay['Gear'] == 'clam')].copy(deep=True)
        scallop = loopDay[(loopDay['Gear'] == 'scallop')].copy(deep=True)
        gillnet = loopDay[(loopDay['Gear'] == 'gillnet')].copy(deep=True)

        if len(trawl) > 0:
            all_trawl.append(trawl)
        if len(clam) > 0:
            all_clam.append(clam)
        if len(scallop) > 0:
            all_scallop.append(scallop)
        if len(gillnet) > 0:
            all_gillnet.append(gillnet)

# Save the gear files
all_trawl = pd.concat(all_trawl)
all_clam = pd.concat(all_clam)
all_scallop = pd.concat(all_scallop)
all_gillnet = pd.concat(all_gillnet)

all_trawl.to_csv(os.path.join(out_path,'all_trawl_2015-2018.csv'))
all_clam.to_csv(os.path.join(out_path,'all_clam_2015-2018.csv'))
all_scallop.to_csv(os.path.join(out_path,'all_scallop_2015-2018.csv'))
all_gillnet.to_csv(os.path.join(out_path,'all_gillnet_2015-2018.csv'))


# In[ ]:




