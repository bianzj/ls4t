"""Canopy radiative-transfer helpers: Planck forward and inverse."""


# ---------------------------------------------------------------------------
# SLSTR case dependencies, moved verbatim from the run project on 2026-09-16
# ---------------------------------------------------------------------------
import numpy as np


def planck(Ts,wavelength=10.8):
    c1 = 11910.439340652
    c2 = 14388.291040407
    if not isinstance(Ts, np.ndarray):
        if (Ts < 100): Ts = Ts + 273.15
        wavelength = float(wavelength)
        Ts = float(Ts)
        rad = c1 / (np.power(wavelength, 5) * (np.exp(c2 / Ts / wavelength) - 1)) * 10000
    else:
        Ts[Ts < 100] = Ts[Ts < 100] + 273.15
        wavelength = float(wavelength)
        rad = c1 / (np.power(wavelength, 5) * (np.exp(c2 / Ts / wavelength) - 1)) * 10000
    return rad


def inv_planck(rad, wavelength= 10.8):
    c1 = 11910.439340652 * 10000
    c2 = 14388.291040407
    temp = c1 / (rad * np.power((wavelength), 5)) + 1
    Ts = c2 / (wavelength * np.log(temp))
    return Ts

