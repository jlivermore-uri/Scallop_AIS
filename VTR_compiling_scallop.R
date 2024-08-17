##################################################################################
# VTR_compiling_scallop.r
##################################################################################
library(dplyr)
library(raster)
library(rgdal)
library(terra)

options(scipen=999)

# For layers to add up the same, all rasters must have the same final extent so that
# trip values are distributed across that same extent, independent of what dataset is
# being used (i.e., for comparing VTR product to AIS+VMS+VTR -- the total value of 
# trips should be the same). Clip each raster prior to distributing values.

# RFP extent: 
e <- as(extent(-72.45,-69.59, 40.1, 42.1), 'SpatialPolygons')
projection(e) <- CRS("+proj=longlat +datum=WGS84 +no_defs")
e_new <- spTransform(e, CRS("+proj=aea +lat_0=40 +lon_0=-96 +lat_1=28 +lat_2=42 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs"))

# Make empty raster to add to make sure final extents all match 
empty<-raster(xmn=1940294.23659445,xmx=2214294.23659445,ymn=244068.550671436,ymx=518568.550671436,resolution=c(500,500),crs="+proj=aea +lat_0=40 +lon_0=-96 +lat_1=28 +lat_2=42 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs",vals=0)

setwd("C:/Users/julia/Dropbox/My PC (DESKTOP-3PRD0P2)/Documents/CEC_project/Data_CEC_Project")

# Load file of trip summaries from Fallback_to_VMS-VTR.ipynb
allTrips<-read.csv("scallop_trips_by_dataset_with_vals.csv")

# Fix that VTR locations aren't negative for longitude (was degrees W)
allTrips$LON<-ifelse(allTrips$location_source=="VTR",allTrips$LON * -1,allTrips$LON)

# Confirm that all within the study area
allTrips<-subset(allTrips,LAT>=40.1 & LAT<=42.1)
allTrips<-subset(allTrips,LON>=-72.45 & LON<=-69.59)

# Summary of value by dataset
aggregate(Point_Value~location_source,data=allTrips,FUN=sum)
sum(allTrips$Point_Value)
aggregate(VTR_NUMBER~location_source,data=allTrips,function(x) length(unique(x)))

# Verify that each trip (VTR number) has only 1 location source (this should be empty)
allTrips$Check<-paste(as.character(allTrips$VTR_NUMBER),allTrips$location_source,sep="-")
allTripsCheck<-as.data.frame(allTrips$Check)
allTrips$Check<-NULL
allTripsCheck<-allTripsCheck[!duplicated(allTripsCheck),]
allTripsCheckCount<-as.data.frame(table(allTripsCheck))
# All 1s - so not double counting any trips

# Compare totals from point calculations to total VTR values
allTrips$X<-NULL
AISVMSsub<-subset(allTrips,location_source!="VTR")
AISVMSsub<-AISVMSsub[,c("location_source","VTR_NUMBER","VTR_Dollars","Year")]
AISVMSsub<-AISVMSsub[!duplicated(AISVMSsub),]
VTRsub<-subset(allTrips,location_source=="VTR")
VTRsub<-VTRsub[,c("location_source","VTR_NUMBER","Point_Value","Year")]
colnames(VTRsub)[3]<-"VTR_Dollars"
allTripsSimplified<-rbind(AISVMSsub,VTRsub)
aggregate(VTR_Dollars~location_source,data=allTripsSimplified,FUN=sum)
# THIS ALL CHECKS OUT!

# Create list of VTRs to aggregate and add to AIS+VMS raster
uncovered_vtr<-subset(allTrips,location_source=="VTR")
uncovered_vtr2<-uncovered_vtr

# Connect to table of IMGIDs
imgid<-read.csv("VTR/IMGID_VTRNUM.csv")
colnames(imgid)<-c("Year","IMGID","VTR_NUMBER")
uncovered_vtr<-merge(uncovered_vtr,imgid,by="VTR_NUMBER",all.x=T)

# Create column with full file name
uncovered_vtr$File<-paste("C:/Users/julia/Dropbox/My PC (DESKTOP-3PRD0P2)/Documents/CEC_project/Data_CEC_Project/VTR_Rasters/Rasters/",uncovered_vtr$IMGID,".grd",sep="")
uncovered_vtr$exists<-file.exists(uncovered_vtr$File)

# Make list of VTRs that didn't match up with IMGID file (will need to remove these trips from AIS+VMS+VTR product when comparing with VTR alone)
missed_VTRs<-as.data.frame(unique(setdiff(uncovered_vtr2$VTR_NUMBER,imgid$VTR_NUMBER)))
# 551 trips not covered (all have 14 digits - meaning they're e-VTRs)
write.csv(missed_VTRs,"No_IMGID_trips.csv")
# This doesn't actually affect comparison between products, but will affect overall totals of all data products from this project
# Pretty sure these are all study fleet trips - they have no IMGIDs
# Looked at NOAA's Fisheries Fish Online and none of these have IMGIDs and later trips for same vessel show up as study fleet.
# Not sure how NOAA handled this in their VTR product.

# Subset to only scallop (already done in python but just to be safe)
scal_sub<-subset(uncovered_vtr,Common.Name=="SCALLOP, SEA")

# Create list of unique, uncovered VTR numbers
uncovered_vtr_sub<-subset(scal_sub,exists==T)
uncovered_vtr_sub$X<-NULL
uncovered_vtr_sub<-uncovered_vtr_sub[!duplicated(uncovered_vtr_sub),]
uncovered_vtr_nums<-unique(uncovered_vtr_sub$VTR_NUMBER)

# Create list of unique, uncovered IMGID rasters to pull in based on VTRs
uncov_vtrs<-unique(uncovered_vtr_sub$IMGID)

# Set up path to rasters
rast_path<-"C:/Users/julia/Dropbox/My PC (DESKTOP-3PRD0P2)/Documents/CEC_project/Data_CEC_Project/VTR_Rasters/Rasters/"

# Test out plotting a single r grid file
test<-raster(paste(rast_path,"80451.grd",sep=""))
plot(test)

# Test out adding grid files together
test2 <- raster(paste(rast_path,"4628334.grd",sep=""))
plot(test2)
#test3 <- test + test2 # WON'T WORK DUE TO EXTENT ISSUE
#test3 <- overlay(test,
#                 test2,
#                 fun=function(r1, r2){return(r1-r2)})

extend_all =
  function(rasters){
    extent(Reduce(raster::extend,rasters))
  }

sum_all =
  function(rasters, extent){
    re = lapply(rasters, function(r){raster::extend(r,extent, value=0)})
    Reduce("+", re)
  }

test3 = sum_all(list(test,test2), extend_all(list(test,test2)))
plot(test3)

sum(test3@data@values)

##################################################################################
##################################################################################
# Loop through individual VTRs in uncov_vtrs and compile corresponding raster data
# Adding in only 1 raster at a time so we don't run out of memory.
##################################################################################
##################################################################################

##################################################################################
# ALL YEARS TOGETHER
##################################################################################

# Create raster to build into inside loop
allRast<-raster(paste(rast_path,uncov_vtrs[1],".grd",sep=""))

# Crop to target extent in case it's on the edge
allRast<-raster::crop(allRast,e_new)
# If partially cut off, numbers need to be re-scaled to account for full trip
allRast<-allRast/cellStats(allRast,sum)

extent(allRast)
startVal<-subset(uncovered_vtr_sub,IMGID==uncov_vtrs[1])
startVal$X<-NULL
startVal<-startVal[!duplicated(startVal),]
if (length(startVal)>1){
  distrVal<-sum(startVal$Point_Value)
} else {
  distrVal<-startVal$Point_Value
}
# Remove NAs
allRast<-reclassify(allRast, cbind(NA, 0))
# Distribute value over grid cells
allRast<-allRast * distrVal

# Make empty table to track progress and whether rasters and table match up
tracking<-data.frame(
  IMGID=character(),
  Raster_Total=numeric(),
  Table_Total=numeric()
)
rowDF<-as.data.frame(t(c(uncov_vtrs[1],sum(allRast@data@values),distrVal)))
colnames(rowDF)<-c("IMGID","Raster_Total","Table_Total")
tracking<-rbind(tracking,rowDF)
remove(distrVal,startVal)

# Run the loop
for (vtr in uncov_vtrs[2:length(uncov_vtrs)]){
  thisRast<-raster(paste(rast_path,vtr,".grd",sep=""))
  thisRast<-raster::crop(thisRast,e_new)
  thisRast<-thisRast/cellStats(thisRast,sum)
  startVal<-subset(uncovered_vtr_sub,IMGID==vtr)
  startVal$X<-NULL
  startVal<-startVal[!duplicated(startVal),]
  if (length(startVal)>1){
    distrVal<-sum(startVal$Point_Value)
  } else {
    distrVal<-startVal$Point_Value
  }
  thisRast<-reclassify(thisRast, cbind(NA, 0))
  # Distribute value over grid cells
  thisRast<-thisRast * distrVal
  
  # Save metrics for tracking loop progress
  rowDF<-as.data.frame(t(c(vtr,sum(thisRast@data@values),distrVal)))
  colnames(rowDF)<-c("IMGID","Raster_Total","Table_Total")
  tracking<-rbind(tracking,rowDF)
  
  remove(distrVal,startVal)
  # Add to other raster (simultaneously enlarging the extent if needed)
  allRast=sum_all(list(thisRast,allRast),extend_all(list(thisRast,allRast)))
  remove(thisRast)
}
plot(allRast)
print(paste("Total of values from VTRs left uncovered by AIS+VMS after rasterizing: $",sum(allRast@data@values),sep=""))

# Fix final extent - this doesn't change the value - unnecessary step just to be safe
allRast=sum_all(list(allRast,empty),extend_all(list(allRast,empty)))
plot(allRast)
print(paste("Total of values from VTRs left uncovered by AIS+VMS after rasterizing and checking extent: $",sum(allRast@data@values),sep=""))
raster::writeRaster(allRast,filename="C:/Users/julia/Dropbox/My PC (DESKTOP-3PRD0P2)/Documents/CEC_project/Data_CEC_Project/VTR/allYrsScallopVTR.tif",format='GTiff',overwrite=T)

# Check to make sure rasterizing giving same total as table summing
print(paste("Total of values from VTRs left uncovered by AIS+VMS from table: $",sum(uncovered_vtr_sub$Point_Value),sep=""))

tracking$Check<-abs(tracking$Table_Total - tracking$Raster_Total)

# Identified two IMGIDs that have empty rasters provided by NOAA (IMGIDs: 4887168 and 4889300)
# These two trips fall out of the raster dataset but not the table and explain the difference in values of $15,980.47
# Need to repeat this process on full VTR dataset to identify trips that may need to be removed from 
# AIS/VMS to get the products to add up equally for comparison purposes. 

##################################################################################
# INDIVIDUAL YEARS
##################################################################################

# Repeat for each year
years<-c(2015,2016,2017,2018)

for (year in years){
  uncovered_vtr_sub_2<-subset(uncovered_vtr_sub,Year==year)
  uncov_vtr_yr<-unique(uncovered_vtr_sub_2$IMGID)
  
  oneYrRast<-raster(paste(rast_path,uncov_vtr_yr[1],".grd",sep=""))
  oneYrRast<-raster::crop(oneYrRast,e_new)
  oneYrRast<-oneYrRast/cellStats(oneYrRast,sum)
  startVal<-subset(uncovered_vtr_sub_2,IMGID==uncov_vtr_yr[1])
  startVal$X<-NULL
  startVal<-startVal[!duplicated(startVal),]
  if (length(startVal)>1){
    distrVal<-sum(startVal$Point_Value)
  } else {
    distrVal<-startVal$Point_Value
  }
  oneYrRast<-reclassify(oneYrRast, cbind(NA, 0))
  # Distribute value over grid cells
  oneYrRast<-oneYrRast * distrVal
  remove(distrVal,startVal)
  
  for (vtr in uncov_vtr_yr[2:length(uncov_vtr_yr)]){
    thisRast<-raster(paste(rast_path,vtr,".grd",sep=""))
    thisRast<-raster::crop(thisRast,e_new)
    thisRast<-thisRast/cellStats(thisRast,sum)
    startVal<-subset(uncovered_vtr_sub_2,IMGID==vtr)
    startVal$X<-NULL
    startVal<-startVal[!duplicated(startVal),]
    if (length(startVal)>1){
      distrVal<-sum(startVal$Point_Value)
    } else {
      distrVal<-startVal$Point_Value
    }
    thisRast<-reclassify(thisRast, cbind(NA, 0))
    # Distribute value over grid cells
    thisRast<-thisRast * distrVal
    remove(distrVal,startVal)
    # Add to other raster (simultaneously enlarging the extend if needed)
    oneYrRast=sum_all(list(thisRast,oneYrRast),extend_all(list(thisRast,oneYrRast)))
    remove(thisRast)
  }
  plot(oneYrRast)
  # Fix final extent
  oneYrRast=sum_all(list(oneYrRast,empty),extend_all(list(oneYrRast,empty)))
  plot(oneYrRast)
  raster::writeRaster(oneYrRast,filename=paste("C:/Users/julia/Dropbox/My PC (DESKTOP-3PRD0P2)/Documents/CEC_project/Data_CEC_Project/VTR/",year,"_ScallopVTR.tif",sep=""),format='GTiff',overwrite=T)
  remove(oneYrRast)
}

##################################################################################
##################################################################################
# Repeat process for ALL scallop VTR for use in comparison
##################################################################################
##################################################################################

# Load file of all VTR trips 
allScalVtrTrips<-allTrips
allScalVtrTrips<-allScalVtrTrips[!duplicated(allScalVtrTrips),]

# Connect to table of IMGIDs
all_vtr<-merge(allScalVtrTrips,imgid,by="VTR_NUMBER",all.x=T)

# Create column with full file name
all_vtr$File<-paste("C:/Users/julia/Dropbox/My PC (DESKTOP-3PRD0P2)/Documents/CEC_project/Data_CEC_Project/VTR_Rasters/Rasters/",all_vtr$IMGID,".grd",sep="")
all_vtr$exists<-file.exists(all_vtr$File)

# Create list of unique, uncovered VTR numbers
all_vtr2<-subset(all_vtr,exists==T)
all_vtr_check<-all_vtr2[!duplicated(all_vtr2),]
all_vtr_nums<-unique(all_vtr2$VTR_NUMBER)
all_vtrs_list<-unique(all_vtr2$IMGID)

# Summarize all trips again but ensuring we're only including trips that have corresponding IMGIDs
aggregate(Point_Value~location_source,data=all_vtr,FUN=sum)
sum(all_vtr$Point_Value)
aggregate(Point_Value~location_source,data=all_vtr2,FUN=sum)
sum(all_vtr2$Point_Value)

# Write trips to list that don't have IMGIDs and need to be removed from AIS+VMS layer for comparison purposes
missedVTRsToRemove<-subset(all_vtr,exists==F)
missedVTRsToRemove<-unique(missedVTRsToRemove$VTR_NUMBER)
write.csv(missedVTRsToRemove,"VTRsToDrop.csv")

##################################################################################
# ALL YEARS TOGETHER
##################################################################################

# Create raster to build into inside loop
allRast<-raster(paste(rast_path,all_vtrs_list[1],".grd",sep=""))
allRast<-raster::crop(allRast,e_new)
allRast<-allRast/cellStats(allRast,sum)
startVal<-subset(all_vtr2,IMGID==all_vtrs_list[1])
startVal$X<-NULL
startVal<-startVal[!duplicated(startVal),]
if (nrow(startVal)>1){
  distrVal<-sum(startVal$Point_Value)
} else {
  distrVal<-startVal$Point_Value
}
allRast<-reclassify(allRast, cbind(NA, 0))
# Distribute value over grid cells
allRast<-allRast * distrVal

# Make empty table to track progress and whether rasters and table match up
tracking_allVTR<-data.frame(
  IMGID=character(),
  Raster_Total=numeric(),
  Table_Total=numeric()
)
rowDF<-as.data.frame(t(c(all_vtrs_list[1],sum(allRast@data@values),distrVal)))
colnames(rowDF)<-c("IMGID","Raster_Total","Table_Total")
tracking_allVTR<-rbind(tracking_allVTR,rowDF)

remove(distrVal,startVal)

# Run the loop
for (vtr in all_vtrs_list[2:length(all_vtrs_list)]){
  thisRast<-raster(paste(rast_path,vtr,".grd",sep=""))
  skip_to_next <- FALSE
  tryCatch(thisRast<-raster::crop(thisRast,e_new), error = function(e) { skip_to_next <<- TRUE})
  if(skip_to_next) { next }     
  thisRast<-thisRast/cellStats(thisRast,sum)
  startVal<-subset(all_vtr2,IMGID==vtr)
  startVal$X<-NULL
  startVal<-startVal[!duplicated(startVal),]
  if (nrow(startVal)>1){
    distrVal<-sum(startVal$Point_Value)
  } else {
    distrVal<-startVal$Point_Value
  }
  thisRast<-reclassify(thisRast, cbind(NA, 0))
  # Distribute value over grid cells
  thisRast<-thisRast * distrVal
  
  # Save metrics for tracking loop progress
  rowDF<-as.data.frame(t(c(vtr,sum(thisRast@data@values),distrVal)))
  colnames(rowDF)<-c("IMGID","Raster_Total","Table_Total")
  tracking_allVTR<-rbind(tracking_allVTR,rowDF)
  
  remove(distrVal,startVal)
  # Add to other raster (simultaneously enlarging the extend if needed)
  allRast=sum_all(list(thisRast,allRast),extend_all(list(thisRast,allRast)))
  remove(thisRast)
}
plot(allRast)
# Fix final extent
allRast=sum_all(list(allRast,empty),extend_all(list(allRast,empty)))
plot(allRast)
sum(allRast@data@values)
raster::writeRaster(allRast,filename="C:/Users/julia/Dropbox/My PC (DESKTOP-3PRD0P2)/Documents/CEC_project/Data_CEC_Project/VTR/allYrsALL_ScallopVTR.tif",format='GTiff',overwrite=T)
remove(allRast)

