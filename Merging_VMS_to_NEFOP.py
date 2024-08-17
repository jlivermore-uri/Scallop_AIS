#!/usr/bin/env python
# coding: utf-8

# In[1]:


###################################
# Merging VMS to NEFOP trips
###################################

# How many VMS points do we have on nefop trips?
import numpy as np
import pandas as pd
import os, random
from datetime import date, timedelta, datetime

# Change settings to showing 1000 rows
pd.options.display.max_rows=1000
pd.options.display.max_columns=100


# In[2]:


# Load all tables
CEC_path = os.path.join(os.path.expanduser('~'),'Dropbox','My PC (DESKTOP-3PRD0P2)','Documents','CEC_project','Data_CEC_Project')
VMS_path = os.path.join(CEC_path,'VMS','ST19-001')
NEFOP_trips = pd.read_csv(os.path.join(CEC_path,'ObserverRequest','Data','ObsData20200304-081502','riobtrp','riobtrp_time_formatted.csv'))
NEFOP_trips = NEFOP_trips[NEFOP_trips['YEAR'] > 2014].copy(deep=True)
NEFOP_trips = NEFOP_trips[NEFOP_trips['YEAR'] < 2019].copy(deep=True)
NEFOP_trips['SAIL'] = NEFOP_trips['DATESAIL'] + ' ' + NEFOP_trips['TIMESAIL'].copy(deep=True)
NEFOP_trips['LAND'] = NEFOP_trips['DATELAND'] + ' ' + NEFOP_trips['TIMELAND'].copy(deep=True)
NEFOP_trips['TRIPSTART'] = pd.to_datetime(NEFOP_trips['SAIL'], infer_datetime_format=True) 
NEFOP_trips['TRIPEND'] = pd.to_datetime(NEFOP_trips['LAND'], infer_datetime_format=True)


# In[3]:


# Fix NEFOP Permit Number formatting
NEFOP_trips['PERMIT'] = NEFOP_trips['PERMIT1'].round().astype('Int64').astype('str')

# Create a new column with year built into the trip id since they can reoccur in other years - for use later
NEFOP_trips['TRIPID_YEAR'] = NEFOP_trips['TRIPID'] + '-' + (NEFOP_trips['YEAR'].astype(str))
all_trips = NEFOP_trips['TRIPID_YEAR'].unique()

# Remove trip XXXXXX-XXXX because there is an error with the trip end time.
# NOTE: REPLACED TRIP ID HERE WITH XXXXXX-XXXX TO MAINTAIN CONFIDENTIALITY
loop_trips = all_trips[(all_trips != 'XXXXXX-XXXX')]


# In[ ]:


###################################
# Loop through all trips
###################################

# Create empty dataframe to build within the loop
all_trips_info = pd.DataFrame()
count = 0

trip_count = len(loop_trips)

