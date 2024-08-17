#!/usr/bin/env python
# coding: utf-8

# In[3]:


# Script to spit out list of all trips in the joint NEFOP/AIS dataset so that we can remove these trips from the unseen dataset
import numpy as np
import pandas as pd
import os

# Change settings to showing 1000 rows
pd.options.display.max_rows=1000
pd.options.display.max_columns=100


# In[4]:


# Load all data
data_path = os.path.join(
    os.path.expanduser('~'),'Dropbox','My PC (DESKTOP-3PRD0P2)','Documents','CEC_project','Data_CEC_Project','Training_Data'
)
scal = pd.read_csv(os.path.join(data_path, 'all_scallop_trained.csv'))
gill = pd.read_csv(os.path.join(data_path, 'all_gill_trained.csv'))
trawl = pd.read_csv(os.path.join(data_path, 'all_trawl_trained.csv'))
clam = pd.read_csv(os.path.join(data_path, 'all_clam_trained.csv'))


# In[6]:


scal.head()


# In[10]:


# Extract list of trip IDs in each and combine into one list
scal_trips = scal['Trip_ID'].unique()
trawl_trips = trawl['Trip_ID'].unique()
clam_trips = clam['Trip_ID'].unique()
gill_trips = gill['Trip_ID'].unique()
all_seen_trips = np.concatenate([scal_trips, trawl_trips, clam_trips, gill_trips])
all_seen_trips_DF = pd.DataFrame(all_seen_trips)
all_seen_trips_DF.to_csv(os.path.join(data_path,"all_seen_trips.csv"))


# In[11]:


# Repeat but for list of vessels 
scal_vess = scal['PERMIT'].unique()
trawl_vess = trawl['PERMIT'].unique()
clam_vess = clam['PERMIT'].unique()
gill_vess = gill['PERMIT'].unique()
all_seen_vess = np.concatenate([scal_vess, trawl_vess, clam_vess, gill_vess])
all_seen_vess_DF = pd.DataFrame(all_seen_vess)
all_seen_vess_DF.to_csv(os.path.join(data_path,"all_seen_vessels.csv"))