tracking_allVTR$Check<-tracking_allVTR$Table_Total - tracking_allVTR$Raster_Total
# Same two trips fall out - have empty rasters provided by NOAA (IMGIDs: 4887168 and 4889300)
print(paste("Difference between raster and tables due to 2 bad IMGID rasters: $",sum(tracking_allVTR$Check),sep=""))

##################################################################################
# INDIVIDUAL YEARS
##################################################################################

# Repeat for each year
for (year in years){
  vtr_sub<-subset(all_vtr2,Year.y==year)
  vtr_yr<-unique(vtr_sub$IMGID)
  
  oneYrRast<-raster(paste(rast_path,vtr_yr[1],".grd",sep=""))
  skip_to_next <- FALSE
  tryCatch(oneYrRast<-raster::crop(oneYrRast,e_new), error = function(e) { skip_to_next <<- TRUE})
  if(skip_to_next) { next }     
  oneYrRast<-oneYrRast/cellStats(oneYrRast,sum)
  startVal<-subset(vtr_sub,IMGID==vtr_yr[1])
  startVal$X<-NULL
  startVal<-startVal[!duplicated(startVal),]
  if (nrow(startVal)>1){
    distrVal<-sum(startVal$Point_Value)
  } else {
    distrVal<-startVal$Point_Value
  }
  oneYrRast<-reclassify(oneYrRast, cbind(NA, 0))
  # Distribute value over grid cells
  oneYrRast<-oneYrRast * distrVal
  remove(distrVal,startVal)
  
  for (vtr in vtr_yr[2:length(vtr_yr)]){
    thisRast<-raster(paste(rast_path,vtr,".grd",sep=""))
    skip_to_next <- FALSE
    tryCatch(thisRast<-raster::crop(thisRast,e_new), error = function(e) { skip_to_next <<- TRUE})
    if(skip_to_next) { next }     
    thisRast<-thisRast/cellStats(thisRast,sum)
    startVal<-subset(vtr_sub,IMGID==vtr)
    startVal$X<-NULL
    startVal<-startVal[!duplicated(startVal),]
    if (nrow(startVal)>1){
      distrVal<-sum(startVal$Point_Value)
    } else {
      distrVal<-startVal$Point_Value
    }
    thisRast<-reclassify(thisRast, cbind(NA, 0))
    # Distribute value over grid cells
    thisRast<-thisRast * distrVal
    remove(distrVal,startVal)
    # Add to other raster (simultaneously enlarging the extend if needed)
    oneYrRast=sum_all(list(thisRast,oneYrRast),extend_all(list(thisRast,oneYrRast)))
    remove(thisRast)
  }
  plot(oneYrRast)
  # Fix final extent
  oneYrRast=sum_all(list(oneYrRast,empty),extend_all(list(oneYrRast,empty)))
  plot(oneYrRast)
  raster::writeRaster(oneYrRast,filename=paste("C:/Users/julia/Dropbox/My PC (DESKTOP-3PRD0P2)/Documents/CEC_project/Data_CEC_Project/VTR/",year,"_ALL_ScallopVTR.tif",sep=""),format='GTiff',overwrite=T)
  remove(oneYrRast)
}

# Flag two bad trips that need to be eliminated from rasters created from AIS/VMS
bad_IMGID_rasters<-subset(tracking_allVTR,Check>0.1)
bad_IMGID_rasters<-as.data.frame(bad_IMGID_rasters$IMGID)
colnames(bad_IMGID_rasters)<-"Bad_IMGIDs"
bad_IMGID_rasters<-merge(bad_IMGID_rasters,all_vtr2,by.x="Bad_IMGIDs",by.y="IMGID")
sum(bad_IMGID_rasters$Point_Value)
VTRsToDrop<-unique(bad_IMGID_rasters$VTR_NUMBER)
# After verifying, these are NOT in the AIS/VMS - only in VTR and fall out of both
# No removal needed