for trip in loop_trips:
    
    this_trip = trip.lstrip()

    # Subset NEFOP data for trip
    subset = NEFOP_trips[(NEFOP_trips['TRIPID_YEAR'] == this_trip)].copy(deep=True)
    subset['TripStart'] = subset['DATESAIL'] + ' ' + subset['TIMESAIL'].copy(deep=True)
    subset['TripEnd'] = subset['DATELAND'] + ' ' + subset['TIMELAND'].copy(deep=True)
    subset['TRIPSTART'] = pd.to_datetime(subset['TripStart'], infer_datetime_format=True) 
    subset['TRIPEND'] = pd.to_datetime(subset['TripEnd'], infer_datetime_format=True)
    del subset['TripStart']
    del subset['TripEnd']
    start = subset['TRIPSTART'].min()
    end = subset['TRIPEND'].max()
        
    permit = subset.iloc[0]['PERMIT']
    yr = subset.iloc[0]['YEAR']
    
    # Pull some key trip variables from NEFOP data
    if len(subset) > 0:
        
        selected = pd.DataFrame()
    
        if yr == 2015:

            # Iterate through the VMS files
            for i in os.listdir(os.path.join(VMS_path, '2015')):
                file = os.path.join(VMS_path, '2015', i)
                next_file = pd.read_csv(file)

                # Pull VMS rows within the NEFOP timeframe
                next_file['utc_Date'] = pd.to_datetime(next_file['utc_Date'], infer_datetime_format=True)
                next_file = next_file[pd.to_datetime(next_file['utc_Date']) >= pd.to_datetime(start)].copy(deep=True)
                next_file = next_file[pd.to_datetime(next_file['utc_Date']) < pd.to_datetime(end)].copy(deep=True)
                selected = selected.append(next_file)
                
        if yr == 2016:

            # Iterate through the VMS files
            for i in os.listdir(os.path.join(VMS_path, '2016')):
                file = os.path.join(VMS_path, '2016', i)
                next_file = pd.read_csv(file)

                # Pull VMS rows within the NEFOP timeframe
                next_file['utc_Date'] = pd.to_datetime(next_file['utc_Date'], infer_datetime_format=True)
                next_file = next_file[pd.to_datetime(next_file['utc_Date']) >= pd.to_datetime(start)].copy(deep=True)
                next_file = next_file[pd.to_datetime(next_file['utc_Date']) < pd.to_datetime(end)].copy(deep=True)
                selected = selected.append(next_file)
                
        if yr == 2017:

            # Iterate through the VMS files
            for i in os.listdir(os.path.join(VMS_path, '2017')):
                file = os.path.join(VMS_path, '2017', i)
                next_file = pd.read_csv(file)

                # Pull VMS rows within the NEFOP timeframe
                next_file['utc_Date'] = pd.to_datetime(next_file['utc_Date'], infer_datetime_format=True)
                next_file = next_file[pd.to_datetime(next_file['utc_Date']) >= pd.to_datetime(start)].copy(deep=True)
                next_file = next_file[pd.to_datetime(next_file['utc_Date']) < pd.to_datetime(end)].copy(deep=True)
                selected = selected.append(next_file)
                
        if yr == 2018:

            # Iterate through the VMS files
            for i in os.listdir(os.path.join(VMS_path, '2018')):
                file = os.path.join(VMS_path, '2018', i)
                next_file = pd.read_csv(file)

                # Pull VMS rows within the NEFOP timeframe
                next_file['utc_Date'] = pd.to_datetime(next_file['utc_Date'], infer_datetime_format=True)
                next_file = next_file[pd.to_datetime(next_file['utc_Date']) >= pd.to_datetime(start)].copy(deep=True)
                next_file = next_file[pd.to_datetime(next_file['utc_Date']) < pd.to_datetime(end)].copy(deep=True)
                selected = selected.append(next_file)
        
        # Combine the VMS with the NEFOP trip data
        trip_dat = pd.merge(subset, selected, how='inner', left_on='PERMIT', right_on='permit')

        vms_len = len(trip_dat)
        
        if vms_len > 0:
            # Sort VMS by timestamp
            trip_dat = trip_dat.sort_values(by='utc_Date')
            
            dec_code = trip_dat.iloc[0]['decl_code']
            
            # Create a dataframe with target outputs
            info = {'Trip_ID': [this_trip],
                    'Has_VMS': [1],
                    'Num_VMS_pts': [vms_len],
                    'Permit': [permit],
                    'Declaration_Code': [dec_code],
                    'Year': [yr]
                     }
    
            trip_info = pd.DataFrame(info)
                
        if vms_len == 0:
            
            # Save trip info
            info = {'Trip_ID': [this_trip],
                    'Has_VMS': [0],
                    'Num_VMS_pts': [0],
                    'Permit': [permit],
                    'Declaration_Code': ['NA'],
                    'Year': [yr]
                     }
    
            trip_info = pd.DataFrame(info)
                
        # Append to previous trips data
        all_trips_info = all_trips_info.append(trip_info)

        # Reporting out loop progress
        print(this_trip + ' complete at: ') 
        print(pd.to_datetime("now"))
        count = count + 1
        progress = 100*count/trip_count
        print('Trip ' + str(count) + ' out of ' + str(trip_count) + '. Loop ' + str(round(progress,2)) + '% complete.')
    
all_trips_info


# In[ ]:


out = os.path.join(VMS_path, 'VMS_NEFOP_alignment.csv')
all_trips_info.to_csv(out)


# In[ ]:


# Merge NEFOP trip information back to the VMS to see alignment between the two datasets
Obs_path = os.path.join(
    os.path.expanduser('~'), # will take me to the current user's top level directory
    'CEC_project','Data_CEC_Project','ObserverRequest','Data', 'ObsData20200304-081502','riobtrp'
)
NEFOP = pd.read_csv(os.path.join(Obs_path, 'NEFOP_CATCH_VES_SP_GEAR_noLoranBound.csv'))
NEFOP['TRIPID_YEAR'] = NEFOP['TRIPID'].astype(str) + '-' + (NEFOP['YEAR'].astype(str))

all_trips_info['TRIPID_YEAR'] = all_trips_info['Trip_ID'].astype(str)

all_dat = pd.merge(NEFOP[['TRIPID_YEAR','GEAR NAME', 'PERMIT', 'NEGEAR_y', 'VESSEL NAME', 'YEAR']], all_trips_info, on='TRIPID_YEAR', how='left').copy(deep=True)
all_dat2 = all_dat.drop_duplicates().copy(deep=True)
all_dat2.head()


# In[ ]:


all_dat2 = all_dat2.loc[all_dat2['YEAR'] > 2014].copy(deep=True)
all_dat2 = all_dat2.loc[all_dat2['YEAR'] < 2019].copy(deep=True)

out2 = os.path.join(VMS_path, 'VMS_NEFOP_alignment_merged.csv')
all_dat2.to_csv(out2)


# In[ ]:




