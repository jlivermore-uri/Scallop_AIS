#!/usr/bin/env python
# coding: utf-8

# In[1]:


# Connecting modeled data to landings and seeing what trips are missing

import numpy as np
import pandas as pd
import os, random
import datetime, time
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point
from geopandas import GeoDataFrame
import rasterio

# Change settings to show more rows & columns
pd.options.display.max_rows=100000
pd.options.display.max_columns=100


# In[2]:


# Set up workspace
out_path = '/work/pi_pengfei_liu_uri_edu/Scallop'
vms_path = '/work/pi_pengfei_liu_uri_edu/Scallop/VMS'
vtr_path = '/work/pi_pengfei_liu_uri_edu/Scallop/VTR'
land_path = '/work/pi_pengfei_liu_uri_edu/Scallop/Landings'


# In[3]:


# Work backwards from VTRs since that's our most complete dataset
vtr_15 = pd.read_csv(os.path.join(vtr_path, 'VTR_2015.txt'), sep='\\t', engine='python')
vtr_16 = pd.read_csv(os.path.join(vtr_path, 'VTR_2016.txt'), sep='\\t', engine='python')
vtr_17 = pd.read_csv(os.path.join(vtr_path, 'VTR_2017.txt'), sep='\\t', engine='python')
vtr_18 = pd.read_csv(os.path.join(vtr_path, 'VTR_2018.txt'), sep='\\t', engine='python')
vtrs = pd.concat([vtr_15, vtr_16, vtr_17, vtr_18])


# In[4]:


del(vtr_15)
del(vtr_16)
del(vtr_17)
del(vtr_18)


# In[5]:


# Isolate individual trips by VTR #
vtrs['Serial num'] = vtrs['Serial num'].astype(int)
vtrs['Supplier trip id'] = vtrs['Supplier trip id'].astype(int)

vtrs['VTR_NUMBER'] = np.where(vtrs['Serial num'].astype(str).str.len() == 8, vtrs['Serial num'], vtrs['Supplier trip id'])
vtr_numbers = vtrs[['VTR_NUMBER']]

# Note that this is for all vessels (not just those that we're focused on) by FMP or location


# In[6]:


# Now isolate to target vessels by pulling landings data, selecting applicable species caught, and targeting only federal trips"
all_land = pd.read_csv(os.path.join(land_path, 'all_land_2015-2018.csv'))
target_sp = ['MACKEREL, ATLANTIC', 'MACKEREL, ATLANTIC CHUB', 'SQUID, LONGFIN LOLIGO', 'SQUID, SHORTFIN ILLEX', 'BUTTERFISH', 'SCALLOP, SEA', 'CLAM, SURF, ATLANTIC', 'CLAM, QUAHOG, OCEAN', 'COD, ATLANTIC', 'HADDOCK', 'POLLOCK', 'REDFISH, ACADIAN', 'FLOUNDER, WINTER', 'FLOUNDER, WITCH', 'FLOUNDER, YELLOWTAIL', 'HAKE, RED', 'HAKE, SILVER', 'HALIBUT, ATLANTIC', 'WOLFFISH, ATLANTIC', 'HAKE, WHITE', 'HAKES, RED AND WHITE', 'FLOUNDER, AMERICAN PLAICE', 'FLOUNDER, WINDOWPANE', 'POUT, OCEAN', 'HAKE, OFFSHORE', 'HAKES, SILVER AND OFFSHORE', 'GOOSEFISH']
mask = all_land['Common Name'].isin(target_sp)
land_target_sp = all_land[mask]

# Drop unnecessary columns from VTRs\n",
vtrs = vtrs[['VTR_NUMBER','Fed ves permit','Latitude','Lat min','Lat sec','Longitude','Lon min','Lon sec','Area code','Date land','Cf name','State postal','Port name','Gear name','Start year','Start month','Start day']]

# Now connect relevant landings to VTRs to isolate federal trips
land_target_sp['Supplier Trip Id'] = land_target_sp['Supplier Trip Id'].astype(str)
vtrs['VTR_NUMBER'] = vtrs['VTR_NUMBER'].astype(str)
vtr_land_target_sp = vtrs.merge(land_target_sp, left_on='VTR_NUMBER', right_on='Supplier Trip Id')

# This dataset now contains landing data and VTR info for relevant trips
# We still have multiple dealer reports per trip - as we should for relevant cases
del(mask)


# In[7]:


vtr_land_target_sp['Common Name'].unique()


# In[8]:


del(all_land)


# In[9]:


# Now isolate only trips with locations that fall within the study area

# Create decimal degrees lat/lon columns
vtr_land_target_sp['Latitude'] = pd.to_numeric(vtr_land_target_sp['Latitude'], errors='coerce')
vtr_land_target_sp['Lat min'] = pd.to_numeric(vtr_land_target_sp['Lat min'], errors='coerce')
vtr_land_target_sp['Lat sec'] = pd.to_numeric(vtr_land_target_sp['Lat sec'], errors='coerce')
vtr_land_target_sp['Lat sec'].fillna(0, inplace=True)
vtr_land_target_sp['Longitude'] = pd.to_numeric(vtr_land_target_sp['Longitude'], errors='coerce')
vtr_land_target_sp['Lon min'] = pd.to_numeric(vtr_land_target_sp['Lon min'], errors='coerce')
vtr_land_target_sp['Lon sec'] = pd.to_numeric(vtr_land_target_sp['Lon sec'], errors='coerce')
vtr_land_target_sp['Lon sec'].fillna(0, inplace=True)

vtr_land_target_sp['LAT'] = vtr_land_target_sp['Latitude'] + (vtr_land_target_sp['Lat min']/60) + (vtr_land_target_sp['Lat sec']/3600)
vtr_land_target_sp['LON'] = vtr_land_target_sp['Longitude'] + (vtr_land_target_sp['Lon min']/60) + (vtr_land_target_sp['Lon sec']/3600)


# In[10]:


vtr_land_target_sp.head()


# In[11]:


# Make a backup (not spatially clipped version) for checks later on
vtr_land_target_sp_backup = vtr_land_target_sp

# Map bounds from RFP: -72.45 - -69.59 W and 40.1 - 42.1 N
vtr_land_target_sp = vtr_land_target_sp[(vtr_land_target_sp['LAT'] >= 40.1) & (vtr_land_target_sp['LAT'] <= 42.1)]
vtr_land_target_sp = vtr_land_target_sp[(vtr_land_target_sp['LON'] >= 69.59) & (vtr_land_target_sp['LON'] <= 72.45)]

vtr_land_target_sp['VTR_NUMBER'].nunique()


# In[12]:


# Still need a dataset of trips by FMP
smb = ['MACKEREL, ATLANTIC', 'MACKEREL, ATLANTIC CHUB', 'SQUID, LONGFIN LOLIGO', 'SQUID, SHORTFIN ILLEX', 'BUTTERFISH']
scoq = ['CLAM, SURF, ATLANTIC', 'CLAM, QUAHOG, OCEAN']
nemulti = ['COD, ATLANTIC', 'HADDOCK', 'POLLOCK', 'REDFISH, ACADIAN', 'FLOUNDER, WINTER', 'FLOUNDER, WITCH', 'FLOUNDER, YELLOWTAIL',
           'HALIBUT, ATLANTIC', 'WOLFFISH, ATLANTIC', 'HAKE, WHITE', 'FLOUNDER, AMERICAN PLAICE', 'FLOUNDER, WINDOWPANE', 'POUT, OCEAN']
nesmmulti = ['HAKE, RED', 'HAKE, SILVER', 'HAKE, OFFSHORE', 'HAKES, SILVER AND OFFSHORE', 'HAKES, RED AND WHITE']
scallop_trips = vtr_land_target_sp[vtr_land_target_sp['Common Name'] == 'SCALLOP, SEA']
monk_trips =  vtr_land_target_sp[vtr_land_target_sp['Common Name'] == 'GOOSEFISH']
nemulti_trips = vtr_land_target_sp[vtr_land_target_sp['Common Name'].isin(nemulti)]
nesmmulti_trips = vtr_land_target_sp[vtr_land_target_sp['Common Name'].isin(nesmmulti)]
smb_trips = vtr_land_target_sp[vtr_land_target_sp['Common Name'].isin(smb)]
scoq_trips = vtr_land_target_sp[vtr_land_target_sp['Common Name'].isin(scoq)]

# # Save all trip lists
scallop_trips.to_csv(os.path.join(out_path,'scallop_ALL_vtr_trips.csv'),index=False)
monk_trips.to_csv(os.path.join(out_path,'monk_ALL_vtr_trips.csv'),index=False)
nemulti_trips.to_csv(os.path.join(out_path,'nemulti_ALL_vtr_trips.csv'),index=False)
nesmmulti_trips.to_csv(os.path.join(out_path,'nesmmulti_ALL_vtr_trips.csv'),index=False)
smb_trips.to_csv(os.path.join(out_path,'smb_ALL_vtr_trips.csv'),index=False)
scoq_trips.to_csv(os.path.join(out_path,'scoq_ALL_vtr_trips.csv'),index=False)

# Also save one new searchable list with an FMP column added
scallop_trips = scallop_trips.assign(FMP = 'Scallop')
monk_trips = monk_trips.assign(FMP = 'Monkfish')
nemulti_trips = nemulti_trips.assign(FMP = 'NE Multisp')
nesmmulti_trips = nesmmulti_trips.assign(FMP = 'NE SM Multisp')
smb_trips = smb_trips.assign(FMP = 'SMB')
scoq_trips = scoq_trips.assign(FMP = 'SQOC')

totalTrips = pd.concat([scallop_trips, monk_trips, nemulti_trips, nesmmulti_trips, smb_trips, scoq_trips])
totalTrips.to_csv(os.path.join(out_path,'ALL_FMP_vtr_trips.csv'),index=False)


# In[13]:


scallop_trips['VTR_NUMBER'].nunique()


# In[14]:


# Now determine how many trips in the VTR show up in the AIS seen + unseen dataset 
scalAISdat = pd.read_csv(os.path.join(out_path, 'scallop_pt_values_AIS.csv'))
scalTrips = scallop_trips['VTR_NUMBER'].unique().astype(int)

coveredScal = scalAISdat[scalAISdat['VTR_NUMBER'].astype(int).isin(scalTrips)]
coveredScal = coveredScal.drop_duplicates()


# In[15]:


scal_trips_AIS_in_VTR = coveredScal['VTR_NUMBER'].unique()
len(scal_trips_AIS_in_VTR)


# In[16]:


scal_trips_AIS_in_VTR = pd.DataFrame(scal_trips_AIS_in_VTR)
scal_trips_AIS_in_VTR.to_csv(os.path.join(out_path,'scal_trips_with_AIS_in_VTR.csv'),index=False)


# In[17]:


# Now isolate the trips NOT covered in the AIS
scal_not_covered = np.setdiff1d(scalTrips,scalAISdat['VTR_NUMBER'])
del(scalAISdat)
len(scal_not_covered)


# In[18]:


scal_not_covered_VTRs = scallop_trips[scallop_trips['VTR_NUMBER'].astype(int).isin(scal_not_covered)]
scal_not_covered_VTRs['Date sail'] = scal_not_covered_VTRs['Start year'].astype(str) + '-' + scal_not_covered_VTRs['Start month'].astype(str) + '-' + scal_not_covered_VTRs['Start day'].astype(str)
scal_not_covered_VTRs = scal_not_covered_VTRs[['VTR_NUMBER','Fed ves permit','Latitude','LAT','LON','Date land','Date sail']]
scal_not_covered_VTRs = scal_not_covered_VTRs.drop_duplicates(ignore_index=True)
scal_not_covered_VTRs.head()


# In[19]:


# ISSUE: I'm picking trips that landed scallops, not just those that targeted. Not sure it's a fair comparison ???
# We want to include ALL scallop landings, from trips targeting as well as any bycatch in terms of developing the most comprehensive data product. 
# However, this makes comparison of AIS coverage to all trips catching scallop unfair. 

