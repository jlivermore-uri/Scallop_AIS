# Comparing accuracy of VTR rasters to NEFOP

library(dplyr)
library(raster)
library(rgdal)
library(terra)
library(sf)

options(scipen=999)
setwd("C:/Users/julia/Dropbox/My PC (DESKTOP-3PRD0P2)/Documents/CEC_project/Data_CEC_Project")

# Create empty raster from existing VTR raster for all years
empty<-rast(xmin=1940294.23659445,xmax=2214294.23659445,ymin=244068.550671436,ymax=518568.550671436,resolution=c(500,500),crs="+proj=aea +lat_0=40 +lon_0=-96 +lat_1=28 +lat_2=42 +x_0=0 +y_0=0 +datum=NAD83 +units=m
               +nodefs")

##################################################################################
# File setup
##################################################################################

nefop<-read.csv("C:/Users/julia/Dropbox/My PC (DESKTOP-3PRD0P2)/Documents/CEC_project/Data_CEC_Project/NEFOP_for_comparison.csv")
nefop<-nefop[!is.na(nefop$GIS_LATHBEG_y),]
nefop<-nefop[!is.na(nefop$GIS_LONHBEG_y),]
nefop<-nefop[!is.na(nefop$GIS_LATHEND_y),]
nefop<-nefop[!is.na(nefop$GIS_LONHEND_y),]
# Identify only trips catching scallop
nefop_scal<-subset(nefop,COMNAME=="SCALLOP, SEA")

# Create lines from all trip hauls
b = nefop_scal[, c("GIS_LONHBEG_y", "GIS_LATHBEG_y")]
names(b) = c("long", "lat")
e = nefop_scal[, c("GIS_LONHEND_y", "GIS_LATHEND_y")]
names(e) = c("long", "lat")

nefop_scal$geometry = do.call(
  "c", 
  lapply(seq(nrow(b)), function(i) {
    st_sfc(
      st_linestring(
        as.matrix(
          rbind(b[i, ], e[i, ])
        )
      ),
      crs = "+proj=longlat +datum=WGS84 +no_defs"
    )
  }))

nefop_scal_sf = st_as_sf(nefop_scal)
options(sf_max.plot=1)
plot(nefop_scal_sf)
nefop_scal_sf$X<-NULL
nefop_scal_sf$HAILWT<-NULL
nefop_scal_sf$FISHDISP<-NULL
nefop_scal_sf$CATDISP<-NULL
nefop_scal_sf$DRFLAG<-NULL
nefop_scal_sf$WGTTYPE<-NULL
nefop_scal_sf<-nefop_scal_sf[!duplicated(nefop_scal_sf), ]

scal_vtr_nums<-as.data.frame(unique(nefop_scal_sf$VTRSERNO))
colnames(scal_vtr_nums)[1]<-"VTR_NUMBER"

# Connect to table of IMGIDs
imgid<-read.csv("VTR/IMGID_VTRNUM.csv")
colnames(imgid)<-c("Year","IMGID","VTR_NUMBER")
compareTrips<-merge(scal_vtr_nums,imgid,by="VTR_NUMBER",all.x=T)
compareTrips<-compareTrips[!is.na(compareTrips$IMGID),]

# Create column with full file name
compareTrips$File<-paste("C:/Users/julia/Dropbox/My PC (DESKTOP-3PRD0P2)/Documents/CEC_project/Data_CEC_Project/VTR_Rasters/Rasters/",compareTrips$IMGID,".grd",sep="")
compareTrips$exists<-file.exists(compareTrips$File)
compareTrips<-subset(compareTrips,exists==TRUE)
imgidList<-unique(compareTrips$IMGID)

# Set up path to rasters
rast_path<-"C:/Users/julia/Dropbox/My PC (DESKTOP-3PRD0P2)/Documents/CEC_project/Data_CEC_Project/VTR_Rasters/Rasters/"

##################################################################################
# Loop through individual VTRs in compareTrips and compile corresponding raster data
##################################################################################

progress<-0

# Create table to track results
results<-data.frame(matrix(nrow=0,ncol=5)) 
colnames(results)<-c("VTR","IMGID","VTR_ftprt_beta","VTR_ftprt_pval","Adj_R2")

# Run the loop
for (imgid in imgidList){
  
  progress<-progress+1
  
  # Pull in raster from IMGID file
  thisRast<-raster(paste(rast_path,imgid,".grd",sep=""))
  thisRast<-reclassify(thisRast, cbind(NA, 0))
  
  # Make an empty (0s) raster with the same extent
  blankRast<-thisRast
  blankRast<-blankRast*0
  
  # Pull corresponding VTR number and hauls from NEFOP
  subDat<-subset(compareTrips,IMGID==imgid)
  vtr<-subDat$VTR_NUMBER[1]
  subLines<-subset(nefop_scal_sf,VTRSERNO==vtr)
  subLines<-subLines[!duplicated(subLines$HAULNUM),]
  subLines<-st_transform(subLines,crs(empty))
  subLines$Val<-1

  skip_to_next <- FALSE
  
  # Intersect haul lines with raster
  
  tryCatch(intRast<-raster::rasterize(subLines, blankRast, field="Val", background=0),
           error = function(e) { skip_to_next <<- TRUE})
    
  if(skip_to_next) { next }     
  
  # Run simple OLS model
  s<-stack(intRast,thisRast)
  sdata<-as.data.frame(s)
  colnames(sdata)<-c("nefop_haul","vtr_footprint")
  head(sdata)
  mod<-lm(nefop_haul~vtr_footprint,data=sdata)
  summary(mod)
  
  # Save results
  newResults<-c(vtr,imgid,mod$coefficients[[2]],summary(mod)$coefficients[2,4],summary(mod)$r.squared)
  results<-rbind(results,newResults)
  
  # Print status
  print(paste("Completed trip ",progress," out of ",length(imgidList),".",sep=""))
  print(paste(100*(progress/length(imgidList)),"% complete.",sep=""))
  remove(thisRast)
  
}

colnames(results)<-c("VTR","IMGID","VTR_ftprt_beta","VTR_ftprt_pval","Adj_R2")

mean(results$VTR_ftprt_beta)
