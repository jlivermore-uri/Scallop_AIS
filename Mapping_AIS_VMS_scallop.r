##################################################################################
# Mapping_AIS_VMS_scallop.r
##################################################################################
library(raster)
library(rgdal)
library(terra)
library(maps)
library(ggplot2)
library(grid)
library(scales)
library(viridis)
library(tidyterra)
library(ggspatial)
library(sf)
library(diffeR)
library(cowplot)
library(gridExtra)
library(spatialEco)
library(SpatialPack)

options(scipen=999)

setwd("/work/pi_pengfei_liu_uri_edu/Scallop")

# Map bounds from RFP: -72.45 - -69.59 W and 40.1 - 42.1 N
# Converted to Alber's equal area conic

##################################################################################
# Map AIS and VMS data and combine with VTR rasters
##################################################################################

aisVms<-read.csv("scallop_pt_values_AIS+VMS_datasets.csv")
tripsToDrop<-read.csv("VTRsToDrop.csv")
tripsToDrop<-tripsToDrop[2]
colnames(tripsToDrop)[1]<-"VTR_NUMBER"
aisVms<-subset(aisVms,!(VTR_NUMBER %in% tripsToDrop$VTR_NUMBER))

# Subset to just scallop landed
aisVmsScalOnly<-subset(aisVms,Common.Name=="SCALLOP, SEA")
# The first pass has all species landed on trips that landed scallops
print(paste("Point value total from AIS and VMS only: $",sum(aisVmsScalOnly$Point_Value),sep=""))

land = readOGR(dsn="Contiguous_US.shp", layer="Contiguous_US")
land = vect(land)

leases = readOGR(dsn="SNE_WindLeaseAres_06062024.shp", layer="SNE_WindLeaseAres_06062024") 
leases = vect(leases)

### DO COMBINED YEARS FIRST