# VTRs do not include target species, and we can't separate trips by license because they have many permits and don't declare which they're using. 
# VMS declarations exist, but they can DOF on the same trip as doing something else. Better to check what they landed.


# In[20]:


# Load VMS
# all_vms = []
    
# for newFile in os.listdir(vms_path):
#    if newFile.endswith('_file.csv'):
#        print(newFile)       
#        thisMonth = pd.read_csv(os.path.join(vms_path, newFile))
#        all_vms.append(thisMonth)
    
# #Save the gear files
# all_vms = pd.concat(all_vms)
# all_vms.to_csv(os.path.join(vms_path,'all_vms_2015-2018.csv'))

# Read in file if already built from previous run
all_vms = pd.read_csv(os.path.join(vms_path, 'all_vms_2015-2018.csv'), engine='python')

# Source data has some duplicate timestamps so drop any duplicates
all_vms = all_vms.drop_duplicates()

all_vms.head()


# In[21]:


# Match VMS (all_vms) to data that doesn't have AIS coverage (scal_not_covered)
all_vms['utc_Date']=pd.to_datetime(all_vms['utc_Date'])
all_vms['permit']=all_vms['permit'].astype(str)
scal_not_covered_VTRs['Date sail']=pd.to_datetime(scal_not_covered_VTRs['Date sail'])
scal_not_covered_VTRs['Date land']=pd.to_datetime(scal_not_covered_VTRs['Date land'], format='%d-%b-%y')
scal_not_covered_VTRs['Fed ves permit']=scal_not_covered_VTRs['Fed ves permit'].astype(str)

# Merge on permit number (will end up with temporal mismatches here)
scal_vms_covered = all_vms.merge(scal_not_covered_VTRs, left_on='permit', right_on='Fed ves permit')


# In[22]:


scal_vms_covered.head()
scal_vms_covered.dtypes


# In[23]:


scal_vms_covered2 = scal_vms_covered

# Drop faster speed points (>4 knots for most species, except scallop which has a 5 knot cutoff)
scal_vms_covered2 = scal_vms_covered2[(scal_vms_covered2['avg_speed']<=5)]

# Now remove temporal mismatches
scal_vms_covered2 = scal_vms_covered2[(scal_vms_covered2['utc_Date']>=scal_vms_covered2['Date sail']) & (scal_vms_covered2['utc_Date']<=scal_vms_covered2['Date land'])]

# Drop VMS points that fall within state waters because fishing activity being attributed to ports. Further, VERY little activity attributed to state waters in AIS model or VTRs
fedWaters = gpd.read_file(os.path.join(out_path,'Federal_Waters_Only.shp'))
fedWaters = fedWaters.to_crs('EPSG:4326')

points = gpd.GeoDataFrame(scal_vms_covered2, geometry=gpd.points_from_xy(scal_vms_covered2.long, scal_vms_covered2.lat), crs='EPSG:4326')

within_points = gpd.sjoin(points, fedWaters, predicate='within')

scal_vms_covered2 = pd.DataFrame(within_points)
scal_vms_covered2.head()


# In[24]:


base = fedWaters.plot()
points.plot(ax=base, marker='o', color='red')


# In[25]:


# Delete unneeded dataframe to free up memory
del(scoq_trips)
del(smb_trips)
del(nemulti_trips)
del(nesmmulti_trips)
del(monk_trips)
del(vtrs)


# In[26]:


# Now add landings information in
vtr_land_target_sp = vtr_land_target_sp.drop_duplicates(ignore_index=True)
scal_vms_land = scal_vms_covered2.merge(vtr_land_target_sp, left_on='VTR_NUMBER', right_on='VTR_NUMBER')
scal_vms_land.head()


# In[27]:


# Need to distribute fishing value (within species and grade) across VMS points in a fishing trip 
# Doing even distribution 
# Following same method from AIS approach in Scallop_data_cleanup_to_landings_cluster.ipynb

