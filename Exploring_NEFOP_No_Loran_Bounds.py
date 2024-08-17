#!/usr/bin/env python
# coding: utf-8

# In[1]:


# Load all important packages
import numpy as np
import pandas as pd
import os, random
pd.set_option('display.max_columns', None)


# In[2]:


# Load all tables C:\Users\julia\Dropbox\My PC (DESKTOP-3PRD0P2)\Documents\CEC_project\Data_CEC_Project\ObserverRequest\Data
Obs_path = os.path.join(
    os.path.expanduser('~'), # will take me to the current user's top level directory
    'Dropbox','My PC (DESKTOP-3PRD0P2)','Documents','CEC_project','Data_CEC_Project','ObserverRequest','Data','ObsData20200304-081502','riobtrp'
)

catch = pd.read_csv(os.path.join(Obs_path, 'riobcatch.csv'))
catch.head()


# In[3]:


haul = pd.read_csv(os.path.join(Obs_path, 'riobhau03222021.csv'))
haul
# Check for NANs on this - mixed data type


# In[4]:


trip = pd.read_csv(os.path.join(Obs_path, 'riobtrp_time_formatted.csv'))
trip.head()


# In[5]:


# Combine trip and haul data
trip_haul = pd.merge(trip, haul, how='inner', on=['TRIPID','YEAR','MONTH'])
trip_haul.head()


# In[6]:


for col in trip_haul.columns: 
    print(col)


# In[7]:


len(trip_haul)


# In[8]:


# TRIPID is only unique within a year
total_trips = 0
for year in range(2015, 2018+1): # The 2018+1 will make 2018 as the last year in the range
    t = len(trip_haul[trip_haul['YEAR'] == year].TRIPID.unique())
    total_trips += t
    print(year, t)
print('Total trips:', total_trips)


# In[9]:


trip_haul.head()


# In[10]:


# Merge trip-haul data with catch data
all_dat = pd.merge(trip_haul, catch, how='inner', on=['HAULNUM','TRIPID','YEAR','MONTH'])
all_dat.head()


# In[11]:


vessels = pd.read_csv(os.path.join(Obs_path, 'OBVESSEL.csv'))
species = pd.read_csv(os.path.join(Obs_path, 'OBSPEC.csv'))
gears = pd.read_csv(os.path.join(Obs_path, 'OBGEAR.csv'))

# Pull in vessel ID info (name)
all_dat = pd.merge(all_dat, vessels, how='inner', left_on=['HULLNUM1','PERMIT1'], right_on=['HULLNUM','PERMIT'])
# Pull in species names
all_dat = pd.merge(all_dat, species, how='inner', on=['NESPP4'])
# Pull in gear types
all_dat = pd.merge(all_dat, gears, how='inner', left_on=['NEGEAR_y'], right_on=['NEGEAR'])
out_dat_path = os.path.join(Obs_path, 'NEFOP_CATCH_VES_SP_GEAR_noLoranBound.csv')
all_dat.to_csv(out_dat_path)
all_dat.head()


# In[12]:


for col in all_dat.columns: 
    print(col)


# In[13]:


out_path = os.path.join(Obs_path, 'Unique_trips_by_year_gear_noLoran.csv')
g = all_dat.groupby(['YEAR', 'GEAR NAME'])['TRIPID'].nunique()
g.to_csv(out_path)
g


# In[14]:


haulTimes = all_dat.groupby(['YEAR', 'GEAR NAME'])['HAULDUR'].mean()
haulTimes


# In[15]:


haulTimes2 = all_dat.groupby(['YEAR', 'GEAR NAME'])['HAULDUR'].median()
haulTimes2


# In[16]:


# Assess haul times only for last 5 years of the dataset to reflect the modern fishery
all_dat_term_6yr = all_dat[all_dat['YEAR'] > 2016]
haulTimes_term_6yr = all_dat_term_6yr.groupby(['GEAR NAME'])['HAULDUR'].mean()
haulTimes_term_6yr


# In[17]:


haulTimes2_term_6yr = all_dat_term_6yr.groupby(['GEAR NAME'])['HAULDUR'].median()
haulTimes2_term_6yr


# In[18]:


recent_haultimes = pd.merge(haulTimes_term_6yr, haulTimes2_term_6yr, how='inner', on=['GEAR NAME'])
recent_haultimes = recent_haultimes.rename(columns={'HAULDUR_x': 'Mean Haul Duration', 'HAULDUR_y': 'Median Haul Duration'}) 
recent_haultimes

# NOTE THESE TIMES ARE IN HOURS


# In[19]:


recent_haultimes.to_csv(os.path.join(Obs_path, 'gear_NEFOP_tow_lengths.csv'))

