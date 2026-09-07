
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


indir<-"/media/hero/forproart/raw/era5_land/"

for(kyear in 1980:2023){

  infiles <- paste0(indir,"ERA5_SKT_",as.character(kyear),".nc")
  data<-rast(infiles)
  
  index<-rep(1:12,24)
  data.max<-tapp(data,index,fun=max,cores=50)
  writeCDF(data.max,paste0(indir,"ERA5_SKT_",as.character(kyear),"_max.nc"))
  data.min<-tapp(data,index,fun=min,cores=50)
  writeCDF(data.min,paste0(indir,"ERA5_SKT_",as.character(kyear),"_min.nc"))
}

# plot(data.max[[1]])
# plot(data.min[[1]])
# 
# temp<-data.max[[1]]-data.min[[1]]
# plot(data.max[[1]]-data.min[[1]])