# Create empty raster from existing VTR raster for all years
empty<-rast(xmin=1940294.23659445,xmax=2214294.23659445,ymin=244068.550671436,ymax=518568.550671436,resolution=c(500,500),crs="+proj=aea +lat_0=40 +lon_0=-96 +lat_1=28 +lat_2=42 +x_0=0 +y_0=0 +datum=NAD83 +units=m
               +nodefs")
aisVmsVect<-st_as_sf(x=aisVmsScalOnly,coords=c("LON","LAT"),crs="+proj=longlat")
aisVmsVect<-st_transform(aisVmsVect,crs(empty))
output<-rasterize(aisVmsVect,empty,field='Point_Value',fun=sum,background=NA)
writeRaster(output,"scal_allYrsAisVmsRast.tif",overwrite=TRUE)
plot(output)
print(paste("Point value total from AIS and VMS only after rasterizing: $",global(output,"sum",na.rm=TRUE),sep=""))
print(paste("Point value total from AIS and VMS only from table: $",sum(aisVmsScalOnly$Point_Value),sep=""))

allYrs_plot<-ggplot() +
  geom_spatraster(data = output) +
  scale_fill_whitebox_c(
    palette = "viridi",
    labels = scales::label_number(prefix = "$"),
    n.breaks = 12,
    guide = guide_legend(reverse = TRUE)
  ) +
  labs(
    fill = "",
    title = "Ex-vessel Value (AIS + VMS only)",
  ) + 
  geom_spatvector(data = land, fill = "gray") +
  geom_spatvector(data = leases, fill = NA) + 
  theme_classic() + 
  coord_sf(xlim=c(xmin(ext(output)),xmax(ext(output))),ylim=c(ymin(ext(output)),ymax(ext(output))), crs = "+proj=aea +lat_0=40 +lon_0=-96 +lat_1=28 +lat_2=42 +x_0=0 +y_0=0 +datum=NAD83 +units=m
           +nodefs") +
  # Add scale and North arrow
  ggspatial::annotation_scale(
    location = "tl",
    bar_cols = c("black", "white"),
    text_family = "ArcherPro Book"
  ) +
  ggspatial::annotation_north_arrow(
    location = "tl", which_north = "true",
    pad_x = unit(0.1, "in"), pad_y = unit(0.4, "in"),
    style = ggspatial::north_arrow_nautical(
      fill = c("grey40", "white"),
      line_col = "black",
      text_family = "ArcherPro Book"
    )
  )
allYrs_plot
ggsave("allYrs_Scallop_AIS_VMS.png",allYrs_plot,width=8,height=8,units="in",dpi=300)

# Add to the VTR layer
uncovVTRscallopAllYrs <- terra::rast("/work/pi_pengfei_liu_uri_edu/Scallop/VTR/Compiled_VTR_Rasters/allYrsScallopVTR.tif")
plot(uncovVTRscallopAllYrs)
print(paste("Raster total from VTR only (uncovered by AIS or VMS): $",global(uncovVTRscallopAllYrs,"sum",na.rm=TRUE),sep=""))

allYrsFULL <- terra::mosaic(output, uncovVTRscallopAllYrs, fun=sum)
writeRaster(allYrsFULL,"scal_allYrs_AISVMSVTR.tif",overwrite=TRUE)
plot(allYrsFULL)
print(paste("Raster total from all 3 datasets combined: $",global(allYrsFULL,"sum",na.rm=TRUE),sep=""))

allYrsAISVMSVTR_plot<-ggplot() +
  geom_spatraster(data = allYrsFULL) +
  scale_fill_whitebox_c(
    palette = "viridi",
    labels = scales::label_number(prefix = "$"),
    n.breaks = 12,
    guide = guide_legend(reverse = TRUE)
  ) +
  labs(
    fill = "",
    title = "Scallop Ex-vessel Value (AIS + VMS + VTR)",
  ) + 
  scale_x_continuous(expand = c(0, 0),limits=c(xmin(ext(allYrsFULL)),xmax(ext(allYrsFULL)))) +
  scale_y_continuous(expand = c(0, 0),limits=c(ymin(ext(allYrsFULL)),ymax(ext(allYrsFULL)))) +
  geom_spatvector(data = land, fill = "gray") +
  geom_spatvector(data = leases, fill = NA) + 
  theme_classic() + 
  coord_sf(xlim=c(xmin(ext(allYrsFULL)),xmax(ext(allYrsFULL))),ylim=c(ymin(ext(allYrsFULL)),ymax(ext(allYrsFULL))), crs = "+proj=aea +lat_0=40 +lon_0=-96 +lat_1=28 +lat_2=42 +x_0=0 +y_0=0 +datum=NAD83 +units=m
           +nodefs") +
  # Add scale and North arrow
  ggspatial::annotation_scale(
    location = "tl",
    bar_cols = c("black", "white"),
    text_family = "ArcherPro Book"
  ) +
  ggspatial::annotation_north_arrow(
    location = "tl", which_north = "true",
    pad_x = unit(0.1, "in"), pad_y = unit(0.4, "in"),
    style = ggspatial::north_arrow_nautical(
      fill = c("grey40", "white"),
      line_col = "black",
      text_family = "ArcherPro Book"
    )
  )
allYrsAISVMSVTR_plot
ggsave("allYrs_Scallop_AIS_VMS_VTR.png",allYrsAISVMSVTR_plot,width=8,height=8,units="in",dpi=300)

# Plot out full VTR rasters (ALL TRIPS)
allVTRscallopAllYrs <- terra::rast("/work/pi_pengfei_liu_uri_edu/Scallop/VTR/Compiled_VTR_Rasters/allYrsALL_ScallopVTR.tif")
plot(allVTRscallopAllYrs)
print(paste("Raster total from ALL VTR only: $",global(allVTRscallopAllYrs,"sum",na.rm=TRUE),sep=""))

allYrsAllVTR_plot<-ggplot() +
  geom_spatraster(data = allVTRscallopAllYrs) +
  scale_fill_whitebox_c(
    palette = "viridi",
    labels = scales::label_number(prefix = "$"),
    n.breaks = 12,
    guide = guide_legend(reverse = TRUE)
  ) +
  labs(
    fill = "",
    title = "Ex-vessel Value (All VTR)",
  ) + 
  geom_spatvector(data = land, fill = "gray") +
  geom_spatvector(data = leases, fill = NA) + 
  theme_classic() + 
  scale_x_continuous(expand = c(0, 0),limits=c(xmin(ext(allVTRscallopAllYrs)),xmax(ext(allVTRscallopAllYrs)))) +
  scale_y_continuous(expand = c(0, 0),limits=c(ymin(ext(allVTRscallopAllYrs)),ymax(ext(allVTRscallopAllYrs)))) +
  coord_sf(xlim=c(xmin(ext(allVTRscallopAllYrs)),xmax(ext(allVTRscallopAllYrs))),ylim=c(ymin(ext(allVTRscallopAllYrs)),ymax(ext(allVTRscallopAllYrs))), crs = "+proj=aea +lat_0=40 +lon_0=-96 +lat_1=28 +lat_2=42 +x_0=0 +y_0=0 +datum=NAD83 +units=m
           +nodefs") +
  # Add scale and North arrow
  ggspatial::annotation_scale(
    location = "tl",
    bar_cols = c("black", "white"),
    text_family = "ArcherPro Book"
  ) +
  ggspatial::annotation_north_arrow(
    location = "tl", which_north = "true",
    pad_x = unit(0.1, "in"), pad_y = unit(0.4, "in"),
    style = ggspatial::north_arrow_nautical(
      fill = c("grey40", "white"),
      line_col = "black",
      text_family = "ArcherPro Book"
    )
  )
allYrsAllVTR_plot
ggsave("AllYrs_ALL_Scallop_VTR.png",allYrsAllVTR_plot,width=8,height=8,units="in",dpi=300)

# Compare full VTR to our product
png("All_years_scallop_comparison_scatter.png")
comp_scatter<-MADscatterplot(allYrsFULL, allVTRscallopAllYrs, strata = NULL)
plot(comp_scatter)
dev.off()
comp_scatter

allVTRscallopAllYrs_crop<-crop(allVTRscallopAllYrs,allYrsFULL)
allYrsDiff<-allYrsFULL-allVTRscallopAllYrs_crop
plot(allYrsDiff)
writeRaster(allYrsDiff,"scal_allYrs_diff.tif",overwrite=TRUE)

diff_plot<-ggplot() +
  geom_spatraster(data = allYrsDiff) +
  scale_fill_whitebox_c(
    palette = "muted",
    labels = scales::label_number(prefix = "$"),
    n.breaks = 12,
    guide = guide_legend(reverse = TRUE)
  ) +
  scale_x_continuous(expand = c(0, 0),limits=c(xmin(ext(allYrsDiff)),xmax(ext(allYrsDiff)))) +
  scale_y_continuous(expand = c(0, 0),limits=c(ymin(ext(allYrsDiff)),ymax(ext(allYrsDiff)))) +
  coord_sf(xlim=c(xmin(ext(allYrsDiff)),xmax(ext(allYrsDiff))),ylim=c(ymin(ext(allYrsDiff)),ymax(ext(allYrsDiff))), crs = "+proj=aea +lat_0=40 +lon_0=-96 +lat_1=28 +lat_2=42 +x_0=0 +y_0=0 +datum=NAD83 +units=m
           +nodefs") +
  labs(
    fill = "",
    title = "Difference in Ex-vessel Value",
  ) + 
  geom_spatvector(data = land, fill = "gray") +
  geom_spatvector(data = leases, fill = NA) + 
  theme_classic() + 
  # Add scale and North arrow
  ggspatial::annotation_scale(
    location = "tl",
    bar_cols = c("black", "white"),
    text_family = "ArcherPro Book"
  ) +
  ggspatial::annotation_north_arrow(
    location = "tl", which_north = "true",
    pad_x = unit(0.1, "in"), pad_y = unit(0.4, "in"),
    style = ggspatial::north_arrow_nautical(
      fill = c("grey40", "white"),
      line_col = "black",
      text_family = "ArcherPro Book"
    )
  )
diff_plot
ggsave(paste("AllYrs_Scallop_Diff.png",sep=""),diff_plot,width=8,height=8,units="in",dpi=300)
print(paste("2015-2018 Moran's I: ",autocor(allYrsDiff, method="moran", global=TRUE),sep = ""))

# Dutilleul moving window bivariate raster correlation
#corr<-spatialEco::raster.modified.ttest(allYrsFULL,allVTRscallopAllYrs,d=10000)     
#plot(raster(corr,main="Raster Correlation"))
#plot(corr["corr"], pch=20)
# This doesn't work because we have lots of cells with 0 values in both layers.
# Corr will fail because sd=0. 

allYrsFULLrast<-raster(allYrsFULL)
allVTRscallopAllYrsrast<-raster(allVTRscallopAllYrs)
Cor<-corLocal(allYrsFULLrast,allVTRscallopAllYrsrast,test=T)
png(file="/work/pi_pengfei_liu_uri_edu/Scallop/correlation.png")  
plot(Cor)
dev.off() 
summary(Cor)
print(paste("Median Pearson's correlation coefficient: ",summary(Cor)[3,1],sep=""))

# Compare sum of products -- these should be equal because the same trips are being accounted for in both (just distributed differently)
allYrsAISVMSVTR_sum<-global(allYrsFULL,"sum",na.rm=TRUE)
allYrsAllVTR_sum<-global(allVTRscallopAllYrs,"sum",na.rm=TRUE)
print(paste("Total dollars from all VTRs all years: ",allYrsAllVTR_sum$sum,sep=""))
print(paste("Total dollars from AIS+VMS+VTR all years: ",allYrsAISVMSVTR_sum$sum,sep=""))

### REPEAT PROCESS FOR INDIVIDUAL YEARS

# Repeat to create year rasters
Years<-c(2015,2016,2017,2018)
aisVmsScalOnly$Year<-substr(aisVmsScalOnly$Date_Land,1,4)
for (i in Years){
  yrDat<-subset(aisVmsScalOnly,Year==i)
  yrDatVect<-vect(yrDat,geom=c("LON","LAT"),crs="+proj=longlat")
  yrDatVect<-project(yrDatVect,crs(empty))
  yrAisVmsRast<-rasterize(yrDatVect,empty,field='Point_Value',fun=sum)
  plot(yrAisVmsRast)
  writeRaster(yrAisVmsRast,paste(i,"_scal_AisVmsRast.tif",sep=""),overwrite=TRUE)
  
  oneYear_plot<-ggplot() +
    geom_spatraster(data = yrAisVmsRast) +
    scale_fill_whitebox_c(
      palette = "viridi",
      labels = scales::label_number(prefix = "$"),
      n.breaks = 12,
      guide = guide_legend(reverse = TRUE)
    ) +
    labs(
      fill = "",
      title = "Ex-vessel Value (AIS + VMS only)",
      subtitle = i
    ) + 
    geom_spatvector(data = land, fill = "gray") +
    geom_spatvector(data = leases, fill = NA) + 
    theme_classic() + 
    scale_x_continuous(expand = c(0, 0),limits=c(xmin(ext(yrAisVmsRast)),xmax(ext(yrAisVmsRast)))) +
    scale_y_continuous(expand = c(0, 0),limits=c(ymin(ext(yrAisVmsRast)),ymax(ext(yrAisVmsRast)))) +
    coord_sf(xlim=c(xmin(ext(yrAisVmsRast)),xmax(ext(yrAisVmsRast))),ylim=c(ymin(ext(yrAisVmsRast)),ymax(ext(yrAisVmsRast))), crs = "+proj=aea +lat_0=40 +lon_0=-96 +lat_1=28 +lat_2=42 +x_0=0 +y_0=0 +datum=NAD83 +units=m
           +nodefs") +
    # Add scale and North arrow
    ggspatial::annotation_scale(
      location = "tl",
      bar_cols = c("black", "white"),
      text_family = "ArcherPro Book"
    ) +
    ggspatial::annotation_north_arrow(
      location = "tl", which_north = "true",
      pad_x = unit(0.1, "in"), pad_y = unit(0.4, "in"),
      style = ggspatial::north_arrow_nautical(
        fill = c("grey40", "white"),
        line_col = "black",
        text_family = "ArcherPro Book"
      )
    )
  oneYear_plot
  ggsave(paste(i,"_Scallop_AIS_VMS.png",sep=""),oneYear_plot,width=8,height=8,units="in",dpi=300)
 
  # Add to the VTR layer
  uncovVTRscallopThisYr <- terra::rast(paste("/work/pi_pengfei_liu_uri_edu/Scallop/VTR/Compiled_VTR_Rasters/",i,"_ScallopVTR.tif",sep=""))
  thisYrFULL <- terra::mosaic(yrAisVmsRast, uncovVTRscallopThisYr, fun=sum)
  writeRaster(thisYrFULL,paste("scal_",i,"_AISVMSVTR.tif",sep=""),overwrite=TRUE)
  plot(thisYrFULL)
  
  thisYrAISVMSVTR_plot<-ggplot() +
    geom_spatraster(data = thisYrFULL) +
    scale_fill_whitebox_c(
      palette = "viridi",
      labels = scales::label_number(prefix = "$"),
      n.breaks = 12,
      guide = guide_legend(reverse = TRUE)
    ) +
    labs(
      fill = "",
      title = "Ex-vessel Value (AIS + VMS + VTR)",
      subtitle = i
    ) + 
    geom_spatvector(data = land, fill = "gray") +
    geom_spatvector(data = leases, fill = NA) + 
    theme_classic() + 
    scale_x_continuous(expand = c(0, 0),limits=c(xmin(ext(thisYrFULL)),xmax(ext(thisYrFULL)))) +
    scale_y_continuous(expand = c(0, 0),limits=c(ymin(ext(thisYrFULL)),ymax(ext(thisYrFULL)))) +
    coord_sf(xlim=c(xmin(ext(thisYrFULL)),xmax(ext(thisYrFULL))),ylim=c(ymin(ext(thisYrFULL)),ymax(ext(thisYrFULL))), crs = "+proj=aea +lat_0=40 +lon_0=-96 +lat_1=28 +lat_2=42 +x_0=0 +y_0=0 +datum=NAD83 +units=m
           +nodefs") +
    # Add scale and North arrow
    ggspatial::annotation_scale(
      location = "tl",
      bar_cols = c("black", "white"),
      text_family = "ArcherPro Book"
    ) +
    ggspatial::annotation_north_arrow(
      location = "tl", which_north = "true",
      pad_x = unit(0.1, "in"), pad_y = unit(0.4, "in"),
      style = ggspatial::north_arrow_nautical(
        fill = c("grey40", "white"),
        line_col = "black",
        text_family = "ArcherPro Book"
      )
    )
  thisYrAISVMSVTR_plot
  ggsave(paste(i,"_Scallop_AIS_VMS_VTR.png",sep=""),thisYrAISVMSVTR_plot,width=8,height=8,units="in",dpi=300)
  
  # Plot out full VTR rasters (ALL TRIPS)
  allVTRscallopThisYr <- terra::rast(paste("/work/pi_pengfei_liu_uri_edu/Scallop/VTR/Compiled_VTR_Rasters/",i,"_ALL_ScallopVTR.tif",sep=""))
  plot(allVTRscallopThisYr)
  
  thisYrAllVTR_plot<-ggplot() +
    geom_spatraster(data = allVTRscallopThisYr) +
    scale_fill_whitebox_c(
      palette = "viridi",
      labels = scales::label_number(prefix = "$"),
      n.breaks = 12,
      guide = guide_legend(reverse = TRUE)
    ) +
    labs(
      fill = "",
      title = "Ex-vessel Value (All VTR)",
      subtitle = i
    ) + 
    geom_spatvector(data = land, fill = "gray") +
    geom_spatvector(data = leases, fill = NA) + 
    theme_classic() + 
    scale_x_continuous(expand = c(0, 0),limits=c(xmin(ext(allVTRscallopThisYr)),xmax(ext(allVTRscallopThisYr)))) +
    scale_y_continuous(expand = c(0, 0),limits=c(ymin(ext(allVTRscallopThisYr)),ymax(ext(allVTRscallopThisYr)))) +
    coord_sf(xlim=c(xmin(ext(allVTRscallopThisYr)),xmax(ext(allVTRscallopThisYr))),ylim=c(ymin(ext(allVTRscallopThisYr)),ymax(ext(allVTRscallopThisYr))), crs = "+proj=aea +lat_0=40 +lon_0=-96 +lat_1=28 +lat_2=42 +x_0=0 +y_0=0 +datum=NAD83 +units=m
           +nodefs") +
    # Add scale and North arrow
    ggspatial::annotation_scale(
      location = "tl",
      bar_cols = c("black", "white"),
      text_family = "ArcherPro Book"
    ) +
    ggspatial::annotation_north_arrow(
      location = "tl", which_north = "true",
      pad_x = unit(0.1, "in"), pad_y = unit(0.4, "in"),
      style = ggspatial::north_arrow_nautical(
        fill = c("grey40", "white"),
        line_col = "black",
        text_family = "ArcherPro Book"
      )
    )
  thisYrAllVTR_plot
  ggsave(paste(i,"_Scallop_VTR.png",sep=""),thisYrAllVTR_plot,width=8,height=8,units="in",dpi=300)
  
  # Compare full VTR to our product
  #png(paste(i,"_Scallop_comparison_scatter.png"))
  #yr_comp_scatter<-MADscatterplot(thisYrFULL, allVTRscallopThisYr, strata = NULL)
  #plot(yr_comp_scatter)
  #dev.off()
  
  allVTRscallopThisYr <- crop(allVTRscallopThisYr,thisYrFULL) 
  thisYrDiff <- thisYrFULL - allVTRscallopThisYr
  
  thisYrDiff_plot<-ggplot() +
    geom_spatraster(data = thisYrDiff) +
    scale_fill_whitebox_c(
      palette = "muted",
      labels = scales::label_number(prefix = "$"),
      n.breaks = 12,
      guide = guide_legend(reverse = TRUE)
    ) +
    labs(
      fill = "",
      title = "Difference in Ex-vessel Value",
      subtitle = i
    ) + 
    geom_spatvector(data = land, fill = "gray") +
    geom_spatvector(data = leases, fill = NA) + 
    theme_classic() + 
    scale_x_continuous(expand = c(0, 0),limits=c(xmin(ext(thisYrDiff)),xmax(ext(thisYrDiff)))) +
    scale_y_continuous(expand = c(0, 0),limits=c(ymin(ext(thisYrDiff)),ymax(ext(thisYrDiff)))) +
    coord_sf(xlim=c(xmin(ext(thisYrDiff)),xmax(ext(thisYrDiff))),ylim=c(ymin(ext(thisYrDiff)),ymax(ext(thisYrDiff))), crs = "+proj=aea +lat_0=40 +lon_0=-96 +lat_1=28 +lat_2=42 +x_0=0 +y_0=0 +datum=NAD83 +units=m
           +nodefs") +    
    # Add scale and North arrow
    ggspatial::annotation_scale(
      location = "tl",
      bar_cols = c("black", "white"),
      text_family = "ArcherPro Book"
    ) +
    ggspatial::annotation_north_arrow(
      location = "tl", which_north = "true",
      pad_x = unit(0.1, "in"), pad_y = unit(0.4, "in"),
      style = ggspatial::north_arrow_nautical(
        fill = c("grey40", "white"),
        line_col = "black",
        text_family = "ArcherPro Book"
      )
    )
  thisYrDiff_plot
  ggsave(paste(i,"_Scallop_Diff.png",sep=""),thisYrDiff_plot,width=8,height=8,units="in",dpi=300)
  print(paste(i," Moran's I: ",autocor(thisYrDiff, method="moran", global=TRUE),sep = ""))
  
  remove(yrDat,yrDatVect,yrAisVmsRast,thisYrFULL,uncovVTRscallopThisYr,allVTRscallopThisYr,thisYrDiff)

  }

# Make combined plots

# All years combined
allYrs_comparison<-plot_grid(allYrsAISVMSVTR_plot,allYrsAllVTR_plot,diff_plot,ncol=3)
allYrs_comparison
ggsave("Comparisons_Scallop_AllYrs.png",allYrs_comparison,width=24,height=8,units="in",dpi=300)

# Combined plot showing each year comparison
a=0
plot.list = list()
for (i in Years){
  yrDat<-subset(aisVmsScalOnly,Year==i)
  yrDatVect<-vect(yrDat,geom=c("LON","LAT"),crs="+proj=longlat")
  yrDatVect<-project(yrDatVect,crs(empty))
  yrAisVmsRast<-rasterize(yrDatVect,empty,field='Point_Value',fun=sum)

  # Add to the VTR layer
  uncovVTRscallopThisYr <- terra::rast(paste("/work/pi_pengfei_liu_uri_edu/Scallop/VTR/Compiled_VTR_Rasters/",i,"_ScallopVTR.tif",sep=""))
  thisYrFULL <- terra::mosaic(yrAisVmsRast, uncovVTRscallopThisYr, fun=sum)

  a<-a+1
  
  thisYrAISVMSVTR_plot<-ggplot() +
    geom_spatraster(data = thisYrFULL) +
    scale_fill_whitebox_c(
      palette = "viridi",
      labels = scales::label_number(prefix = "$"),
      n.breaks = 12,
      guide = guide_legend(reverse = TRUE)
    ) +
    labs(
      fill = "",
    ) + 
    geom_spatvector(data = land, fill = "gray") +
    geom_spatvector(data = leases, fill = NA) + 
    theme_classic() + 
    scale_x_continuous(expand = c(0, 0),limits=c(xmin(ext(thisYrFULL)),xmax(ext(thisYrFULL)))) +
    scale_y_continuous(expand = c(0, 0),limits=c(ymin(ext(thisYrFULL)),ymax(ext(thisYrFULL)))) +
    coord_sf(xlim=c(xmin(ext(thisYrFULL)),xmax(ext(thisYrFULL))),ylim=c(ymin(ext(thisYrFULL)),ymax(ext(thisYrFULL))), crs = "+proj=aea +lat_0=40 +lon_0=-96 +lat_1=28 +lat_2=42 +x_0=0 +y_0=0 +datum=NAD83 +units=m
           +nodefs") +
    # Add scale and North arrow
    ggspatial::annotation_scale(
      location = "tl",
      bar_cols = c("black", "white"),
      text_family = "ArcherPro Book"
    ) +
    ggspatial::annotation_north_arrow(
      location = "tl", which_north = "true",
      pad_x = unit(0.1, "in"), pad_y = unit(0.4, "in"),
      style = ggspatial::north_arrow_nautical(
        fill = c("grey40", "white"),
        line_col = "black",
        text_family = "ArcherPro Book"
      )
    )

  plot.list[[a]]<-thisYrAISVMSVTR_plot
  
  # Plot out full VTR rasters (ALL TRIPS)
  allVTRscallopThisYr <- terra::rast(paste("/work/pi_pengfei_liu_uri_edu/Scallop/VTR/Compiled_VTR_Rasters/",i,"_ALL_ScallopVTR.tif",sep=""))

  a<-a+1
  
  thisYrAllVTR_plot<-ggplot() +
    geom_spatraster(data = allVTRscallopThisYr) +
    scale_fill_whitebox_c(
      palette = "viridi",
      labels = scales::label_number(prefix = "$"),
      n.breaks = 12,
      guide = guide_legend(reverse = TRUE)
    ) +
    labs(
      fill = "",
    ) + 
    geom_spatvector(data = land, fill = "gray") +
    geom_spatvector(data = leases, fill = NA) + 
    theme_classic() + 
    scale_x_continuous(expand = c(0, 0),limits=c(xmin(ext(allVTRscallopThisYr)),xmax(ext(allVTRscallopThisYr)))) +
    scale_y_continuous(expand = c(0, 0),limits=c(ymin(ext(allVTRscallopThisYr)),ymax(ext(allVTRscallopThisYr)))) +
    coord_sf(xlim=c(xmin(ext(allVTRscallopThisYr)),xmax(ext(allVTRscallopThisYr))),ylim=c(ymin(ext(allVTRscallopThisYr)),ymax(ext(allVTRscallopThisYr))), crs = "+proj=aea +lat_0=40 +lon_0=-96 +lat_1=28 +lat_2=42 +x_0=0 +y_0=0 +datum=NAD83 +units=m
           +nodefs") +
    # Add scale and North arrow
    ggspatial::annotation_scale(
      location = "tl",
      bar_cols = c("black", "white"),
      text_family = "ArcherPro Book"
    ) +
    ggspatial::annotation_north_arrow(
      location = "tl", which_north = "true",
      pad_x = unit(0.1, "in"), pad_y = unit(0.4, "in"),
      style = ggspatial::north_arrow_nautical(
        fill = c("grey40", "white"),
        line_col = "black",
        text_family = "ArcherPro Book"
      )
    )

  plot.list[[a]]<-thisYrAllVTR_plot
  
  # Compare full VTR to our product
  allVTRscallopThisYr <- crop(allVTRscallopThisYr,thisYrFULL) 
  thisYrDiff <- thisYrFULL - allVTRscallopThisYr
  
  a<-a+1
  
  thisYrDiff_plot<-ggplot() +
    geom_spatraster(data = thisYrDiff) +
    scale_fill_whitebox_c(
      palette = "viridi",
      labels = scales::label_number(prefix = "$"),
      n.breaks = 12,
      guide = guide_legend(reverse = TRUE)
    ) +
    labs(
      fill = "",
    ) + 
    geom_spatvector(data = land, fill = "gray") +
    geom_spatvector(data = leases, fill = NA) + 
    theme_classic() + 
    scale_x_continuous(expand = c(0, 0),limits=c(xmin(ext(thisYrDiff)),xmax(ext(thisYrDiff)))) +
    scale_y_continuous(expand = c(0, 0),limits=c(ymin(ext(thisYrDiff)),ymax(ext(thisYrDiff)))) +
    coord_sf(xlim=c(xmin(ext(thisYrDiff)),xmax(ext(thisYrDiff))),ylim=c(ymin(ext(thisYrDiff)),ymax(ext(thisYrDiff))), crs = "+proj=aea +lat_0=40 +lon_0=-96 +lat_1=28 +lat_2=42 +x_0=0 +y_0=0 +datum=NAD83 +units=m
           +nodefs") +    
    # Add scale and North arrow
    ggspatial::annotation_scale(
      location = "tl",
      bar_cols = c("black", "white"),
      text_family = "ArcherPro Book"
    ) +
    ggspatial::annotation_north_arrow(
      location = "tl", which_north = "true",
      pad_x = unit(0.1, "in"), pad_y = unit(0.4, "in"),
      style = ggspatial::north_arrow_nautical(
        fill = c("grey40", "white"),
        line_col = "black",
        text_family = "ArcherPro Book"
      )
    )

  plot.list[[a]]<-thisYrDiff_plot
  
  remove(yrDat,yrDatVect,yrAisVmsRast,thisYrFULL,uncovVTRscallopThisYr,allVTRscallopThisYr,thisYrDiff)
  
}

png("YearByYear.png",width=22,height=26,units='in',res=300)
grid.arrange(grobs=plot.list, 
             ncol=3, nrow = 4)
dev.off()

### Check that AIS+VMS+VTR = All VTR values
app(output,fun=sum)

################################################################################

### Repeat all years plot but adjusting color scales

allYrsAISVMSVTR_plot2<-ggplot() +
  geom_spatraster(data = allYrsFULL) +
  scale_fill_whitebox_c(
    palette = "viridi",
    labels = scales::label_number(prefix = "$"),
    n.breaks = 8,
    guide = guide_legend(reverse = TRUE),
    limits = range(500, 326103.1)
  ) +
  labs(
    fill = "",
    title = "Scallop Ex-vessel Value (AIS + VMS + VTR)",
  ) + 
  scale_x_continuous(expand = c(0, 0),limits=c(xmin(ext(allYrsFULL)),xmax(ext(allYrsFULL)))) +
  scale_y_continuous(expand = c(0, 0),limits=c(ymin(ext(allYrsFULL)),ymax(ext(allYrsFULL)))) +
  geom_spatvector(data = land, fill = "gray") +
  geom_spatvector(data = leases, fill = NA) + 
  theme_classic() + 
  coord_sf(xlim=c(xmin(ext(allYrsFULL)),xmax(ext(allYrsFULL))),ylim=c(ymin(ext(allYrsFULL)),ymax(ext(allYrsFULL))), crs = "+proj=aea +lat_0=40 +lon_0=-96 +lat_1=28 +lat_2=42 +x_0=0 +y_0=0 +datum=NAD83 +units=m
           +nodefs") +
  # Add scale and North arrow
  ggspatial::annotation_scale(
    location = "tl",
    bar_cols = c("black", "white"),
    text_family = "ArcherPro Book"
  ) +
  ggspatial::annotation_north_arrow(
    location = "tl", which_north = "true",
    pad_x = unit(0.1, "in"), pad_y = unit(0.4, "in"),
    style = ggspatial::north_arrow_nautical(
      fill = c("grey40", "white"),
      line_col = "black",
      text_family = "ArcherPro Book"
    )
  )
allYrsAISVMSVTR_plot2
ggsave("allYrs_Scallop_AIS_VMS_VTR_2.png",allYrsAISVMSVTR_plot2,width=8,height=8,units="in",dpi=300)


# Plot out full VTR rasters (ALL TRIPS)
allYrsAllVTR_plot2<-ggplot() +
  geom_spatraster(data = allVTRscallopAllYrs) +
  scale_fill_whitebox_c(
    palette = "viridi",
    labels = scales::label_number(prefix = "$"),
    n.breaks = 8,
    guide = guide_legend(reverse = TRUE),
    limits = range(500, 326103.1) # Range from AIS+VMS+VTR to have same scale
  ) +
  labs(
    fill = "",
    title = "Ex-vessel Value (All VTR)",
  ) + 
  geom_spatvector(data = land, fill = "gray") +
  geom_spatvector(data = leases, fill = NA) + 
  theme_classic() + 
  scale_x_continuous(expand = c(0, 0),limits=c(xmin(ext(allVTRscallopAllYrs)),xmax(ext(allVTRscallopAllYrs)))) +
  scale_y_continuous(expand = c(0, 0),limits=c(ymin(ext(allVTRscallopAllYrs)),ymax(ext(allVTRscallopAllYrs)))) +
  coord_sf(xlim=c(xmin(ext(allVTRscallopAllYrs)),xmax(ext(allVTRscallopAllYrs))),ylim=c(ymin(ext(allVTRscallopAllYrs)),ymax(ext(allVTRscallopAllYrs))), crs = "+proj=aea +lat_0=40 +lon_0=-96 +lat_1=28 +lat_2=42 +x_0=0 +y_0=0 +datum=NAD83 +units=m
           +nodefs") +
  # Add scale and North arrow
  ggspatial::annotation_scale(
    location = "tl",
    bar_cols = c("black", "white"),
    text_family = "ArcherPro Book"
  ) +
  ggspatial::annotation_north_arrow(
    location = "tl", which_north = "true",
    pad_x = unit(0.1, "in"), pad_y = unit(0.4, "in"),
    style = ggspatial::north_arrow_nautical(
      fill = c("grey40", "white"),
      line_col = "black",
      text_family = "ArcherPro Book"
    )
  )
allYrsAllVTR_plot2
ggsave("AllYrs_ALL_Scallop_VTR_2.png",allYrsAllVTR_plot2,width=8,height=8,units="in",dpi=300)

diff_plot2<-ggplot() +
  geom_spatraster(data = allYrsDiff) +
  scale_fill_whitebox_c(
    palette = "muted",
    labels = scales::label_number(prefix = "$"),
    n.breaks = 8,
    guide = guide_legend(reverse = TRUE),
    limits = range(500, 326103.1)
  ) +
  scale_x_continuous(expand = c(0, 0),limits=c(xmin(ext(allYrsDiff)),xmax(ext(allYrsDiff)))) +
  scale_y_continuous(expand = c(0, 0),limits=c(ymin(ext(allYrsDiff)),ymax(ext(allYrsDiff)))) +
  coord_sf(xlim=c(xmin(ext(allYrsDiff)),xmax(ext(allYrsDiff))),ylim=c(ymin(ext(allYrsDiff)),ymax(ext(allYrsDiff))), crs = "+proj=aea +lat_0=40 +lon_0=-96 +lat_1=28 +lat_2=42 +x_0=0 +y_0=0 +datum=NAD83 +units=m
           +nodefs") +
  labs(
    fill = "",
    title = "Difference in Ex-vessel Value",
  ) + 
  geom_spatvector(data = land, fill = "gray") +
  geom_spatvector(data = leases, fill = NA) + 
  theme_classic() + 
  # Add scale and North arrow
  ggspatial::annotation_scale(
    location = "tl",
    bar_cols = c("black", "white"),
    text_family = "ArcherPro Book"
  ) +
  ggspatial::annotation_north_arrow(
    location = "tl", which_north = "true",
    pad_x = unit(0.1, "in"), pad_y = unit(0.4, "in"),
    style = ggspatial::north_arrow_nautical(
      fill = c("grey40", "white"),
      line_col = "black",
      text_family = "ArcherPro Book"
    )
  )
diff_plot2
ggsave(paste("AllYrs_Scallop_Diff_2.png",sep=""),diff_plot2,width=8,height=8,units="in",dpi=300)

# All years combined
allYrs_comparison2<-plot_grid(allYrsAISVMSVTR_plot2,allYrsAllVTR_plot2,diff_plot2,ncol=3,labels=c('A', 'B','C'),label_size=20)
ggsave("Comparisons_Scallop_AllYrs_2.png",allYrs_comparison2,width=24,height=8,units="in",dpi=300)
