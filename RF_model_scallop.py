#!/usr/bin/env python
# coding: utf-8

# In[2]:


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


# In[3]:


# Set up workspace
data_path = os.path.join(
    os.path.expanduser('~'),'Dropbox','My PC (DESKTOP-3PRD0P2)','Documents','CEC_project','Data_CEC_Project','Training_Data'
)


# In[4]:


# Load scallop data and remove rows where there are NA values in any of the features
scal = pd.read_csv(os.path.join(data_path, 'all_scallop_trained.csv'))
scal = scal.dropna()


# In[5]:


# scal.head()


# In[6]:


scal['NEFOP_Fishing'].unique()
# If values other than 0s and 1s, means that in the NEFOP data there are consecutive starts and ends.
# Looks good to proceed here.


# In[7]:


# Describe data for write-up
scal.describe()

# Number of rows
print("Number of rows: " + str(len(scal)))
# Number of trips
print("Number of trips: "+ str(scal.Trip_ID.nunique()))
# Number of vessels (permits)
print("Number of vessels (permits): "+ str(scal.PERMIT.nunique()))


# In[8]:


# Take random subset of data (pulled 50 trips - <10% of data) for initial testing 
# Commented out after initial testing
# trips = scal['Trip_ID'].unique()
# print(len(trips))
# sel_trips = np.random.choice(a=trips,size=50)
# sel_scal = scal[scal.Trip_ID.isin(sel_trips)]
# sel_scal.head()


# In[5]:


# Data prep for RF
modDat = scal[['NEFOP_Fishing','SOG_Avg','Crow_flies_km',
               'SOG_Std','Depth_Avg','Depth_Std',
               'COG_Avg_Abs_d','d_COG_StartEnd',
               'Month','Weekday','Moon']]

dummies = pd.get_dummies(modDat[['Month', 'Weekday', 'NEFOP_Fishing']])
y = modDat.NEFOP_Fishing.astype('int64')
X_ = modDat.drop(['Month','Weekday', 'NEFOP_Fishing'], axis = 1).astype('float64')
X = pd.concat([X_, dummies[['Month', 'Weekday']]], axis = 1)

X.info()


# In[8]:


# For intitial testing, 
# Split data into training and test sets
X_train, X_test , y_train, y_test = train_test_split(X, y, test_size=0.1) # 90% training and 10% test


# In[9]:


# Train on training set and perform predictions on the test set

#Create a Gaussian Classifier
clf=RandomForestClassifier(n_estimators=100, 
                           oob_score=True)
# Name clf as model instead moving forward

#Train the model using the training sets
clf.fit(X_train,y_train)

y_pred=clf.predict(X_test)


# In[10]:


# Get the OOB error 
oob_error = 1 - clf.oob_score_
# Print the OOB error
print(f'OOB error: {oob_error:.3f}')


# In[11]:


# Test prediction accuracy

# Model Accuracy: % Correct Predictions
print("Accuracy (% Correct):",metrics.accuracy_score(y_test, y_pred))

# Balanced Model Accuracy: 0.5((TP/(TP+FN) + TN/(TN+FP)))
print("Balanced Accuracy:",metrics.balanced_accuracy_score(y_test, y_pred))

# Confusion Matrix
cm = metrics.confusion_matrix(y_test, y_pred)
disp = metrics.ConfusionMatrixDisplay(confusion_matrix=cm)
disp.plot()


# In[14]:


feature_imp = pd.Series(clf.feature_importances_,index=X.columns).sort_values(ascending=False)
feature_imp


# In[15]:


# Creating a bar plot
sns.barplot(x=feature_imp, y=feature_imp.index)
# Add labels to your graph
plt.xlabel('Feature Importance Score')
plt.ylabel('Features')
plt.title("Visualizing Important Features")
plt.legend()
plt.show()
plt.savefig(os.path.join(os.path.expanduser('~'),'Dropbox','My PC (DESKTOP-3PRD0P2)','Documents','CEC_project','Data_CEC_Project','Model_Outputs','Scallop_RF_feat_imp.png'), dpi=300, bbox_inches='tight')


# In[16]:


# Why is crow flies so important? They're doing ovals/circles often? Shorter distance may be indicative of fishing 
# Run regression on features to see the coefficient on crow flies - get at direction of prediction
y = scal[['NEFOP_Fishing']].astype('int64')
X = scal[['SOG_Avg','Crow_flies_km',
          'SOG_Std','Depth_Avg','Depth_Std',
          'COG_Avg_Abs_d','d_COG_StartEnd', 
          'Month','Weekday','Moon']]
reg = LinearRegression().fit(X,y)
X = sm.add_constant(X) # Adding a constant for the intercept in sm
regModel = sm.OLS(y, X).fit()
print(regModel.summary())


# In[17]:


# Hyperparameter tuning - start with number of trees
from sklearn.metrics import roc_curve, auc
false_positive_rate, true_positive_rate, thresholds = roc_curve(y_test, y_pred)
roc_auc = auc(false_positive_rate, true_positive_rate)
roc_auc

n_estimators = [100,500,1000,2000]
train_results = []
test_results = []
for estimator in n_estimators:
   rf = RandomForestClassifier(n_estimators=estimator, n_jobs=-1)
   rf.fit(X_train, y_train)
   train_pred = rf.predict(X_train)
   false_positive_rate, true_positive_rate, thresholds = roc_curve(y_train, train_pred)
   roc_auc = auc(false_positive_rate, true_positive_rate)
   train_results.append(roc_auc)
   y_pred = rf.predict(X_test)
   false_positive_rate, true_positive_rate, thresholds = roc_curve(y_test, y_pred)
   roc_auc = auc(false_positive_rate, true_positive_rate)
   test_results.append(roc_auc)
