# Script to drop AIS data points in state waters FOR UNSEEN VESSELS OR UNSEEN TRIPS OF SEEN VESSELS
require(raster)
require(rgdal)
require(sf)

######################################################################
# 2015-2017 files are formatted separately so start with first 3 years
######################################################################

# List files in the folder
files<-list.files(path="C:/Users/julia/Dropbox/My PC (DESKTOP-3PRD0P2)/Documents/CEC_project/Data_CEC_Project/AIS/FV_only/2015-2017", pattern="*.csv", full.names=T, recursive=F)

# Read in bathymetry data
bathy<-raster("C:/Users/julia/Dropbox/My PC (DESKTOP-3PRD0P2)/Documents/CEC_project/Data_CEC_Project/Bathymetry/Bathymetry.tif")

# Read in state waters shapefile
fed_waters<-readOGR("C:/Users/julia/Dropbox/My PC (DESKTOP-3PRD0P2)/Documents/CEC_project/Data_CEC_Project/Fed_Non_St_Waters.shp")
crs(fed_waters)
federal_waters<-spTransform(fed_waters,CRS("+proj=longlat +datum=NAD83 +no_defs +ellps=GRS80 +towgs84=0,0,0"))

# Path to save to
path<-"C:/Users/julia/Dropbox/My PC (DESKTOP-3PRD0P2)/Documents/CEC_project/Data_CEC_Project/AIS/FV_only/No_St_Water_Bathy/"

only_st<-c()
allDates<-length(files)
thisDate<-0

# Loop through each file and extract bathymetry values
for (i in files){
  thisDate<-thisDate+1
  day = read.csv(i,header=T)
  if (nrow(day)>0){
    AIS_date<-substr(i,109,122)
    day$LAT<-as.numeric(as.character(day$LAT))
    day$LON<-as.numeric(as.character(day$LON))
    coordinates(day)<-c("LON","LAT")
    proj4string(day)<-"+proj=longlat +datum=NAD83 +no_defs +ellps=GRS80 +towgs84=0,0,0"
    # Clip by non-state waters
    clipped<-day[federal_waters,]
    if (nrow(clipped)>0){
      newname<-paste(path,AIS_date,"_bathy_no_state.csv",sep="")
      # Merge with bathymetry data
      rasValue<-extract(bathy,clipped)
      withVals<-cbind(clipped,rasValue)
      newfile<-as.data.frame(withVals)
      colnames(newfile)[15]<-"Depth_m"
      # Save file
      write.csv(newfile,newname)
      print(paste("Saved file: ",AIS_date,sep=""))
      progress<-(thisDate/allDates)*100
      print(paste(progress,"% complete",sep=""))
    }
    else {
      only_st<-c(only_st,AIS_date)
      print(paste("No federal data for this date: ",AIS_date,sep=""))
      progress<-(thisDate/allDates)*100
      print(paste(progress,"% complete",sep=""))
    }
  }
}

######################################################################
# Repeat, with modifications for 2018
######################################################################

files2<-list.files(path="C:/Users/julia/Dropbox/My PC (DESKTOP-3PRD0P2)/Documents/CEC_project/Data_CEC_Project/AIS/FV_only/2018", pattern="*.csv", full.names=T, recursive=F)

only_st<-c()
allDates<-length(files2)
thisDate<-0

# Loop through each file and extract bathymetry values
for (i in files2){
  thisDate<-thisDate+1
  day = read.csv(i,header=T)
  if (nrow(day)>0){
    AIS_date<-substr(i,104,117)
    day$LAT<-as.numeric(as.character(day$LAT))
    day$LON<-as.numeric(as.character(day$LON))
    coordinates(day)<-c("LON","LAT")
    proj4string(day)<-"+proj=longlat +datum=NAD83 +no_defs +ellps=GRS80 +towgs84=0,0,0"
    # Clip by non-state waters
    clipped<-day[federal_waters,]
    if (nrow(clipped)>0){
      newname<-paste(path,AIS_date,"_bathy_no_state.csv",sep="")
      # Merge with bathymetry data
      rasValue<-extract(bathy,clipped)
      withVals<-cbind(clipped,rasValue)
      newfile<-as.data.frame(withVals)
      colnames(newfile)[17]<-"Depth_m"
      # Clean up to match formatting of 2015-2017 files
      newfile<-newfile[,c("COG","CallSign","Cargo","Datetime","Draft","Heading","IMO","Length","MMSI",
                          "SOG","Status","VesselName","VesselType","Width","Depth_m","LON","LAT")]
      # Save file
      write.csv(newfile,newname)
      print(paste("Saved file: ",AIS_date,sep=""))
      progress<-(thisDate/allDates)*100
      print(paste(progress,"% complete",sep=""))
    }
    else {
      only_st<-c(only_st,AIS_date)
      print(paste("No federal data for this date: ",AIS_date,sep=""))
      progress<-(thisDate/allDates)*100
      print(paste(progress,"% complete",sep=""))
    }
  }
}

###########################################################################################
# Repeat, with modifications for 2018 (second half of year is formatted differently AGAIN)
###########################################################################################

files3<-list.files(path="C:/Users/julia/Dropbox/My PC (DESKTOP-3PRD0P2)/Documents/CEC_project/Data_CEC_Project/AIS/FV_only/2018_2", pattern="*.csv", full.names=T, recursive=F)

allDates<-length(files3)
thisDate<-0

# Loop through each file and extract bathymetry values
for (i in files3){
  thisDate<-thisDate+1
  day = read.csv(i,header=T)
  if (nrow(day)>0){
    AIS_date<-substr(i,106,119)
    day$LAT<-as.numeric(as.character(day$LAT))
    day$LON<-as.numeric(as.character(day$LON))
    coordinates(day)<-c("LON","LAT")
    proj4string(day)<-"+proj=longlat +datum=NAD83 +no_defs +ellps=GRS80 +towgs84=0,0,0"
    # Clip by non-state waters
    clipped<-day[federal_waters,]
    if (nrow(clipped)>0){
      newname<-paste(path,AIS_date,"_bathy_no_state.csv",sep="")
      # Merge with bathymetry data
      rasValue<-extract(bathy,clipped)
      withVals<-cbind(clipped,rasValue)
      newfile<-as.data.frame(withVals)
      colnames(newfile)[16]<-"Depth_m"
      # Clean up to match formatting of 2015-2017 files
      newfile<-newfile[,c("COG","CallSign","Cargo","Datetime","Draft","Heading","IMO","Length","MMSI",
                          "SOG","Status","VesselName","VesselType","Width","Depth_m","LON","LAT")]
      # Save file
      write.csv(file,newname)
      print(paste("Saved file: ",AIS_date,sep=""))
      progress<-(thisDate/allDates)*100
      print(paste(progress,"% complete",sep=""))
    }
    else {
      only_st<-c(only_st,AIS_date)
      print(paste("No federal data for this date: ",AIS_date,sep=""))
      progress<-(thisDate/allDates)*100
      print(paste(progress,"% complete",sep=""))
    }
  }
}

