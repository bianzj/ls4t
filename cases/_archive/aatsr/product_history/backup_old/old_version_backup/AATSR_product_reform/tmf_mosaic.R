rm(list = ls())


library(data.table)
library(dplyr)
library(tidyr)
library(terra)
library(stringr)
library(ggplot2)
library(data.table)
library(pracma)
library(tidyterra)

library("foreach")
library("doParallel")
library("doRNG")
# setwd('./work/ship_lscteco/')





# indir<-"F:/raw/treecover/"
# infiles<- list.files(indir,"*tif",recursive = TRUE,full.names = TRUE)
# outdir<- "F:/raw/treecover_new/"

# for(k in 1:length(infiles))
# {
# print(infiles[k])
#   infile<-infiles[k]
#   
#   data<-rast(infiles[k])
#   
#   data_new <- aggregate(data,fact=100)
#   
#     
#     outfile <- paste0(outdir,basename(infile))
#   if(file.exists(outfile) == TRUE) next
#   writeRaster(data_new, outfile, overwrite=FALSE)
#   
# }
# print(infiles)



indir<-"F:/raw/TMF_new/"
outdir<-"F:/raw/TMF_new/"
for(kyear in 2023:2023){
  
  mark<- as.character(kyear)
  outfile<-paste0(outdir,"global_",mark,".tif")
  infiles<- list.files(indir,mark,recursive = TRUE,full.names = TRUE)
  raster_list <- lapply(infiles, rast)
  mosaic_raster <- do.call(mosaic, c(raster_list, fun = median))
  writeRaster(mosaic_raster, outfile, overwrite = TRUE)
}
plot(mosaic_raster)