# Make sure all points fall within the study area - map bounds from RFP: -72.45 - -69.59 W and 40.1 - 42.1 N
scal_vms_land = scal_vms_land[(scal_vms_land['long']>=-72.45) & (scal_vms_land['long']<=-69.59)]
scal_vms_land = scal_vms_land[(scal_vms_land['lat']>=40.1) & (scal_vms_land['lat']<=42.1)]

# Ensure we don't have any duplicate timestamps in the VMS
scal_vms_land = scal_vms_land.drop_duplicates()

# Make sure we're only looking at Scallop values
scal_vms_land = scal_vms_land[(scal_vms_land['Common Name']=='SCALLOP, SEA')]

scal_vms_land['VTR_NUMBER'].nunique()


# In[28]:


# Identify number of VMS locations on each trip
scal_vms_land['UniqueTripTime'] = scal_vms_land['VTR_NUMBER'].astype(str) + scal_vms_land['utc_Date'].astype(str)

# Found a few VMS trips with duplicate timestamps so correct this first
scal_vms_land['DuplicateTimeCheck'] = scal_vms_land['VTR_NUMBER'].astype(str) + scal_vms_land['utc_Date'].astype(str) + scal_vms_land['Dollars'].astype(str) + scal_vms_land['Market desc'].astype(str)
scal_vms_land = scal_vms_land.drop_duplicates(subset=['DuplicateTimeCheck'])

# Now calculate the number of VMS points per trip and divide dollars by that value
scal_vms_land['Num_Landing'] = scal_vms_land.UniqueTripTime.map(scal_vms_land.UniqueTripTime.value_counts())
scal_vms_land['All_Pts_Num'] = scal_vms_land.VTR_NUMBER.map(scal_vms_land.VTR_NUMBER.value_counts())
scal_vms_land['Num_Pts'] = scal_vms_land['All_Pts_Num']/scal_vms_land['Num_Landing']
scal_vms_land.head()


# In[29]:


# Generate point 'value' by dividing ex-vessel value by number of points per trip
scal_vms_land['Point_Value'] = scal_vms_land['Dollars'] / scal_vms_land['Num_Pts']
scal_vms_land['location_source'] = 'VMS'
scal_vms_land = scal_vms_land[['location_source','permit','utc_Date','lat','long','VTR_NUMBER','Date sail','Date land_x',
                               'State postal','Port','Gear name_x','Common Name','Point_Value','Dollars','Num_Pts']]
scal_vms_land.rename(columns={'Gear name_x': 'Gear', 'permit': 'Permit', 'Date sail': 'Date_Sail', 'Date land_x': 'Date_Land', 
                              'State postal': 'State_landed', 'Port': 'Port_landed', 'utc_Date': 'Timestamp', 'lat': 'LAT', 
                              'long': 'LON','Dollars': 'VTR_Dollars'}, inplace=True)
scal_vms_land.head()


# In[30]:


# Test a few random trips to make sure they add up correctly - run this a bunch of times to make sure it always checks out

scal_vms_land['VTR_NUMBER'] = scal_vms_land['VTR_NUMBER'].astype(str)
scallop_trips['VTR_NUMBER'] = scallop_trips['VTR_NUMBER'].astype(str)
randomTrip = scal_vms_land['VTR_NUMBER'].sample().astype(str)
randomTripVal = randomTrip.tolist()
randomTripVal = randomTripVal[0]

print('Random VTR Number: ' + randomTripVal)
randomTrip_vals = scal_vms_land[(scal_vms_land['VTR_NUMBER']==randomTripVal)]
print('Point total from VMS: '+ randomTrip_vals['Point_Value'].sum().astype(str))

# Pull relevant VTR
randomVTR = scallop_trips[(scallop_trips['VTR_NUMBER']==randomTripVal)].drop_duplicates(ignore_index=True)
print('Trip value from VTR: '+ randomVTR['Dollars'].sum().astype(str))


# In[31]:


#randomTrip_vals


# In[32]:


#randomVTR


# In[33]:


