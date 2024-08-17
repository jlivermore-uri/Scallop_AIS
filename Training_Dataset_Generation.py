#!/usr/bin/env python
# coding: utf-8

# In[2]:


# Merging vessels in AIS to NEFOP
import numpy as np
import pandas as pd
import os, random
from datetime import date, timedelta, datetime
import glob

# Change settings to showing 1000 rows
pd.options.display.max_rows=1000
pd.options.display.max_columns=100


# In[3]:


# Load all tables
AIS_path = os.path.join(
    os.path.expanduser('~'),'Dropbox','My PC (DESKTOP-3PRD0P2)','Documents','CEC_project','Data_CEC_Project'
)

AIS = pd.read_csv(os.path.join(AIS_path, 'AIS_GARFO_MATCHED_2015_2018.csv'))


# In[4]:


Obs_path = os.path.join(
    os.path.expanduser('~'),'Dropbox','My PC (DESKTOP-3PRD0P2)','Documents','CEC_project','Data_CEC_Project','ObserverRequest','Data', 'ObsData20200304-081502','riobtrp'
)
NEFOP = pd.read_csv(os.path.join(Obs_path, 'NEFOP_CATCH_VES_SP_GEAR_noLoranBound.csv'))

# Clean up duplicate columns post NEFOP table merges
del NEFOP['NEGEAR_y']
del NEFOP['AREA_y']
del NEFOP['HULLNUM1']
del NEFOP['PERMIT1']
del NEFOP['NEGEAR_x']


# In[5]:


# NEFOP data were not requested/pulled correctly initially so a second Trip Haul table was pulled and received 3/23/2021 from NOAA
# Need to merge in the times from the start and ends of each haul from the secondary dataset
# NOAA staff were rushed when doing the data pull, so they just did a larger pull and there will be orphan data points 
# that won't match up with other data tables (inner join should drop data from this second dataset)
NEFOP_newhaul = pd.read_csv(os.path.join(Obs_path, 'riobhau03222021.csv'))

# Merge old to new data pulls with as many matching columns as possible
NEFOP_ALL = pd.merge(NEFOP, NEFOP_newhaul, how='inner', on=['YEAR','MONTH','TRIPID','HAULNUM','NEGEAR','TARGSPEC1','OBSRFLAG','NEMAREA','DEPTH','TARGSPEC2','WTMP','SOAKDUR','HAULDUR'])
del NEFOP_ALL['Unnamed: 0']
del NEFOP_ALL['AREA_x']
del NEFOP_ALL['GIS_LATHBEG_x']
del NEFOP_ALL['GIS_LATHEND_x']
del NEFOP_ALL['GIS_LONHBEG_x']
del NEFOP_ALL['GIS_LONHEND_x']
NEFOP_ALL = NEFOP_ALL.loc[NEFOP_ALL['YEAR'] > 2014]
NEFOP_ALL = NEFOP_ALL.loc[NEFOP_ALL['YEAR'] < 2019]

# Create columns of just dates
NEFOP_ALL['DATE_BEG'] = NEFOP_ALL['DATEHBEG_y'].str.slice(0, 11)
NEFOP_ALL['DATE_END'] = NEFOP_ALL['DATEHEND_y'].str.slice(0, 11)

# Convert haul times to datetime format
NEFOP_ALL['DATEHBEG_y'] = pd.to_datetime(NEFOP_ALL['DATEHBEG_y'], infer_datetime_format=True) 
NEFOP_ALL['DATEHEND_y'] = pd.to_datetime(NEFOP_ALL['DATEHEND_y'], infer_datetime_format=True) 


# In[6]:


# Fix data types before merging
NEFOP_ALL['PERMIT'] = NEFOP_ALL['PERMIT'].fillna(0).astype(int).copy(deep=True)
AIS['HULL ID'] = AIS['HULL ID'].astype(str).copy(deep=True)
NEFOP_ALL['HULLNUM'] = NEFOP_ALL['HULLNUM'].astype(str).copy(deep=True)
NEFOP_ALL.head()


# In[ ]:


# Save this file for comparing datasets later on
NEFOP_ALL.to_csv(os.path.join(os.path.join(os.path.expanduser('~'),'Dropbox','My PC (DESKTOP-3PRD0P2)','Documents','CEC_project','Data_CEC_Project'),"NEFOP_for_comparison.csv"))


# In[6]:


# THIS IS WHERE THE CLAM DATA WERE DISAPPEARING!
# Issue was the the permit numbers for clam data were stored differently than all others in the AIS file!!!
# Issue with scallop was resolved by reformatting trip departures and return times in original .csv for trips from GARFO's NEFOP data.

# Merge AIS/GARFO file to the merged NEFOP data
dat = pd.merge(AIS, NEFOP_ALL, how='inner', left_on=['HULL ID','PERMIT','PERMIT YEAR'], right_on=['HULLNUM','PERMIT','YEAR']).copy(deep=True)

unique_ves_in_both = dat[['MMSI', 'CallSign', 'HULLNUM', 'YEAR', 'PERMIT', 'GEAR NAME']].copy(deep=True)
unique_ves_in_both = unique_ves_in_both.drop_duplicates().reset_index(drop=True).copy(deep=True)


# In[7]:


# Merge unique vessels back to NEFOP to see trips/year by gear
NEFOP_AIS = pd.merge(AIS, NEFOP_ALL, how='inner', left_on=['HULL ID','PERMIT','PERMIT YEAR'], right_on=['HULLNUM','PERMIT','YEAR'])
del NEFOP_AIS['DATEHBEG_x']
del NEFOP_AIS['DATEHEND_x']
del NEFOP_AIS['VesselName_y']
del NEFOP_AIS['VESSEL NAME_x']
del NEFOP_AIS['VESSEL NAME_y']

# Create a new column with year built into the trip id since they can reoccur in other years - for use later
NEFOP_AIS['TRIPID_YEAR'] = NEFOP_AIS['TRIPID'] + '-' + (NEFOP_AIS['YEAR'].astype(str))
all_trips = NEFOP_AIS['TRIPID_YEAR'].unique()

# In[8]:


# In[9]:


# Create empty dataframe to build within the loop
count = 0
trip_count = len(loop_trips)

# Pull in NEFOP/VMS check file
VMS_check = pd.read_csv('C:/Users/julia/Dropbox/My PC (DESKTOP-3PRD0P2)/Documents/CEC_project/Data_CEC_Project/VMS/ST19-001/VMS_NEFOP_alignment.csv')

# Path to save output files into
out_path = os.path.join(os.path.expanduser('~'),'Dropbox','My PC (DESKTOP-3PRD0P2)','Documents','CEC_project','Data_CEC_Project','Training_Data')

for trip in loop_trips:
    this_trip = trip.lstrip()

    # Add new column for haul number plus the trip ID
    NEFOP_ALL['TRIPID_YEAR'] = NEFOP_ALL['TRIPID'] + '-' + (NEFOP_ALL['YEAR'].astype(str))
    NEFOP_ALL['TRIPID_HAUL'] = NEFOP_ALL['TRIPID_YEAR'] + '-' + NEFOP_ALL['HAULNUM'].values.astype(str)

    # Subset NEFOP data for trip
    subset = NEFOP_ALL[(NEFOP_ALL['TRIPID_YEAR'] == this_trip)].copy(deep=True)
    
    # Create clean, formatted times
    subset['TripStart'] = subset['DATESAIL'] + ' ' + subset['TIMESAIL'].copy(deep=True)
    subset['TripEnd'] = subset['DATELAND'] + ' ' + subset['TIMELAND'].copy(deep=True)
    subset['TRIPSTART'] = pd.to_datetime(subset['TripStart'], infer_datetime_format=True) 
    subset['TRIPEND'] = pd.to_datetime(subset['TripEnd'], infer_datetime_format=True)
    del subset['TripStart']
    del subset['TripEnd']
    start = subset['TRIPSTART'].min()
    end = subset['TRIPEND'].max()

    # Pull some key trip variables from NEFOP data
    if len(subset) > 0:
        boat = subset.iloc[0]['PERMIT'].round().astype(int).astype(str)
        gear = subset.iloc[0]['GEAR NAME']
        start_year = subset.iloc[0]['YEAR']
        subset['Start_month'] = pd.to_datetime(subset['TRIPSTART']).dt.to_period('M')
        start_month = subset.iloc[0]['Start_month']

    # Format dates for pulling in AIS files by their file names
    start_date = start.strftime('%Y_%m_%d')
    end_date = end.strftime('%Y_%m_%d')
    start_date_format = start.strftime('%Y-%m-%d')
    end_date_format = end.strftime('%Y-%m-%d')
    start_date_again = pd.to_datetime(start_date_format, infer_datetime_format=True)
    end_date_again = pd.to_datetime(end_date_format, infer_datetime_format=True)
    dates = pd.date_range(start_date_again, end_date_again, freq='d')

    # Different setup based on 1-day vs. multi-day trips
    if len(dates) == 1:
        file = 'AIS_' + start_date + '.csv'
        filename = os.path.join(AIS_path, 'AIS', 'FV_only', file)
        if os.path.exists(os.path.join(AIS_path, 'AIS', 'FV_only', filename)) == True:
            selected = pd.read_csv(filename)
            selected['Datetime'] = pd.to_datetime(selected['Datetime'], infer_datetime_format=True)
            selected = selected[pd.to_datetime(selected['Datetime']) >= pd.to_datetime(start)].copy(deep=True)
            selected = selected[pd.to_datetime(selected['Datetime']) < pd.to_datetime(end)].copy(deep=True) 
            if len(selected) > 0:
                selected['YEAR'] = pd.to_datetime(selected['Datetime']).dt.to_period('Y').astype(str).astype(int)
                selected = pd.merge(selected, unique_ves_in_both, how='inner', on=['MMSI','CallSign','YEAR']).copy(deep=True)
                selected = selected[(selected['PERMIT'].round().astype(int).astype(str) == boat)].copy(deep=True)
    elif len(dates) > 1:
        selected = pd.DataFrame()
        for i in dates:
            file_date = i.strftime('%Y_%m_%d')
            file = 'AIS_' + file_date + '.csv'
            filename = os.path.join(AIS_path, 'AIS', 'FV_only', file)
            if os.path.exists(os.path.join(AIS_path, 'AIS', 'FV_only', filename)) == True:
                next_file = pd.read_csv(filename)
                next_file['Datetime'] = pd.to_datetime(next_file['Datetime'], infer_datetime_format=True)
                next_file = next_file[pd.to_datetime(next_file['Datetime']) >= pd.to_datetime(start)].copy(deep=True)
                next_file = next_file[pd.to_datetime(next_file['Datetime']) < pd.to_datetime(end)].copy(deep=True)
                selected = selected.append(next_file)
        if len(selected) > 0:
            selected['YEAR'] = pd.to_datetime(selected['Datetime']).dt.to_period('Y').astype(str).astype(int)
            selected = pd.merge(selected, unique_ves_in_both, how='inner', on=['MMSI','CallSign','YEAR']).copy(deep=True)
            selected = selected[(selected['PERMIT'].round().astype(int).astype(str) == boat)].copy(deep=True)
            selected['DATE'] = pd.to_datetime(selected['Datetime']).dt.date

    if len(selected) > 0:
        ves_len = selected.iloc[0]['Length']

        # Calculate total trip length (from NEFOP start and end trip times)
        trip_time = (end - start).total_seconds()

        # Calculate fishing time per haul (from NEFOP start and end hauls)
        subset['HAUL_TIME_LENGTH'] =  (subset['DATEHEND_y'] - subset['DATEHBEG_y']).dt.total_seconds().copy(deep=True)

        # Eliminate duplicate haul info (since there's a row for each species caught per haul)
        subset = subset[['YEAR', 'MONTH', 'DATESAIL', 'TRIPID', 'TIMESAIL', 'DATELAND', 'TIMELAND', 'VTRSERNO', 'PORTSAIL', 'PORTLAND', 'HAULNUM', 'OBSRFLAG', 'DATEHBEG_x', 'DATEHEND_x', 'NEGEAR', 'GEAR NAME', 'DATEHBEG_y', 'DATEHEND_y', 'GIS_LATHBEG_y', 'GIS_LONHBEG_y', 'GIS_LATHEND_y', 'GIS_LONHEND_y', 'DATE_BEG', 'DATE_END', 'TRIPID_YEAR', 'TRIPSTART', 'TRIPEND', 'HAUL_TIME_LENGTH']].copy(deep=True)
        subset = subset.drop_duplicates().copy(deep=True)

        # Add up all the fishing times (1 time per haul now)
        fishing_time = subset['HAUL_TIME_LENGTH'].sum()

        # Calculate the share of time spent fishing out of total trip time
        share_fishing = fishing_time/trip_time

        # Calculate # of hauls on trip
        num_hauls = len(subset)

        # Now need to determine what share of AIS pings are during fishing by gear and by year
        # Generate dataset with interspersing AIS and NEFOP observations
        # First need to create 2 rows/haul/trip where one row is the start and the other is the end
        del subset['DATEHBEG_x']
        del subset['DATEHEND_x']
        subset_end = subset.copy(deep=True)
        subset_start = subset.copy(deep=True)
        subset_end['Haul_Status'] = 'END'
        subset_start['Haul_Status'] = 'START'
        subset_start['Datetime_orig'] = subset_start['DATEHBEG_y']
        subset_end['Datetime_orig'] = subset_end['DATEHEND_y']
        newDat = subset_start.append(subset_end, ignore_index=True).copy(deep=True)

        # Convert NEFOP times to UTC to match the AIS (need to account for daylight savings time)
        if start_year == 2015:
            if datetime(2015, 3, 8, 2, 0, 0) <= start.to_pydatetime() <= datetime(2015, 11, 1, 2, 0, 0):
                newDat['Datetime'] = newDat['Datetime_orig'] + timedelta(0, 4*60*60)
            else:
                newDat['Datetime'] = newDat['Datetime_orig'] + timedelta(0, 5*60*60)
        elif start_year == 2016:
            if datetime(2016, 3, 13, 2, 0, 0) <= start.to_pydatetime() <= datetime(2016, 11, 6, 2, 0, 0):
                newDat['Datetime'] = newDat['Datetime_orig'] + timedelta(0, 4*60*60)
            else:
                newDat['Datetime'] = newDat['Datetime_orig'] + timedelta(0, 5*60*60)
        elif start_year == 2017:
            if datetime(2017, 3, 12, 2, 0, 0) <= start.to_pydatetime() <= datetime(2017, 11, 5, 2, 0, 0):
                newDat['Datetime'] = newDat['Datetime_orig'] + timedelta(0, 4*60*60)
            else:
                newDat['Datetime'] = newDat['Datetime_orig'] + timedelta(0, 5*60*60)
        elif start_year == 2018:
            if datetime(2018, 3, 11, 2, 0, 0) <= start.to_pydatetime() <= datetime(2018, 11, 4, 2, 0, 0):
                newDat['Datetime'] = newDat['Datetime_orig'] + timedelta(0, 4*60*60)
            else:
                newDat['Datetime'] = newDat['Datetime_orig'] + timedelta(0, 5*60*60)

        newDat = newDat.sort_values('Datetime').copy(deep=True)

        # Merge with AIS data
        NumPingsDuringTrip = len(selected)
        selected['Haul_Status'] = 'AIS'
        alltimes = pd.concat([selected, newDat], sort=False).copy(deep=True)
        alltimes['Datetime'] = pd.to_datetime(alltimes['Datetime']).copy(deep=True)

        # Create a new column for status of each row (start or end of NEFOP haul, or AIS datapoint)
        alltimes['Status'] = np.where(alltimes['Haul_Status'] == 'AIS', 0, 1)
        alltimes['Status'] = np.where(alltimes['Haul_Status'] == 'END', -1, alltimes['Status'])
        alltimes = alltimes.sort_values('Datetime').copy(deep=True)
        alltimes['Cumulative_Sum'] = alltimes['Status'].cumsum(axis = 0) 

        # Create another column to calculate whether the haul has corresponding AIS
        alltimes['Shifted_Status'] = alltimes['Status'].shift(-1)
        alltimes['HAUL_W_AIS'] = (alltimes['Status'] == 1)*(alltimes['Shifted_Status'] == 0)*1

        # Add additional column to AIS rows to denote whether the vessel is fishing on a NEFOP trip
        AIS_only = alltimes[(alltimes['Haul_Status'] == 'AIS')].copy(deep=True)
        AIS_only['NEFOP_Fishing'] = AIS_only['Cumulative_Sum']
        
        # Pull in corresponding declaration code
        AIS_VMS_check = VMS_check[(VMS_check['Trip_ID'] == this_trip)].copy(deep=True)
        ves_dec = AIS_VMS_check.iloc[0]['Declaration_Code']
        AIS_only['Declaration_code'] = ves_dec
        
        # Generate third trip id column to pull in the actual trip number (whether it came over from the VMS or not)
        AIS_only['TRIP_ID'] = this_trip
        
        AIS_w_VMS = AIS_only[['MMSI', 
                              'CallSign', 
                              'HULLNUM', 
                              'PERMIT', 
                              'GEAR NAME',
                              'SOG',
                              'COG',
                              'Heading',
                              'Length',
                              'Datetime',
                              'LAT', 
                              'LON',
                              'TRIP_ID',
                              'NEFOP_Fishing',
                              'Declaration_code']].copy(deep=True)

        # Add in step to make sure that NEFOP_Fishing code is calculated correctly - this stems from an issue in the NEFOP files
        if ((max(AIS_w_VMS['NEFOP_Fishing']) == 1) and (min(AIS_w_VMS['NEFOP_Fishing']) == 0)):
            
            outfile = this_trip + '_good.csv'
            out_path_2 = os.path.join(out_path, outfile)
            AIS_w_VMS.to_csv(out_path_2)

            print(this_trip + ' complete at: ') 
            print(pd.to_datetime("now"))
            count = count + 1
            progress = 100*count/trip_count
            print('Trip ' + str(count) + ' out of ' + str(trip_count) + '. Loop ' + str(round(progress,2)) + '% complete.')
    
        else:
            
            outfile = this_trip + '_bad.csv'
            out_path_2 = os.path.join(out_path, outfile)
            AIS_w_VMS.to_csv(out_path_2)

            print(this_trip + ' complete at: ') 
            print(pd.to_datetime("now"))
            count = count + 1
            progress = 100*count/trip_count
            print('Trip ' + str(count) + ' out of ' + str(trip_count) + '. Loop ' + str(round(progress,2)) + '% complete.')
            
        
    elif len(selected) == 0:
        count = count + 1
        progress = 100*count/trip_count
        print(this_trip + ' has no corresponding AIS data.') 
        print('Trip ' + str(count) + ' out of ' + str(trip_count) + '. Loop ' + str(round(progress,2)) + '% complete.')


# In[10]:


# Combine all good training data into one csv file
out_path = os.path.join(os.path.expanduser('~'),'Dropbox','My PC (DESKTOP-3PRD0P2)','Documents','CEC_project','Data_CEC_Project','Training_Data')

all_files = glob.glob(os.path.join(out_path, "*_good.csv"))
df_from_each_file = (pd.read_csv(f, sep=',') for f in all_files)
df_merged = pd.concat(df_from_each_file, ignore_index=True)
df_merged['FMP'] = df_merged.Declaration_code.str.slice(0,3)
df_merged.to_csv(os.path.join(out_path,"all_training_data.csv"))


# In[11]:


df_merged.head()


# In[12]:


# Breakdown of Declaration Codes (see if there's gillnet data in the monkfish)
dec_codes = df_merged.groupby(['GEAR NAME', 'FMP'])['TRIP_ID'].nunique()
dec_codes.to_csv(os.path.join(out_path,"training_data_Dec_Code_summary.csv"))
dec_codes


# In[13]:


# Check for speed over ground and heading anomalies
df_merged.describe()


# In[14]:


df_merged.boxplot(column=['SOG'])


# In[15]:


df_merged.boxplot(column=['COG'])


# In[16]:


df_merged['NEFOP_Fishing'].unique()


# In[17]:


df_merged['NEFOP_Fishing'].value_counts()


# In[ ]:


# Script AFTER this one is Time_adjustment_1min

