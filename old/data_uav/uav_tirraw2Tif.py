import numpy as np
import matplotlib.pyplot as plt
import cv2
import os
import struct
import PIL.Image as Image

'''
将热红外原始图像保存为tif格式
'''

def getFileName(file_dir,ref):
        L=[]
        for root, dirs, files in os.walk(file_dir):
            for file in files:
                if os.path.splitext(file)[1] == ref:
                    L.append(os.path.join(root, file))
        return L

def readimage(infile,ns,nl,nb):
    fb = open(infile,'rb')
    mydata = np.zeros((ns,nl,nb))
    for kb in range(nb):
        for ks in range(ns):
            for kl in range(nl):
                arr = fb.read(2)
                elem = struct.unpack('h',arr)[0]
                mydata[ks][kl][kb] = elem
    return mydata

fileDir = r"E:\20211414chengde\rawdata\14\TIR\DIR003\MID000\\"

# read and save as tif
fileNames=getFileName(fileDir,'.raw')
fileNum = len(fileNames)
#fileNum = 3
im=[]
off = 0

# for i in range(fileNum):
for i in range(fileNum):

    infile = fileNames[i+off]
    print(infile)
    fsize = os.path.getsize(infile)
    fsize = fsize / float(1024)
    if (fsize < 25) :
        continue
    img0 = readimage(infile, 512, 640, 1)[:, :, 0]
    outfile = os.path.splitext(infile)[0] + '.tif'
    img0 = np.uint16(img0)
    cv2.imwrite(outfile,img0)

