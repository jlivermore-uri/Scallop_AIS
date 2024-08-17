#!/usr/bin/env python
# coding: utf-8

# In[1]:


# Testing model configurations with training data
import numpy as np
import pandas as pd
import os, random
import datetime, time
import glob
import matplotlib.pyplot as plt
import seaborn as sns
#%pylab inline - insert this above if the image doesn't show up at the bottom

#Import Random Forest Model
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
#Import scikit-learn metrics module for accuracy calculation
from sklearn import metrics
# Import regression from scikit-learn
from sklearn.linear_model import LinearRegression
import statsmodels.api as sm

# Change settings to showing 1000 rows
pd.options.display.max_rows=100000
pd.options.display.max_columns=100


# In[2]:


# Set up workspace
trained_path = '/home/jlivermore_uri_edu/Scallop/Trained'
unseen_path = '/home/jlivermore_uri_edu/Scallop/Unseen'


# In[3]:


# Load trained scallop data and remove rows where there are NA values in any of the features
scal_trained = pd.read_csv(os.path.join(trained_path, 'all_scallop_trained.csv'))
scal_trained = scal_trained.dropna()


# In[4]:


scal_trained.head()


# In[5]:


scal_trained['NEFOP_Fishing'].unique()
# If values other than 0s and 1s, means that in the NEFOP data there are consecutive starts and ends.
# Looks good to proceed here.


# In[6]:


# Describe data for write-up
scal_trained.describe()

# Number of rows
print("Number of rows: " + str(len(scal_trained)))
# Number of trips
print("Number of trips: "+ str(scal_trained.Trip_ID.nunique()))
# Number of vessels (permits)
print("Number of vessels (permits): "+ str(scal_trained.PERMIT.nunique()))


# In[7]:


# Data prep for RF
modDat = scal_trained[['NEFOP_Fishing','SOG_Avg','Crow_flies_km','SOG_Std','Depth_Avg','Depth_Std',
                       'COG_Avg_Abs_d','d_COG_StartEnd','Month','Weekday','Moon']]

dummies = pd.get_dummies(modDat[['Month', 'Weekday', 'NEFOP_Fishing']])
y = modDat.NEFOP_Fishing.astype('int64')
X_ = modDat.drop(['Month','Weekday', 'NEFOP_Fishing'], axis = 1).astype('float64')
X = pd.concat([X_, dummies[['Month', 'Weekday']]], axis = 1)

X.info()


# In[8]:


# Split data into training and test sets
X_train, X_test , y_train, y_test = train_test_split(X, y, test_size=0.1) # 90% training and 10% test


# In[9]:


# Run tuned model on full training dataset (see Scallop_RF_model.ipynb for model training and tuning)
# Using earlier full dataset train and test prep (see cell 8)
clf2=RandomForestClassifier(n_estimators=500, # Max number of trees
                            oob_score=True,
                            max_depth=40, # Max tree depth is 40
                            n_jobs=24) # 24 is the number of cores being used
clf2.fit(X_train,y_train)
y_pred=clf2.predict(X_test)
oob_error = 1 - clf2.oob_score_
print(f'OOB error: {oob_error:.3f}')
print("Accuracy (% Correct):",metrics.accuracy_score(y_test, y_pred))
print("Balanced Accuracy:",metrics.balanced_accuracy_score(y_test, y_pred))
cm = metrics.confusion_matrix(y_test, y_pred)
disp = metrics.ConfusionMatrixDisplay(confusion_matrix=cm)
disp.plot()

# Set number of trees to 500 and max depth to 40. Left all 10 features in instead of dropping one.


# In[10]:


# Read in full scallop dataset
# Loop through the generated files and sort out by gear used (these will be the model input files)
all_unseen_scal = []

for newFile in os.listdir(unseen_path):
    if newFile.endswith("unseen_boats.csv"):
        print(newFile)       
        loopDay=pd.read_csv(os.path.join(unseen_path, newFile))
        scallop = loopDay[(loopDay['Gear'] == 'scallop')].copy(deep=True)

        if len(scallop) > 0:
            all_unseen_scal.append(scallop)

# Save the gear files
all_unseen_scal = pd.concat(all_unseen_scal)


# In[13]:


# Prep data for model
all_unseen_scal=all_unseen_scal.dropna()
dummies = pd.get_dummies(all_unseen_scal[['Month', 'Weekday']])
X_intermed = all_unseen_scal.drop(['Month','Weekday'], axis = 1)
X_scal = pd.concat([X_intermed, dummies[['Month', 'Weekday']]], axis = 1)
unseen_scal_X = all_unseen_scal[['SOG_Avg','Crow_flies_km','SOG_Std','Depth_Avg','Depth_Std',
                               'COG_Avg_Abs_d','d_COG_StartEnd','Moon','Month','Weekday']]
unseen_scal_X


# In[14]:


scal_pred=clf2.predict(unseen_scal_X)
all_unseen_scal['Predict_Fishing'] = scal_pred
#all_unseen_scal.head()


# In[ ]:


all_unseen_scal.to_csv(os.path.join(unseen_path, 'scallop_unseen_inference.csv'))
# Next step is to merge all data (seen and unseen together) for mapping/connecting to landings


# In[ ]:




