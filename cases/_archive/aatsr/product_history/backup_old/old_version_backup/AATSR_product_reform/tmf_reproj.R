rm(list = ls())


library(data.table)
library(dplyr)
library(tidyr)
library(terra)
library(stringr)
library(ggplot2)
library(data.table)
library(pracma)

# setwd('./work/ship_lscteco/')
library(parallel)
detectCores()

indir<-"/media/hero/forproart/raw/TMF_/forobs/products/tmf_v1/AnnualChange/"
infiles<- list.files(indir,"*tif",recursive = TRUE,full.names = TRUE)
outdir<- "/media/hero/forproart/raw/TMF_new/"

quick_class<-function(x){
  
  if(any(is.na(x))==TRUE){
    return(0)
  }
  
  # freq_table<-terra::freq(x)
  freq_table<-table(factor(x,levels=0:6))
  
  f_c<-sum(freq_table[2:5])
  if(f_c < 2125){
    return(0)
  }
  if(freq_table[2] >= 2125){
    return(1)
  }else if(freq_table[4]>125){
    return(3)
  }else if(freq_table[5]>125){
    return(4)
  }else if(freq_table[3]>125){
    return(2)
  }else{
    return(0)
  }
  return(0)
}


for(k in 1:length(infiles))
{
  
  

  infile<-infiles[k]
  outfile <- paste0(outdir,basename(infile))
  if(file.exists(outfile) == TRUE) next
  print(infiles[k])
  data<-rast(infiles[k])

  data_new <- aggregate(data,fact=50,fun=quick_class,cores=100)
  writeRaster(x=data_new, filename=outfile, overwrite=FALSE)
  
  
}
# print(infiles)
# 
# raster_list <- lapply(infiles, rast)
# mosaic_raster <- do.call(mosaic, c(raster_list, fun = mean))
# 
# writeRaster(mosaic_raster, "mosaic_output.tif", overwrite = TRUE)