scal_vms_land.to_csv(os.path.join(out_path,'scallop_pt_values_VMS.csv'))
scal_vms_land['Lbs'] = 'Not needed here'
scal_vms_land['Grade'] = 'Not needed here'


# In[34]:


# Fallback to VTRs
uncovered_VTRs = np.setdiff1d(scal_not_covered_VTRs['VTR_NUMBER'],scal_vms_land['VTR_NUMBER'])
uncovered_VTRs_land = vtr_land_target_sp[vtr_land_target_sp['VTR_NUMBER'].astype(str).isin(uncovered_VTRs)]
uncovered_VTRs_land.head()


# In[35]:


# Add AIS and VMS datasets together

# Bring in the AIS point data
scal_ais_pts = pd.read_csv(os.path.join(out_path, 'scallop_pt_values_AIS.csv'))
scal_ais_pts['location_source'] = 'AIS'
scal_ais_pts.head()


# In[36]:



# Clean up the datasets (make same columns) so they can be concatenated
scal_ais_pts = scal_ais_pts[['location_source','Permit','Datetime','LAT','LON','VTR_NUMBER','Date_Sail','Date_Land',
                             'State Postal','Port','Gear name','Common Name','Point_Value','Dollars','Num_Pts']]
scal_ais_pts.rename(columns={'Gear name': 'Gear', 'Date sail': 'Date_Sail', 'Date land_x': 'Date_Land', 
                             'State Postal': 'State_landed', 'Port': 'Port_landed', 'Datetime': 'Timestamp',
                             'Dollars': 'VTR_Dollars'}, inplace=True)
scal_ais_pts['Lbs'] = 'Not needed here'
scal_ais_pts['Grade'] = 'Not needed here'
uncovered_VTRs_land['location_source'] = 'VTR'
uncovered_VTRs_land['Timestamp'] = ''
uncovered_VTRs_land['Date_Sail'] = uncovered_VTRs_land['Start year'].astype(str) + '-' + uncovered_VTRs_land['Start month'].astype(str) + '-' + uncovered_VTRs_land['Start day'].astype(str)
uncovered_VTRs_land['Date_Sail']=pd.to_datetime(uncovered_VTRs_land['Date_Sail'])
uncovered_VTRs_land['Date_Land']=pd.to_datetime(uncovered_VTRs_land['Date land'], format='%d-%b-%y')
uncovered_VTRs_land = uncovered_VTRs_land[['location_source','Fed ves permit','Timestamp','LAT','LON','VTR_NUMBER','Date_Sail','Date_Land',
                             'State Postal','Port','Gear name_x','Common Name','Dollars','Landed Lbs','Grade desc']]
uncovered_VTRs_land.rename(columns={'Gear name_x': 'Gear', 'State Postal': 'State_landed', 'Port': 'Port_landed',
                                    'Dollars': 'Point_Value', 'Fed ves permit': 'Permit', 'Landed Lbs': 'Lbs', 'Grade desc': 'Grade'}, inplace=True)

# Combine AIS and VMS for saving later
to_combine = [scal_ais_pts, scal_vms_land]  
Scal_AIS_VMS = pd.concat(to_combine)

# Combine all datasets just for summarizing at trip level (e.g., number of trips per dataset by year)
to_combine2 = [scal_ais_pts, scal_vms_land, uncovered_VTRs_land]  
ALL_SCALLOP = pd.concat(to_combine2)
ALL_SCALLOP.head()


# In[37]:


uncovered_VTRs_land.to_csv(os.path.join(out_path,'scallop_pts_uncovered_VTR.csv'))


# In[38]:


# Testing for trips that may have a unique situation
# NOTE: THE UNIQUE VTR NUMBER FOR THIS TRIP WITH AN ISSUE HAS BEEN REPLACED WITH XXXXXXXX IN THE CODE
# DUE TO CONFIDENTIALITY REQUIREMENTS
#test_vtr = ALL_SCALLOP[(ALL_SCALLOP['VTR_NUMBER']==XXXXXXXX)].drop_duplicates(ignore_index=True)
test_vtr['Point_Value'].sum()


# In[39]:


#test_vtr_trip = scallop_trips[scallop_trips['VTR_NUMBER'] == XXXXXXXX]
#test_vtr_trip
# THIS TRIP IS NOT IN THE VTRS
# Plot out and see if this doesn't fall in study area??? Could have AIS or VMS in study area but the VTR point reported isn't.


# In[40]:


plt.plot(test_vtr['LON'], test_vtr['LAT'], 'bo')


# In[41]:


# Check FULL VTR dataset to see where reported point is located 
vtr_land_target_sp_backup_TEST = vtr_land_target_sp_backup[vtr_land_target_sp_backup['VTR_NUMBER'] == 'XXXXXXXX']
vtr_land_target_sp_backup_TEST['Dollars'].sum()
# This confirms the issue - this is the same sum as the combined data product 


# In[42]:


# Map bounds from RFP: -72.45 - -69.59 W and 40.1 - 42.1 N
# In the example we pulled here, the VTR reported location is not within the study area, while the AIS falls partially within it. 
# VTR location reported was: -72.483333, 40.333333 (this is west of the study area)
vtr_land_target_sp_backup_TEST


# In[43]:


# Delete all rows in Scal_AIS_VMS where the VTR number doesn't occur in the scallop_trips list from the VTRs
Scal_AIS_VMS['VTR_NUMBER'] = Scal_AIS_VMS['VTR_NUMBER'].astype(str)
scallop_trips['VTR_NUMBER'] = scallop_trips['VTR_NUMBER'].astype(str)

mask3 = Scal_AIS_VMS['VTR_NUMBER'].isin(scallop_trips['VTR_NUMBER'].astype(str))
Scal_AIS_VMS2 = Scal_AIS_VMS[mask3]
Scal_AIS_VMS2.head()


# In[44]:


Scal_AIS_VMS2.to_csv(os.path.join(out_path,'scallop_pt_values_AIS+VMS_datasets.csv'))


# In[45]:


# Combine all datasets just for summarizing at trip level (e.g., number of trips per dataset by year)
to_combine2 = [Scal_AIS_VMS2, uncovered_VTRs_land]  
ALL_SCALLOP2 = pd.concat(to_combine2)
ALL_SCALLOP2.head()
#ALL_SCALLOP2['Common Name'].unique()


# In[46]:


ALL_SCALLOP2 = ALL_SCALLOP2[(ALL_SCALLOP2['Common Name']=='SCALLOP, SEA')]


# In[47]:


# Finally group data to determine trips covered by AIS, NEFOP, VMS, and VTR by year
ALL_SCALLOP2.groupby('location_source')['VTR_NUMBER'].nunique()

# This is including ALL trips that had scallop in their landings, not just trips targetting scallops


# In[48]:


ALL_SCALLOP2['Year'] = [x[:4] for x in ALL_SCALLOP2['Date_Land'].astype(str)]
ALL_SCALLOP2.groupby(['location_source', 'Year'])['VTR_NUMBER'].nunique()


# In[49]:


scal_trip_breakdown = ALL_SCALLOP2[['location_source','Permit','Year','VTR_NUMBER']]
scal_trip_breakdown = scal_trip_breakdown.drop_duplicates(ignore_index=True)
scal_trip_breakdown.to_csv(os.path.join(out_path,'scallop_trips_by_dataset.csv'))
ALL_SCALLOP2.to_csv(os.path.join(out_path,'scallop_trips_by_dataset_with_vals.csv'))
scal_trip_breakdown.head()


# In[50]:


# Check to verify that each VTR number shows up with only a single Location Source
ALL_SCALLOP2.groupby(['VTR_NUMBER'])['location_source'].nunique().describe()
# Each trip is accounted for only once (meaning in only 1 of 3 data sources) - this checks out


# In[51]:


# Next script compiles corresponding VTR data from NEFSC rasters (Scallop_VTR_compiling.ipynb)
# Following step is to combine convert points to raster dataset in ArcGIS (Point to Raster (Conversion)) and combine with VTR raster data (Mapping.ipynb)
# Can't run ArcPy from the cluster so this must be done externally from Python code

