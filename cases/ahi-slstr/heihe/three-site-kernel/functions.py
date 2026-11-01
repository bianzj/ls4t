"""Standalone LS4T paired thermal kernels; angles in degrees, LST in kelvin.

Formula snapshot: base/kernel.py::kernel_LSF, kernel_RLf and
base/normalization/kernels.py::evaluate_kernel (2026-10-28).
Subtract each kernel's nadir value at the SAME solar angle.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np


def kernel_basis(vza, sza, raa, width=1.):
    if not np.isfinite(width) or width <= 0:
        raise ValueError('hotspot width must be positive')
    v, s, a = np.broadcast_arrays(*[np.asarray(x, float) for x in (vza, sza, raa)])
    valid = np.isfinite(v+s+a) & (v >= 0) & (v < 80) & (s >= 0) & (s < 85)
    v, s, a = np.deg2rad(v), np.deg2rad(s), np.deg2rad(a % 360)
    c = np.cos(v)
    with np.errstate(all='ignore'):
        def lsf(c):
            return (1+2*c)/(np.sqrt(.96)+2*.96*c) - .25*c/(1+2*c) + .15*(1-np.exp(-.75/c))
        distance = np.sqrt(np.maximum(0, np.tan(v)**2 + np.tan(s)**2 - 2*np.tan(v)*np.tan(s)*np.cos(a)))
        ref = np.exp(-width*np.tan(s))
        rl = (np.exp(-width*distance)-ref)/(1.0001-ref)
        basis = np.stack([lsf(c)-lsf(1.), rl], axis=-1)
    return np.where(valid[..., None], basis, np.nan)


def fit_pairs(tn, to, kn, ko, *, weights=None, max_condition=100.):
    """No intercept: difference cancels a distinct isotropic level per pixel.

    Inputs MUST already contain calibration rows only. AHI is not an argument.
    Equal-area observations by default; callers may equalize coarse block weight.
    """
    tn, to = np.asarray(tn, float), np.asarray(to, float)
    x = np.asarray(ko, float)-np.asarray(kn, float)
    if x.ndim != 2 or tn.shape != to.shape or tn.shape != (len(x),):
        raise ValueError('incompatible paired observation shapes')
    w = np.ones(len(x)) if weights is None else np.broadcast_to(np.asarray(weights, float), tn.shape)
    valid = np.isfinite(tn+to+w) & (w > 0) & np.isfinite(x).all(axis=1)
    x, y, w = x[valid], (to-tn)[valid], w[valid]
    if len(y) <= max(x.shape[1], 2):
        raise ValueError('insufficient paired observations')
    root = np.sqrt(w/w.max())
    a = x*root[:, None]; scale = np.linalg.norm(a, axis=0)
    if np.any(scale < 1e-12):
        raise ValueError('rank deficient angular differences')
    scaled = a/scale
    solution, _, rank, singular = np.linalg.lstsq(scaled, y*root, rcond=None)
    condition = float(singular[0]/singular[-1]) if singular[-1] else float('inf')
    if rank != x.shape[1] or condition > max_condition:
        raise ValueError(f'rank deficient or ill-conditioned angular differences: {condition:.3g}')
    beta = solution/scale
    residual = y-x@beta
    return dict(coefficients=beta, condition=condition, count=len(y),
                training_rmse_k=float(np.sqrt(np.average(residual**2, weights=w))),
                gram_inverse=np.linalg.inv(a.T@a), weight_scale=float(w.max()),
                unique_geometry_count=len(np.unique(np.round(x, 7), axis=0)))


def normalize(temperature, basis, coefficients):
    return np.asarray(temperature, float)-np.asarray(basis, float)@np.asarray(coefficients, float)


def normalize_native(temperature, basis, coefficients):
    """Correct each native subpixel, THEN aggregate; return coarse T, dT and max native |dT|."""
    t, k = np.asarray(temperature, float), np.asarray(basis, float)
    delta = -k@np.asarray(coefficients, float)
    corrected = t+delta
    valid = np.isfinite(corrected).all(axis=1) & (corrected >= 220).all(axis=1) & (corrected <= 365).all(axis=1)
    aggregate = radiance_mean(corrected, axis=1)
    aggregate = np.where(valid, aggregate, np.nan)
    return aggregate, aggregate-radiance_mean(t, axis=1), np.max(abs(delta), axis=1)


def decode_hhmm(raw):
    x = np.asarray(raw, float)
    valid = np.isfinite(x) & (x == np.floor(x)) & (x >= 0) & (x < 2400) & (x % 100 < 60)
    return np.where(valid, np.floor(x/100)*60+x % 100, np.nan)


def match_minutes(minutes, tolerance=5):
    minute = np.asarray(minutes, float)
    nearest = np.floor(minute/10+.5)*10
    good = np.isfinite(minute) & (minute >= 0) & (minute < 1440) & (nearest < 1440) & (abs(nearest-minute) <= tolerance)
    return nearest, good


def split_blocks(rows, cols, centre_row, centre_col, block_cells=5):
    br, bc = np.asarray(rows)//block_cells, np.asarray(cols)//block_cells
    dr, dc = abs(br-centre_row//block_cells), abs(bc-centre_col//block_cells)
    out = np.where((br*73856093+bc*19349663) % 4 == 0, 'test', 'train').astype('U6')
    out[np.maximum(dr, dc) <= 1] = 'buffer'
    out[(dr == 0) & (dc == 0)] = 'test'
    return out


def radiance_mean(temperature, axis, wavelength_um=10.85):
    t = np.asarray(temperature, float)
    c2 = 14387.76877
    with np.errstate(all='ignore'):
        radiance = 1/np.expm1(c2/(wavelength_um*t))
        return c2/(wavelength_um*np.log1p(1/np.mean(radiance, axis=axis)))


def geostationary_angles(lon, lat):
    """Nominal Himawari 140.7 E geometry; NOT per-scan navigation."""
    phi, lam = np.deg2rad(lat), np.deg2rad(lon)
    n = 6378137/np.sqrt(1-6.69437999014e-3*np.sin(phi)**2)
    gx, gy, gz = n*np.cos(phi)*np.cos(lam), n*np.cos(phi)*np.sin(lam), n*(1-6.69437999014e-3)*np.sin(phi)
    rayx = 42164000*np.cos(np.deg2rad(140.7))-gx
    rayy = 42164000*np.sin(np.deg2rad(140.7))-gy
    rayz = -gz
    east = -rayx*np.sin(lam)+rayy*np.cos(lam)
    north = -rayx*np.sin(phi)*np.cos(lam)-rayy*np.sin(phi)*np.sin(lam)+rayz*np.cos(phi)
    up = rayx*np.cos(phi)*np.cos(lam)+rayy*np.cos(phi)*np.sin(lam)+rayz*np.sin(phi)
    return np.rad2deg(np.arctan2(np.hypot(east, north), up)), np.rad2deg(np.arctan2(east, north)) % 360


def metrics(difference):
    d = np.asarray(difference, float); d = d[np.isfinite(d)]
    if not len(d):
        return dict(n=0, bias_k=None, rmse_k=None, mae_k=None)
    return dict(n=len(d), bias_k=float(d.mean()), rmse_k=float(np.sqrt(np.mean(d*d))), mae_k=float(np.mean(abs(d))))


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda: f.read(4*1024*1024), b''):
            h.update(part)
    return h.hexdigest()


def write_json(path, data):
    def encode(value):
        if isinstance(value, np.ndarray): return value.tolist()
        if isinstance(value, np.generic): return value.item()
        if isinstance(value, Path): return str(value)
        raise TypeError(type(value).__name__)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2, default=encode, allow_nan=False), encoding='utf-8')
