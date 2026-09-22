"""Canopy radiative-transfer helpers: component radiance."""


# ---------------------------------------------------------------------------
# SLSTR case dependencies, moved verbatim from the run project on 2026-09-16
# ---------------------------------------------------------------------------
import numpy as np


def radiance_direct(Ecom,Rcom):
    Ecom =np.asarray(Ecom)
    Rcom = np.asarray(Rcom)
    number_component = np.size(Rcom)
    # Ecom = np.reshape(Ecom, (4, -1))
    # number_angle = np.shape(Ecom)[1]
    # if np.shape(Ecom)[0]==4:
    #     number_angle = 1
    # else:
    #     number_angle = np.shape(Ecom[0])[0]
    # Rcomnew = np.zeros([number_component,number_angle])
    # for k in range(number_component):
    #     Rcomtemp = Rcom[k]
    #     Rcomtemp = np.transpose(np.tile(Rcomtemp,[number_angle,1]))
    #     Rcomnew[k,:] = np.sum(np.asarray(Ecom[k])*Rcomtemp,axis=0)
    Rcomnew = np.asarray([Ecom[k,:]*Rcom[k] for k in range(number_component)])
    Rcomnew = np.sum(Rcomnew,axis=0)
    return Rcomnew


def radiance_scatter(Ecom,Rcom):
    Ecom =np.asarray(Ecom)
    Rcom = np.asarray(Rcom)
    number_component = np.size(Rcom)
    Rcomnew = np.asarray([Ecom[k,:]*Rcom[k] for k in range(number_component)])
    Rcomnew = np.sum(Rcomnew,axis=0)
    return Rcomnew

