#!/usr/bin/env python
# coding: utf-8

# In[1]:


# Testing model configurations with training data
import numpy as np
import pandas as pd
import os, random
import datetime, time
import glob
from geopy.distance import geodesic
from shapely.geometry import Point

# Change settings to showing 1000 rows
pd.set_option('display.max_rows',None)
pd.options.display.max_columns=100


# In[2]:


# Load all tables
data_path = os.path.join(
    os.path.expanduser('~'),'Dropbox','My PC (DESKTOP-3PRD0P2)','Documents','CEC_project','Data_CEC_Project','Training_Data'
)

# Read in moon phase data
moon_dat = pd.read_csv(os.path.join(data_path,'Moon_phase.csv'))
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

# In[5]:


######################################################################
# Loop through all trips - by gear

# ALL WINDOW LENGTHS SHOULD BE ODD NUMBERS OF POINTS (WITH A MIDPOINT)
######################################################################

g = '_1min_scal.csv'
    
for filename in os.listdir(data_path):
    if filename.endswith(g):
        print(os.path.join(data_path, filename))        
        loopDat = pd.read_csv(os.path.join(data_path, filename))
        if len(loopDat)>0:
            loopDat = loopDat.rename(columns={'GEAR.NAME': 'GEAR'})

            # Starting with 15 point (minute) window - this is actually 14 minutes
            window_points = 15 
            window_minutes = window_points - 1
            assert window_minutes % 2 == 0
            half_minutes = window_minutes // 2

            # Add columns for change in time, speed, and depth
            loopDat['Datetime'] = pd.to_datetime(loopDat['Datetime'], infer_datetime_format=True)
            loopDat['d_SOG'] = loopDat['SOG'] - loopDat['SOG'].shift(1)
            loopDat['d_Time'] = loopDat['Datetime'] - loopDat['Datetime'].shift(1)
            loopDat['d_Depth'] = loopDat['Depth_m'] - loopDat['Depth_m'].shift(1)

            # Average and SD of SOG
            loopDat['SOG_Avg'] = loopDat['SOG'].rolling(window=window_points, center=True, min_periods=1).mean()
            loopDat['SOG_Std'] = loopDat['SOG'].rolling(window=window_points, center=True, min_periods=1).std()

            # Average and SD of Depth
            loopDat['Depth_Avg'] = loopDat['Depth_m'].rolling(window=window_points, center=True, min_periods=1).mean()
            loopDat['Depth_Std'] = loopDat['Depth_m'].rolling(window=window_points, center=True, min_periods=1).std()

            # Distance between points
            loopDat['Prev_LAT'] = loopDat['LAT'].shift(1)
            loopDat['Prev_LON'] = loopDat['LON'].shift(1)
            loopDat['Start_LAT'] = loopDat['LAT'].shift(half_minutes)
            loopDat['Start_LON'] = loopDat['LON'].shift(half_minutes)
            loopDat['End_LAT'] = loopDat['LAT'].shift(-half_minutes)
            loopDat['End_LON'] = loopDat['LON'].shift(-half_minutes)
            loopDat['Km_bw_pts']= loopDat.apply(lambda x: robust_dist(x['Prev_LAT'], x['Prev_LON'], x['LAT'], x['LON']),axis=1)

            # Start-end distance (as crow flies)
            loopDat['Crow_flies_km']= loopDat.apply(lambda x: robust_dist(x['Start_LAT'], x['Start_LON'], x['End_LAT'], x['End_LON']),axis=1)

            loopDat = loopDat.drop(columns=['Prev_LAT', 'Prev_LON', 'Start_LAT', 'Start_LON', 'End_LAT', 'End_LON'])

            # Total distance traveled
            loopDat['Total_km_trav'] = loopDat['Km_bw_pts'].rolling(window=window_points,center=True,min_periods=1).sum()

            # COG change column
            # Course over ground is 0 to 360, at due North we'll run into a 360 degree change potentially so I'm calculating 2 ways and using the minimum of the two
            loopDat['d_COG'] = abs(loopDat['COG'] - loopDat['COG'].shift(1))
            loopDat['d_COG'] = np.minimum(loopDat['d_COG'], 360 - loopDat['d_COG'])

            # Start-end COG change
            loopDat['d_COG_StartEnd'] = abs(loopDat['COG'].shift(half_minutes) - loopDat['COG'].shift(-half_minutes))
            loopDat['d_COG_StartEnd'] = np.minimum(loopDat['d_COG_StartEnd'], 360 - loopDat['d_COG_StartEnd'])

            # Mean COG change overall steps (this is actually absolute average deviation)
            loopDat['COG_Avg_Abs_d'] = loopDat['d_COG'].rolling(window=window_points,center=True).mean()

            # Add dummy variables for month, year, moon phase, etc.
            loopDat['Datetime'] = pd.to_datetime(loopDat['Datetime'])
            loopDat['Month'] = loopDat['Datetime'].dt.month
            loopDat['Year'] = loopDat['Datetime'].dt.year
            loopDat['Weekday'] = loopDat['Datetime'].dt.weekday
            loopDat['Date'] = loopDat['Datetime'].dt.date
            loopDat['Date'] = loopDat['Date'].astype(str)   
            # Merge with moon phase file by date (it's actually not a dummy)
            loopDat2 = pd.merge(loopDat,moon_dat,on='Date')

            # Save trip file
            out_path=os.path.join(data_path,filename[0:11] + '_prepped' + g)
            loopDat2.to_csv(out_path)


# In[6]:


loopDat2.head()


# In[7]:


all_files=glob.glob(os.path.join(data_path,"*prepped_1min_scal.csv"))
df_from_each_file_scal=(pd.read_csv(f, sep=',') for f in all_files)
df_merged_scal=pd.concat(df_from_each_file_scal, ignore_index=True)
df_merged_scal.to_csv(os.path.join(data_path,"all_scallop_trained.csv"))


# In[ ]:




