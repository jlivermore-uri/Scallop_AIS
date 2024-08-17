#!/usr/bin/env python
# coding: utf-8

# In[1]:


######################################################################
# Merging VMS to NEFOP trips for comparing accuracy with AIS model
######################################################################

import numpy as np
import pandas as pd
import os, random
from datetime import date, timedelta, datetime
import glob

# Change settings to showing 1000 rows
pd.options.display.max_rows=1000
pd.options.display.max_columns=100


# In[2]:


CEC_path = os.path.join(os.path.expanduser('~'),'Dropbox','My PC (DESKTOP-3PRD0P2)','Documents','CEC_project','Data_CEC_Project')
VMS_path = os.path.join(CEC_path,'VMS','ST19-001')


# In[3]:


# Read in compiled NEFOP haul info from Training_Dataset_Generation.ipynb
NEFOP = pd.read_csv(os.path.join(CEC_path,'NEFOP_for_comparison.csv'))
NEFOP.head()                    


# In[4]:


# Create a new column with year built into the trip id since they can reoccur in other years - for use later
NEFOP['TRIPID_YEAR'] = NEFOP['TRIPID'] + '-' + (NEFOP['YEAR'].astype(str))

# Remove trip H45001-2017 because there is an error with the trip end time.
NEFOP = NEFOP[(NEFOP['TRIPID_YEAR'] != 'H45001-2017')]
NEFOP.head()


# In[5]:


# Pull in list of trips we know we have overlap from the Merging_VMS_to_NEFOP.ipynb script
relevantTrips = pd.read_csv(os.path.join(VMS_path, 'VMS_NEFOP_alignment.csv'))
relevantTrips = relevantTrips[(relevantTrips['Has_VMS'] == 1)]
tripList = relevantTrips['Trip_ID'].unique()
tripList


# In[6]:


#############################################################################################
# Loop through all trips and compile points and NEFOP status of each point
#############################################################################################

# Create empty dataframe to build within the loop
all_trip_vms_pts = pd.DataFrame()
count = 0

trip_count = len(tripList)

for trip in tripList:
    
    this_trip = trip.lstrip()

    # Subset NEFOP data for trip
    subset = NEFOP[(NEFOP['TRIPID_YEAR'] == this_trip)].copy(deep=True)
    
    # Format trip times and pull permit umber and year
    if len(subset) > 0:
                
        # Clean up timestamp columns
        subset['TripStart'] = subset['DATESAIL'] + ' ' + subset['TIMESAIL'].copy(deep=True)
        subset['TripEnd'] = subset['DATELAND'] + ' ' + subset['TIMELAND'].copy(deep=True)
        subset['TRIPSTART'] = pd.to_datetime(subset['TripStart'], infer_datetime_format=True) 
        subset['TRIPEND'] = pd.to_datetime(subset['TripEnd'], infer_datetime_format=True)
        del subset['TripStart']
        del subset['TripEnd']

        start = subset['TRIPSTART'].min()
        end = subset['TRIPEND'].max()

        permit = subset.iloc[0]['PERMIT'].astype(str)
        yr = subset.iloc[0]['YEAR']
            
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
                
                # Drop all but correct permit
                next_file = next_file[(next_file['permit'] == permit)].copy(deep=True)
                
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
                                
                # Drop all but correct permit
                next_file = next_file[(next_file['permit'] == permit)].copy(deep=True)
                
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
                                
                # Drop all but correct permit
                next_file = next_file[(next_file['permit'] == permit)].copy(deep=True)
                
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
                                
                # Drop all but correct permit
                next_file = next_file[(next_file['permit'] == permit)].copy(deep=True)
                
                selected = selected.append(next_file)
        
        # Combine the VMS with the NEFOP trip data
        
        if len(selected) > 0:
            
            # Eliminate duplicate haul info (since there's a row for each species caught per haul)
            subset = subset[['YEAR', 'MONTH', 'DATESAIL', 'TRIPID', 'TIMESAIL', 'DATELAND', 'TIMELAND', 'VTRSERNO', 'PORTSAIL', 'PORTLAND', 'HAULNUM', 'OBSRFLAG', 'DATEHBEG_x', 'DATEHEND_x', 'NEGEAR', 'GEAR NAME', 'DATEHBEG_y', 'DATEHEND_y', 'GIS_LATHBEG_y', 'GIS_LONHBEG_y', 'GIS_LATHEND_y', 'GIS_LONHEND_y', 'DATE_BEG', 'DATE_END', 'TRIPID_YEAR', 'TRIPSTART', 'TRIPEND']].copy(deep=True)
            subset = subset.drop_duplicates().copy(deep=True)

            # Generate dataset with interspersing VMS and NEFOP observations
            # First need to create 2 rows/haul/trip where one row is the start and the other is the end
            del subset['DATEHBEG_x']
            del subset['DATEHEND_x']
            subset_end = subset.copy(deep=True)
            subset_start = subset.copy(deep=True)
            subset_end['Haul_Status'] = 'END'
            subset_start['Haul_Status'] = 'START'
            subset_start['utc_Date'] = subset_start['DATEHBEG_y']
            subset_end['utc_Date'] = subset_end['DATEHEND_y']
            newDat = subset_start.append(subset_end, ignore_index=True).copy(deep=True)
            
            # Identified some incorrect values in the NEFOP dataset - they appear to be missing LAT LON coordinates so using that to eliminate them
            newDat = newDat.sort_values(by='utc_Date')
            newDat.dropna(subset=['GIS_LATHBEG_y'], inplace=True)
                
            # Combine with VMS data (not merging - rather stacking via concatenate)
            selected['Haul_Status'] = 'VMS'
            alltimes = pd.concat([selected, newDat], sort=False).copy(deep=True)
            
            # Sort data by timestamp
            alltimes['utc_Date'] = pd.to_datetime(alltimes['utc_Date']).copy(deep=True)
            alltimes = alltimes.sort_values(by='utc_Date')
            
            # Create a new column for status of each row (start or end of NEFOP haul, or VMS datapoint)
            alltimes['Status'] = np.where(alltimes['Haul_Status'] == 'VMS', 0, 1)
            alltimes['Status'] = np.where(alltimes['Haul_Status'] == 'END', -1, alltimes['Status'])
            alltimes['Cumulative_Sum'] = alltimes['Status'].cumsum(axis = 0)

            # Add additional column to VMS rows to denote whether the vessel is fishing on a NEFOP trip
            VMS_only = alltimes[(alltimes['Haul_Status'] == 'VMS')].copy(deep=True)
            VMS_only['NEFOP_Fishing'] = VMS_only['Cumulative_Sum']
    
            if isinstance(VMS_only.iloc[0]['decl_code'], str) == True:
            
                dec_code = VMS_only.iloc[0]['decl_code']
                VMS_only['DECCODE'] = VMS_only['decl_code'].astype(str).str[:3]

                # Add column for speed cutoff prediction (do scallop separately)
                if dec_code == 'SES':
                    VMS_only['Speed_Fishing_Prediction'] = np.where((VMS_only['avg_speed'] <= 5),1,0)
                else:
                    VMS_only['Speed_Fishing_Prediction'] = np.where((VMS_only['avg_speed'] <= 4),1,0)

                # Add column for whether speed prediction is correct or not
                VMS_only['Speed_Method_Correct'] = np.where(((VMS_only['NEFOP_Fishing'] - VMS_only['Speed_Fishing_Prediction']) == 0),1,0)

                # Append to previous trips data
                all_trip_vms_pts = all_trip_vms_pts.append(VMS_only)

    # Reporting out loop progress
    print(this_trip + ' complete at: ') 
    print(pd.to_datetime("now"))
    count = count + 1
    progress = 100*count/trip_count
    print('Trip ' + str(count) + ' out of ' + str(trip_count) + '. Loop ' + str(round(progress,2)) + '% complete.')

all_trip_vms_pts.head()


# In[7]:


VMS_only.head()


# In[8]:


all_trip_vms_pts['YEAR'] = pd.DatetimeIndex(all_trip_vms_pts['utc_Date']).year
out = os.path.join(CEC_path,'VMS_NEFOP_accuracy_check.csv')
all_trip_vms_pts.to_csv(out)


# In[9]:


FMPs = ['SES','SMB','MNK','SCO','NMS','DOF']
for FMP in FMPs:
    FMPdat = all_trip_vms_pts[(all_trip_vms_pts['DECCODE'] == FMP)]
    numCorrect = FMPdat['Speed_Method_Correct'].sum()
    totalPts = FMPdat['Speed_Method_Correct'].count()
    print('Percent correct for ' + FMP + ' FMP: ' + (numCorrect/totalPts).astype('str'))