from matplotlib.legend_handler import HandlerLine2D
line1, = plt.plot(n_estimators, train_results, color="blue", label="Train AUC")
line2, = plt.plot(n_estimators, test_results, color="red", label="Test AUC")
plt.legend(handler_map={line1: HandlerLine2D(numpoints=2)})
plt.ylabel("AUC score")
plt.xlabel("n_estimators")
plt.show()

# Looks like AUC plateaus at 500 and is already performing well 
# Python default condition is 100 estimators


# In[23]:


# Tuning tree depth hyperparameter
max_depths = np.linspace(1, 32, 32, endpoint=True)
train_results = []
test_results = []
for max_depth in max_depths:
   rf = RandomForestClassifier(max_depth=max_depth, n_jobs=-1)
   rf.fit(X_train, y_train)
   train_pred = rf.predict(X_train)
   false_positive_rate, true_positive_rate, thresholds = roc_curve(y_train, train_pred)
   roc_auc = auc(false_positive_rate, true_positive_rate)
   train_results.append(roc_auc)
   y_pred = rf.predict(X_test)
   false_positive_rate, true_positive_rate, thresholds = roc_curve(y_test, y_pred)
   roc_auc = auc(false_positive_rate, true_positive_rate)
   test_results.append(roc_auc)
from matplotlib.legend_handler import HandlerLine2D
line1, = plt.plot(max_depths, train_results, 'b', label='Train AUC')
line2, = plt.plot(max_depths, test_results, 'r', label='Test AUC')
plt.legend(handler_map={line1: HandlerLine2D(numpoints=2)})
plt.ylabel('AUC Score')
plt.xlabel('Tree depth')
plt.show()

# Test dataset AUC plateaus around 35
# Python default is no max tree depth - but that is likely overfitting the data


# In[12]:


from sklearn.feature_selection import RFECV
rfe = RFECV(clf,cv=5) # 5-fold cross validation
rfe.fit(X_train,y_train)


# In[13]:


#selected_features = np.array(features)[rfe.get_support()]
#rfe.support_
#selector.ranking_
print('Optimal number of features: {}'.format(rfe.n_features_))
plt.figure(figsize=(16, 9))
plt.title('Recursive Feature Elimination with Cross-Validation', fontsize=18, fontweight='bold', pad=20)
plt.xlabel('Number of features selected', fontsize=14, labelpad=20)
plt.ylabel('% Correct Classification', fontsize=14, labelpad=20)
plt.plot(range(1, len(rfe.grid_scores_) + 1), rfe.grid_scores_, color='#303F9F', linewidth=3)
plt.show()

# Suggests we should include all features


# In[14]:


corrmat = modDat.corr()
top_corr_features = corrmat.index
plt.figure(figsize=(20,20))
#plot heat map
g=sns.heatmap(modDat[top_corr_features].corr(),annot=True,cmap="RdYlGn")


# In[15]:


# If OOS prediciton is better, then we don't need to drop variables. 
# No theoretical reason to remove any of them and model performance was worse without it


# In[16]:


# Run tuned model on full training dataset
# Using earlier full dataset train and test prep (see cell 8)
clf2=RandomForestClassifier(n_estimators=500, 
                            oob_score=True,
                            max_depth=40)
clf2.fit(X_train,y_train)
y2_pred=clf2.predict(X_test)
oob_error = 1 - clf2.oob_score_
print(f'OOB error: {oob_error:.3f}')
print("Accuracy (% Correct):",metrics.accuracy_score(y_test, y_pred))
print("Balanced Accuracy:",metrics.balanced_accuracy_score(y_test, y_pred))
cm = metrics.confusion_matrix(y_test, y_pred)
disp = metrics.ConfusionMatrixDisplay(confusion_matrix=cm)
disp.plot()

# Set number of trees to 500 and max depth to 40. Left all 10 features in instead of dropping one.


# In[ ]:


# Read in full scallop dataset
unseen_path = os.path.join(
    os.path.expanduser('~'),'Dropbox','My PC (DESKTOP-3PRD0P2)','Documents','CEC_project',
    'Data_CEC_Project','AIS','FV_only','Unseen')
all_unseen_scal=pd.read_csv(os.path.join(unseen_path, 'all_scallop_2015-2018.csv'))
all_unseen_scal


# In[ ]:


# Prep data for model
all_unseen_scal=all_unseen_scal.dropna()
dummies = pd.get_dummies(all_unseen_scal[['Month', 'Weekday']])
X_intermed = all_unseen_scal.drop(['Month','Weekday'], axis = 1)
X_scal = pd.concat([X_intermed, dummies[['Month', 'Weekday']]], axis = 1)
unseen_scal_X = all_unseen_scal[['SOG_Avg','Crow_flies_km','SOG_Std','Depth_Avg','Depth_Std',
                               'COG_Avg_Abs_d','d_COG_StartEnd','Month','Weekday','Moon']]
unseen_scal_X


# In[25]:


scal_pred=clf2.predict(unseen_scal_X)
all_unseen_scal['Predict_Fishing'] = scal_pred
all_unseen_scal


# In[ ]:


# Merge all data (seen and unseen together) for mapping/connecting to landings

