# Script to drop AIS data points in state waters
require(raster)
require(rgdal)
require(sf)

# List files in the folder
files<-list.files(path="C:/Users/julia/Dropbox/My PC (DESKTOP-3PRD0P2)/Documents/CEC_project/Data_CEC_Project/Training_Data/", pattern="*good.csv", full.names=T, recursive=F)

# Read in bathymetry data
bathy <- raster("C:/Users/julia/Dropbox/My PC (DESKTOP-3PRD0P2)/Documents/CEC_project/Data_CEC_Project/Bathymetry/Bathymetry.tif")

# Read in state waters shapefile
fed_waters<-readOGR("C:/Users/julia/Dropbox/My PC (DESKTOP-3PRD0P2)/Documents/CEC_project/Data_CEC_Project/Fed_Non_St_Waters.shp")
crs(fed_waters)
federal_waters<-spTransform(fed_waters,CRS("+proj=longlat +datum=NAD83 +no_defs +ellps=GRS80 +towgs84=0,0,0"))

only_st<-c()

# Loop through each file and extract bathymetry values
for (i in files){
  trip = read.csv(i,header=T)
  if (nrow(trip)>0){
    trip_ID<-substr(i,101,111)
    trip$LAT<-as.numeric(as.character(trip$LAT))
    trip$LON<-as.numeric(as.character(trip$LON))
    coordinates(trip)<-c("LON","LAT")
    proj4string(trip)<-"+proj=longlat +datum=NAD83 +no_defs +ellps=GRS80 +towgs84=0,0,0"
    # Clip by non-state waters
    clipped<-trip[federal_waters,]
    if (nrow(clipped)>0){
      newname<-gsub("_good.csv","_bathy_no_state.csv",i)
      # Merge with bathymetry data
      rasValue<-extract(bathy,clipped)
      withVals<-cbind(clipped,rasValue)
      newfile<-as.data.frame(withVals)
      colnames(newfile)[15]<-"Depth_m"
      # Save file
      write.csv(newfile,newname)
      print(paste("Saved file: ",trip_ID,sep=""))
    }
    else {
      only_st<-c(only_st,trip_ID)
      print(paste("No federal data for trip: ",trip_ID,sep=""))
    }
  }
}
