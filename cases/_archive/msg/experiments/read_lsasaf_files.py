import os
import sys
import h5py
import argparse


parser = argparse.ArgumentParser(description="example script in python using h5py to access datasets and attributes")
parser.add_argument('full_filename',type=str,help="this is the file you want to open and read")
args = parser.parse_args()

#check if the file passed as agument exists
if (not os.path.isfile(args.full_filename)):
    print("problem: the file %s doesnt exist." % args.full_filename)
    sys.exit(1)
try:
    #open the file in reading mode
    f = h5py.File(args.full_filename,'r')
except:
    print("problem: %s is not a valid hdf5 file" % args.full_filename)
    sys.exit(1)

#get global attributes of the hdf5 file
for attr in f.attrs.keys():
    print("global attribute %s : %s" % (attr,f.attrs[attr]))

#list the hdf5 datasets. It opens like a python dictionary
print("keys: \n%s" % f.keys())

#get dataset shape, datatype, dataset attributes and the dataset itself
for key in f.keys():
    dset= f[key]
    print("Dataset %s shape: %s" % (key,dset.shape))
    print("Dataset %s dtype: %s" % (key,dset.dtype))
    for attr in dset.attrs.keys():
        print("Dataset %s attr %s : %s" % (key,attr,dset.attrs[attr]))
    print(dset)
