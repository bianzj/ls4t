from __future__ import annotations

from dataclasses import dataclass
from enum import IntFlag
from pathlib import Path
import hashlib
import os
import numpy as np

# 修改本段和文件末尾 main() 即可；所有科学函数均已复制到本文件。
CASE_ROOT = Path(__file__).resolve().parent
USE_DEMO = True  # 合成演示。真实运行时改 False，并填写下面的 NPZ 文件。
INPUT_FILES = []  # 相对路径以 DATA_ROOT 为基准，也接受绝对路径。
CASE_ID = CASE_ROOT.name  # 多个同名任务时改成不同标识。
DATA_ROOT = Path(os.environ["LS4T_DATA_ROOT"]) / CASE_ID if os.environ.get("LS4T_DATA_ROOT") else None
OUTPUT_DIR = Path(os.environ["LS4T_PRODUCT_ROOT"]) / CASE_ID if os.environ.get("LS4T_PRODUCT_ROOT") else None

from datetime import date, datetime
from numbers import Real
from types import MappingProxyType
from typing import Mapping
import re
from numpy import abs
from scipy.optimize import minimize


# Source snapshot: base/quality.py:10 (QualityFlag)
class QualityFlag(IntFlag):
    GOOD = 0
    INPUT_INVALID = 1 << 0
    CLOUD = 1 << 1
    OUT_OF_RANGE = 1 << 2
    RETRIEVAL_FAILED = 1 << 3
    ILL_CONDITIONED = 1 << 4
    NORMALIZATION_FAILED = 1 << 5
    PROFILE_MISMATCH = 1 << 6
    FUSION_REJECTED = 1 << 7
    LOW_SUPPORT = 1 << 8


# Source snapshot: base/quality.py:23 (INVALID_FLAGS)
INVALID_FLAGS = (
    QualityFlag.INPUT_INVALID
    | QualityFlag.CLOUD
    | QualityFlag.OUT_OF_RANGE
    | QualityFlag.RETRIEVAL_FAILED
    | QualityFlag.NORMALIZATION_FAILED
    | QualityFlag.PROFILE_MISMATCH
    | QualityFlag.LOW_SUPPORT
)


# Source snapshot: base/quality.py:34 (new_flags)
def new_flags(shape: tuple[int, ...]) -> np.ndarray:
    return np.zeros(shape, dtype=np.uint16)


# Source snapshot: base/quality.py:38 (set_flag)
def set_flag(flags: np.ndarray, mask: np.ndarray, flag: QualityFlag) -> None:
    flags[np.asarray(mask, dtype=bool)] |= np.uint16(flag)


# Source snapshot: base/quality.py:42 (usable)
def usable(flags: np.ndarray, reject: QualityFlag = INVALID_FLAGS) -> np.ndarray:
    return (np.asarray(flags, dtype=np.uint16) & np.uint16(reject)) == 0


# Source snapshot: base/normalization/_fit.py:7 (fit_linear)
def fit_linear(design, target, weights):
    """Require residual degrees of freedom and an identifiable weighted model."""
    if len(target) <= design.shape[1]:
        raise ValueError("insufficient samples for an identifiable model with residual degrees of freedom")
    root = np.sqrt(weights / np.max(weights))
    matrix = design * root[:, None]
    scale = np.linalg.norm(matrix, axis=0)
    if np.any(scale == 0):
        raise ValueError("rank deficient model: predictors do not identify coefficients")
    matrix = matrix / scale
    solution, _, rank, singular = np.linalg.lstsq(matrix, target * root, rcond=None)
    if rank < design.shape[1] or singular[0] / singular[-1] > 1e10:
        raise ValueError("rank deficient or ill-conditioned model")
    coefficients = solution / scale
    residual = target - design @ coefficients
    rmse = float(np.sqrt(np.average(residual**2, weights=weights)))
    return coefficients, rmse


# Source snapshot: base/normalization/_validation.py:7 (quality_flags)
def quality_flags(values):
    """Never turn missing/fractional/out-of-range QA values into GOOD by casting."""
    values = np.asarray(values, dtype=float)
    valid = np.isfinite(values) & (values >= 0) & (values <= 65535) & (values == np.floor(values))
    return np.where(valid, values, int(QualityFlag.INPUT_INVALID)).astype(np.uint16)


# Source snapshot: base/kernel.py:12 (kernel_Vin)
def kernel_Vin(vza):
    '''
    Vinnikov emissivity
    :param vza:
    :return: Vin 核值
    '''
    Kvin = 1 - np.cos(np.deg2rad(vza))
    return Kvin


# Source snapshot: base/kernel.py:22 (kernel_LiDense)
def kernel_LiDense(vza,sza,raa, h = 2, r = 1, b = 1):
    '''

    :param vza:
    :param sza:
    :param raa:
    :return:
    '''
    ind = raa > 180
    raa[ind] = 360 - raa[ind]

    ### 椭球到球体的转换
    vza = np.arctan(b/r * np.tan(np.deg2rad(vza))) * 180 / np.pi
    sza = np.arctan(b / r * np.tan(np.deg2rad(sza))) * 180 / np.pi

    cthetv = np.cos(np.deg2rad(vza))
    sthetv = np.sin(np.deg2rad(vza))
    cthets = np.cos(np.deg2rad(sza))
    sthets = np.sin(np.deg2rad(sza))
    cphivs = np.cos(np.deg2rad(raa))
    sphivs = np.sin(np.deg2rad(raa))
    tgths = np.tan(np.deg2rad(sza))
    tgthv = np.tan(np.deg2rad(vza))

    calpha =cthets * cthetv + sthetv * sthets * cphivs
    DD = np.power(tgths, 2) + np.power(tgthv, 2) - 2 * tgths * tgthv * cphivs
    DD[DD < 0] = 0
    D = np.sqrt(DD)

    cost = h / b  *np.sqrt(D * D + np.power(tgthv * tgths * sphivs, 2)) / (1.0 / cthets + 1.0 / cthetv)
    cost[cost < -1] = -0.999
    cost[cost > 1] = 0.999

    t = np.arccos(cost)
    O = (1 / np.pi) * (t - np.sin(t) * np.cos(t)) * (1.0 / cthets + 1.0 / cthetv)
    Kli = (1 + calpha) * (1.0 / cthets * 1.0 / cthetv) / (1.0 / cthetv + 1 / cthets - O) - 2
    ### 热点消除
    # Kli[sza >= 75] = 0
    return Kli


# Source snapshot: base/kernel.py:63 (kernel_LiSparse)
def kernel_LiSparse(vza, sza, raa, h = 2, r = 1, b = 1):
    '''

    :param vza:
    :param sza:
    :param raa:
    :return:
    '''
    ind = raa > 180
    raa[ind] = 360 - raa[ind]

    ### 椭球到球体的转换
    vza = np.arctan(b/r * np.tan(np.deg2rad(vza))) * 180 / np.pi
    sza = np.arctan(b / r * np.tan(np.deg2rad(sza))) * 180 / np.pi

    cthetv = np.cos(np.deg2rad(vza))
    sthetv = np.sin(np.deg2rad(vza))
    cthets = np.cos(np.deg2rad(sza))
    sthets = np.sin(np.deg2rad(sza))
    cphivs = np.cos(np.deg2rad(raa))
    sphivs = np.sin(np.deg2rad(raa))
    tgths = np.tan(np.deg2rad(sza))
    tgthv = np.tan(np.deg2rad(vza))


    DD = np.power(tgths, 2) + np.power(tgthv, 2) - 2 * tgths * tgthv * cphivs
    DD[DD < 0] = 0
    D = np.sqrt(DD)
    cost = h / b * np.sqrt(D * D + np.power(tgthv * tgths * sphivs, 2)) / (1.0 / cthets + 1.0 / cthetv)
    cost[cost < -1] = -0.999
    cost[cost > 1] = 0.999
    calpha = cthetv * cthets + sthetv * sthets * cphivs
    t = np.arccos(cost)
    O = (1 / np.pi) * (t - np.sin(t) * np.cos(t)) * (1.0 / cthets + 1.0 / cthetv)
    Kli = O - 1.0/cthetv - 1.0/cthets + 0.5*(1+calpha) *(1.0/cthets)*(1.0/cthetv)

    ### 热点消除
    # Kli[sza >= 75] = 0

    return Kli


# Source snapshot: base/kernel.py:105 (kernel_Solar)
def kernel_Solar(vza,sza,raa):
    '''
    vinnikov solar
    :param vza:
    :param sza:
    :param raa:
    :return:
    '''
    ind = raa > 180
    raa[ind] = 360 - raa[ind]
    thetas = np.deg2rad(sza)
    thetaa = np.deg2rad(raa)
    thetav = np.deg2rad(abs(vza))
    kz = np.zeros(np.size(vza))
    kz[:] = 1.0
    ua = np.cos(thetaa)
    uv = np.cos(thetav)
    us = np.cos(thetas)
    vv = np.sin(thetav)
    vs = np.sin(thetas)
    kS = vv*vs*us*ua*np.cos(thetas-thetav)
    return kS


# Source snapshot: base/kernel.py:129 (kernel_RLf)
def kernel_RLf(vza,sza,raa):
    '''
    Roujean hotspot angular distance function
    :param vza:
    :param sza:
    :param raa:
    :return:
    '''
    tgths = np.tan(np.deg2rad(sza))
    tgthv = np.tan(np.deg2rad(vza))
    cphivs = np.cos(np.deg2rad(raa))
    f = np.sqrt((np.power(tgthv, 2) + np.power(tgths, 2) - 2 * tgths * tgthv * cphivs))
    return f


# Source snapshot: base/kernel.py:144 (kernel_LSF_analytical)
def kernel_LSF_analytical(vza):
    '''
    一种LSF核的参数化方案
    :param vza: 观测天顶角
    :return: LSF核值
    '''
    ### 这个参数化方案是JL.Roujean 提出的
    cthetv = np.cos(np.deg2rad(vza))
    kLSF = 0.069*cthetv*cthetv-0.215*cthetv+1.176
    return kLSF


# Source snapshot: base/kernel.py:156 (kernel_LSF)
def kernel_LSF(vza):
    '''
    LSF核的原始计算方法
    :param vza: 观测天顶角
    :return: LSF核
    '''
    ### 这个方案是Su. 提出的，对hapke的简化，考虑了上层和下层间的差异
    cthetv = np.cos(np.deg2rad(vza))
    kLSF = ((1 + 2 * cthetv) / (np.sqrt(0.96) + 2 * 0.96 * cthetv) - 0.25 * cthetv
            / (1 + 2 * cthetv) + 0.15 * (1 - np.exp(-0.75 / cthetv)))
    return kLSF


# Source snapshot: base/kernel.py:169 (kernel_TLSF)
def kernel_TLSF(vza,w=0.10):
    '''
    LSF核的原始计算方法
    :param vza: 观测天顶角
    :return: LSF核
    '''
    ### 这个方案是Su. 提出的，对hapke的简化，考虑了上层和下层间的差异
    cthetv = np.cos(np.deg2rad(vza))
    kLSF = ((1 + 2 * cthetv) / (np.sqrt(1-w) + 2 * np.sqrt(1-w) * cthetv) - 0.25 * cthetv
            / (1 + 2 * cthetv))
    return kLSF


# Source snapshot: base/kernel.py:182 (kernel_VLSF)
def kernel_VLSF(vza,w=0.15):
    '''
    LSF核的原始计算方法
    :param vza: 观测天顶角
    :return: LSF核
    '''
    ### 这个方案是Su. 提出的，对hapke的简化，考虑了上层和下层间的差异
    cthetv = np.cos(np.deg2rad(vza))
    kLSF = ((1 + 2 * cthetv) / (np.sqrt(1-w) + 2 * np.sqrt(1-w) * cthetv) - 0.25 * cthetv
            / (1 + 2 * cthetv))
    return kLSF


# Source snapshot: base/kernel.py:195 (kernel_Thapke)
def kernel_Thapke(vza,w=0.10,K=1.0):
    '''
    LSF核的原始计算方法
    :param vza: 观测天顶角
    :return: LSF核
    '''
    ### 这个方案是Su. 提出的，对hapke的简化，考虑了上层和下层间的差异
    cthetv = np.cos(np.deg2rad(vza))
    fa = 2*cthetv/K
    ra = np.sqrt(1-w)
    kLSF = ra*(1+fa)/(1+fa*ra)
    return kLSF


# Source snapshot: base/kernel.py:209 (kernel_RossThick)
def kernel_RossThick(vza, sza, raa):
    '''
    Ross 简化模型，用于多次散射项计算
    :param sza:
    :param vza:
    :param raa:
    :return:
    '''
    ind = raa > 180
    raa[ind] = 360 - raa[ind]
    cthetv = np.cos(np.deg2rad(vza))
    sthetv = np.sin(np.deg2rad(vza))
    cthets = np.cos(np.deg2rad(sza))
    sthets = np.sin(np.deg2rad(sza))
    cphivs = np.cos(np.deg2rad(raa))


    calpha = cthetv * cthets + sthetv * sthets * cphivs
    alpha = np.arccos(calpha)
    salpha = np.sin(alpha)
    Kross = ((np.pi/2.0 - alpha)*calpha + salpha)/(cthetv+cthets)-np.pi/4.0
    return Kross


# Source snapshot: base/kernel.py:233 (kernel_RossThin)
def kernel_RossThin(vza, sza, raa):
    '''
    Ross 简化模型，用于多次散射项计算
    :param sza:
    :param vza:
    :param raa:
    :return:
    '''
    ind = raa > 180
    raa[ind] = 360 - raa[ind]
    cthetv = np.cos(np.deg2rad(vza))
    sthetv = np.sin(np.deg2rad(vza))
    cthets = np.cos(np.deg2rad(sza))
    sthets = np.sin(np.deg2rad(sza))
    cphivs = np.cos(np.deg2rad(raa))

    calpha = cthetv * cthets + sthetv * sthets * cphivs
    alpha = np.arccos(calpha)
    salpha = np.sin(alpha)
    Kross = ((np.pi / 2.0 - alpha) * calpha + salpha) / (cthetv * cthets) - np.pi / 2.0

    return Kross


# Source snapshot: base/normalization/kernels.py:24 (_REGISTRY)
_REGISTRY = {
    'isotropic': (None, True, 'isotropic', {}),
    'vin': (kernel_Vin, True, 'emissivity', {}),
    'lsf': (kernel_LSF, True, 'layer_difference', {}),
    'lsf_analytical': (kernel_LSF_analytical, True, 'layer_difference', {}),
    'tlsf': (kernel_TLSF, True, 'layer_difference', {'w': .10}),
    'vlsf': (kernel_VLSF, True, 'layer_difference', {'w': .15}),
    'thapke': (kernel_Thapke, True, 'layer_difference', {'w': .10, 'K': 1.}),
    'li_dense': (kernel_LiDense, False, 'geometric_optical', {'h': 2., 'r': 1., 'b': 1.}),
    'li_sparse': (kernel_LiSparse, False, 'geometric_optical', {'h': 2., 'r': 1., 'b': 1.}),
    'ross_thick': (kernel_RossThick, False, 'volumetric', {}),
    'ross_thin': (kernel_RossThin, False, 'volumetric', {}),
    'solar': (kernel_Solar, False, 'solar_geometry', {}),
    'rl_distance': (kernel_RLf, False, 'angular_distance', {}),
    'r': (None, False, 'hotspot', {'k': 1.}),
    'rl': (None, False, 'hotspot', {'k': 1.}),
}


# Source snapshot: base/normalization/kernels.py:42 (PRESETS)
PRESETS = MappingProxyType({
    'lsf_li_dense': ('isotropic', 'lsf', 'li_dense'),
    'lsf_li_sparse': ('isotropic', 'lsf', 'li_sparse'),
    'lsf_li_dense_ross_thick': ('isotropic', 'lsf', 'li_dense', 'ross_thick'),
    'ross_thick_li_sparse': ('isotropic', 'ross_thick', 'li_sparse'),
    'ross_thick_li_dense': ('isotropic', 'ross_thick', 'li_dense'),
    'vin_li_dense': ('isotropic', 'vin', 'li_dense'),
    'vin_li_sparse': ('isotropic', 'vin', 'li_sparse'),
    'vin_solar': ('isotropic', 'vin', 'solar'),
    'lsf_r': ('isotropic', 'lsf', 'r'),
    'ross_thick_r': ('isotropic', 'ross_thick', 'r'),
    'vin_r': ('isotropic', 'vin', 'r'),
    'lsf_rl': ('isotropic', 'lsf', 'rl'),
})


# Source snapshot: base/normalization/kernels.py:58 (available_kernels)
def available_kernels() -> dict:
    """Return independent metadata dictionaries, safe for JSON configuration."""
    return {name: {'family': family, 'parameters': dict(defaults)}
            for name, (_, _, family, defaults) in _REGISTRY.items()}


# Source snapshot: base/normalization/kernels.py:64 (KernelTerm)
@dataclass(frozen=True)
class KernelTerm:
    name: str
    parameters: Mapping[str, float] | None = None

    def __post_init__(self):
        if self.name not in _REGISTRY:
            raise ValueError(f'unknown kernel: {self.name}')
        defaults = _REGISTRY[self.name][3]
        supplied = {} if self.parameters is None else dict(self.parameters)
        if supplied.keys() - defaults.keys():
            raise ValueError(f'unknown parameter for {self.name}: {supplied.keys() - defaults.keys()}')
        parameters = {**defaults, **supplied}
        for key, value in parameters.items():
            value = float(value)
            if not np.isfinite(value) or (not 0 <= value < 1 if key == 'w' else value <= 0):
                raise ValueError(f'invalid parameter {self.name}.{key}: {value}')
            parameters[key] = value
        object.__setattr__(self, 'parameters', MappingProxyType(parameters))


# Source snapshot: base/normalization/kernels.py:85 (evaluate_kernel)
def evaluate_kernel(term: KernelTerm | str, vza, sza, raa) -> np.ndarray:
    """Evaluate one kernel without changing input arrays; preserve broadcast shape."""
    term = KernelTerm(term) if isinstance(term, str) else term
    v, s, a = np.broadcast_arrays(*[np.asarray(x, dtype=float) for x in (vza, sza, raa)])
    shape = v.shape
    valid = np.isfinite(v) & (np.abs(v) < 90) & np.isfinite(s) & (s >= 0) & (s < 90) & np.isfinite(a)
    out = np.full(v.size, np.nan)
    mask = valid.ravel()
    if not mask.any():
        return out.reshape(shape)
    v, s, a = v.ravel()[mask].copy(), s.ravel()[mask].copy(), np.mod(a.ravel()[mask], 360.)
    function, view_only, _, _ = _REGISTRY[term.name]
    with np.errstate(all='ignore'):
        if term.name == 'isotropic':
            values = np.ones_like(v)
        elif term.name in ('r', 'rl'):
            f = kernel_RLf(v, s, a)
            values = np.exp(-term.parameters['k'] * f)
            if term.name == 'rl':
                reference = np.exp(-term.parameters['k'] * np.tan(np.deg2rad(s)))
                values = (values-reference)/(1.0001-reference)
        else:
            args = (v,) if view_only else (v, s, a)
            values = function(*args, **term.parameters)
    out[mask] = np.where(np.isfinite(values), values, np.nan)
    return out.reshape(shape)


# Source snapshot: base/normalization/kernels.py:113 (KernelModel)
@dataclass(frozen=True)
class KernelModel:
    """Ordered terms; coefficient order is exactly term order, never implicit."""
    terms: tuple[KernelTerm | str, ...]

    def __post_init__(self):
        terms = tuple(KernelTerm(t) if isinstance(t, str) else t for t in self.terms)
        if not terms or not all(isinstance(t, KernelTerm) for t in terms):
            raise ValueError('model requires KernelTerm objects or kernel names')
        if len({t.name for t in terms}) != len(terms):
            raise ValueError('duplicate kernel names; each term must have a unique name')
        object.__setattr__(self, 'terms', terms)

    def design_matrix(self, vza, sza, raa) -> np.ndarray:
        return np.stack([evaluate_kernel(t, vza, sza, raa) for t in self.terms], axis=-1)

    def to_dict(self) -> dict:
        return {'terms': [{'name': t.name, 'parameters': dict(t.parameters)} for t in self.terms]}

    @classmethod
    def from_dict(cls, config: dict) -> KernelModel:
        return cls(tuple(KernelTerm(**term) for term in config['terms']))


# Source snapshot: base/normalization/kernels.py:137 (kernel_model)
def kernel_model(preset: str) -> KernelModel:
    if preset not in PRESETS:
        raise ValueError(f'unknown kernel preset: {preset}; choices: {list(PRESETS)}')
    return KernelModel(PRESETS[preset])


# Source snapshot: base/normalization/kernels.py:143 (KernelFit)
@dataclass(frozen=True)
class KernelFit:
    model: KernelModel
    coefficients: np.ndarray
    rmse_k: float
    sample_count: int
    solver: str
    success: bool
    message: str

    def predict(self, vza, sza, raa) -> np.ndarray:
        return self.model.design_matrix(vza, sza, raa) @ self.coefficients

    def normalize(self, temperature_k, vza, sza, raa, *, reference_vza=0.,
                  reference_sza=None, reference_raa=0.) -> np.ndarray:
        """Preserve the observed residual; default is nadir at the SAME solar angle."""
        solar = sza if reference_sza is None else reference_sza
        t = np.asarray(temperature_k, dtype=float)
        result = t + self.predict(reference_vza, solar, reference_raa) - self.predict(vza, sza, raa)
        valid = np.isfinite(t) & (t >= 150) & (t <= 400) & np.isfinite(result) & (result >= 150) & (result <= 400)
        return np.where(valid, result, np.nan)


# Source snapshot: base/normalization/kernels.py:166 (_replace_parameters)
def _replace_parameters(model, keys, values):
    changes = dict(zip(keys, values))
    return KernelModel(tuple(KernelTerm(t.name, {k: changes.get(f'{t.name}.{k}', v)
                                               for k, v in t.parameters.items()}) for t in model.terms))


# Source snapshot: base/normalization/kernels.py:172 (fit_kernel_model)
def fit_kernel_model(model: KernelModel, temperature_k, vza, sza, raa, *, weights=1.,
                     quality_flag=0, solver='linear', parameter_bounds=None,
                     method='Powell', options=None) -> KernelFit:
    """Fit ONE co-located/same-state angular sample set, not a mixed image/time pool.

    Linear: all kernel shape parameters are fixed. Minimize: variable projection
    estimates ONLY named shape parameters (e.g. {'rl.k': (0.1, 3.)}); WLS solves
    coefficients at each evaluation. Bounds are mandatory. RMSE is in-sample;
    this function supplies no independent accuracy or posterior uncertainty.
    """
    if solver not in ('linear', 'minimize'):
        raise ValueError('solver must be linear or minimize')
    if solver == 'linear' and parameter_bounds:
        raise ValueError('linear solver holds shape parameters fixed; omit parameter_bounds')
    t, v, s, a, w, flags = np.broadcast_arrays(*[np.asarray(x) for x in
                                               (temperature_k, vza, sza, raa, weights, quality_flag)])
    design = model.design_matrix(v, s, a)
    valid = (np.isfinite(t) & (t >= 150) & (t <= 400) & np.isfinite(w) & (w > 0)
             & usable(quality_flags(flags)) & np.isfinite(design).all(axis=-1))
    t, v, s, a, w = [x[valid].astype(float) for x in (t, v, s, a, w)]
    coefficients, rmse = fit_linear(design[valid], t, w)
    message = 'weighted linear least squares'
    if solver == 'minimize':
        if not parameter_bounds:
            raise ValueError('minimize requires parameter_bounds for shape parameters')
        if method not in ('Powell', 'Nelder-Mead', 'L-BFGS-B', 'SLSQP'):
            raise ValueError('unsupported bounded minimize method')
        current = {f'{term.name}.{k}': value for term in model.terms for k, value in term.parameters.items()}
        keys = list(parameter_bounds)
        if set(keys) - current.keys():
            raise ValueError('bounds reference an unknown model parameter')
        for name in ('li_dense', 'li_sparse'):
            if {f'{name}.{p}' for p in ('h','r','b')}.issubset(keys):
                raise ValueError(f'{name} has an unidentifiable common scale: fix one of h/r/b to fit two ratios')
        bounds = np.asarray([parameter_bounds[k] for k in keys], dtype=float)
        x0 = np.asarray([current[k] for k in keys])
        if bounds.shape != (len(keys), 2) or not np.isfinite(bounds).all() or np.any(bounds[:,0] >= bounds[:,1]):
            raise ValueError('parameter bounds must be finite ordered (lower, upper) pairs')
        _replace_parameters(model, keys, bounds[:,0])
        _replace_parameters(model, keys, bounds[:,1])
        if np.any(x0 < bounds[:,0]) or np.any(x0 > bounds[:,1]):
            raise ValueError('initial shape parameters must lie inside their bounds')
        if len(t) <= len(model.terms) + len(keys):
            raise ValueError('insufficient samples for linear and nonlinear parameters')

        def objective(values):
            candidate = _replace_parameters(model, keys, values)
            matrix = candidate.design_matrix(v, s, a)
            if not np.isfinite(matrix).all():
                return np.inf
            try:
                _, error = fit_linear(matrix, t, w)
            except ValueError:
                return np.inf
            return error**2

        result = minimize(objective, x0, bounds=bounds, method=method, options=options)
        if not result.success or not np.isfinite(result.fun):
            raise RuntimeError(f'kernel optimization failed: {result.message}')
        model = _replace_parameters(model, keys, result.x)
        matrix = model.design_matrix(v, s, a)
        coefficients, rmse = fit_linear(matrix, t, w)
        # Local sensitivity check: an optimizer can "converge" on a flat width.
        jacobian = [matrix]
        for i, value in enumerate(result.x):
            step = max(abs(value), 1.) * 1e-5
            lo, hi = result.x.copy(), result.x.copy()
            lo[i] = max(bounds[i,0], value-step)
            hi[i] = min(bounds[i,1], value+step)
            derivative = ((_replace_parameters(model, keys, hi).design_matrix(v,s,a)
                           - _replace_parameters(model, keys, lo).design_matrix(v,s,a)) @ coefficients)/(hi[i]-lo[i])
            if np.linalg.norm(derivative) < 1e-7:
                raise ValueError('shape parameter is not identifiable (zero sensitivity)')
            jacobian.append(derivative[:,None])
        fit_linear(np.column_stack(jacobian), t, w)
        message = f'{method}: {result.message}'
    coefficients = coefficients.copy()
    coefficients.setflags(write=False)
    return KernelFit(model, coefficients, float(rmse), len(t), solver, True, str(message))


# Source snapshot: base/normalization/annual.py:21 (annual_phase)
def annual_phase(dates_or_doy, *, year_length=365) -> np.ndarray:
    """Map dates or 1-based DOY to [0,1); invalid samples/NaT become NaN.

    Datetime strings must be timezone-free (or already converted to the chosen
    local calendar); this function does not infer timezone/overpass time.
    Multi-year dates align by fraction of each actual calendar year.
    """
    values = np.asarray(dates_or_doy)
    if values.dtype.kind == 'O':
        present = [x for x in values.flat if x is not None]
        if all(isinstance(x, Real) and not isinstance(x, (bool,np.bool_)) for x in present):
            values = values.astype(float)
        elif any(isinstance(x, Real) for x in present):
            raise ValueError('do not mix numeric DOY and calendar dates')
        elif not all(isinstance(x,(date,str,np.datetime64)) for x in present):
            raise ValueError('expected numeric DOY or calendar dates')
    if values.dtype.kind in 'OUS':
        for value in values.flat:
            if isinstance(value, datetime) and value.utcoffset() is not None:
                raise ValueError('timezone-aware dates require explicit conversion to a timezone-free calendar')
            if isinstance(value,(str,bytes)):
                value = value.decode() if isinstance(value,bytes) else value
                if ('T' in value or ' ' in value) and re.search(r'(?:Z|[+-]\d{2}(?::?\d{2})?)$',value):
                    raise ValueError('timezone offsets require explicit conversion to a timezone-free calendar')
                if value != 'NaT' and not re.match(r'^\d{4}-\d{2}-\d{2}(?:$|[T ])',value):
                    raise ValueError('date strings must use ISO YYYY-MM-DD; supply DOY as numbers')
    if values.dtype.kind in 'MmOUS':
        if values.dtype.kind == 'm':
            raise ValueError('timedeltas are not calendar dates')
        dates = values.astype('datetime64[us]')
        years = dates.astype('datetime64[Y]')
        start = years.astype('datetime64[us]')
        end = (years+np.timedelta64(1,'Y')).astype('datetime64[us]')
        with np.errstate(invalid='ignore', divide='ignore'):
            phase = (dates-start)/(end-start)
        return np.where(np.isnat(dates), np.nan, phase).astype(float)
    if values.dtype.kind not in 'iuf':
        raise ValueError('numeric DOY must be real numbers')
    day, length = np.broadcast_arrays(np.asarray(values, dtype=float), np.asarray(year_length, dtype=float))
    if not np.isfinite(length).all() or not np.isin(length, [365,366]).all():
        raise ValueError('numeric DOY year_length must be 365 or 366')
    valid = np.isfinite(day) & (day >= 1) & (day < length+1)
    return np.where(valid, (day-1)/length, np.nan)


# Source snapshot: base/normalization/annual.py:66 (_annual_design)
def _annual_design(phase, harmonics):
    columns = [np.ones_like(phase)]
    for j in range(1,harmonics+1):
        columns.extend((np.cos(2*np.pi*j*phase), np.sin(2*np.pi*j*phase)))
    return np.stack(columns, axis=-1)


# Source snapshot: base/normalization/annual.py:73 (ATCFit)
@dataclass(frozen=True)
class ATCFit:
    coefficients: np.ndarray
    harmonics: int
    rmse_k: float
    sample_count: int
    seasonal_coverage: float

    @property
    def mean_k(self) -> float:
        return float(self.coefficients[0])

    @property
    def amplitudes_k(self) -> np.ndarray:
        return np.hypot(self.coefficients[1::2],self.coefficients[2::2])

    def peak_days(self, year_length=365) -> np.ndarray:
        """First peak of EACH harmonic in [1,1+N/j), not the combined-curve peak.

        Undefined phase of a zero-amplitude harmonic returns NaN.
        """
        if year_length not in (365,366):
            raise ValueError('year_length must be 365 or 366')
        phase = np.mod(np.arctan2(self.coefficients[2::2], self.coefficients[1::2]), 2*np.pi)
        days = 1+phase/(2*np.pi)*year_length/np.arange(1,self.harmonics+1)
        return np.where(self.amplitudes_k > 1e-10, days, np.nan)

    def predict(self, dates_or_doy, *, year_length=365) -> np.ndarray:
        phase = annual_phase(dates_or_doy, year_length=year_length)
        return _annual_design(phase,self.harmonics) @ self.coefficients

    def normalize(self, temperature_k, dates_or_doy, *, reference,
                  year_length=365, reference_year_length=365) -> np.ndarray:
        """Shift season while retaining anomalies; NaN observations remain NaN."""
        t = np.asarray(temperature_k, dtype=float)
        observed = self.predict(dates_or_doy, year_length=year_length)
        target = self.predict(reference, year_length=reference_year_length)
        result = t+target-observed
        valid = np.isfinite(t) & (t >= 150) & (t <= 400) & np.isfinite(result) & (result >= 150) & (result <= 400)
        return np.where(valid,result,np.nan)


# Source snapshot: base/normalization/annual.py:115 (fit_annual_cycle)
def fit_annual_cycle(temperature_k, dates_or_doy, *, harmonics=1, year_length=365,
                     weights=1., quality_flag=0, minimum_coverage=.5) -> ATCFit:
    """Fit one pixel/site at comparable solar time, geometry and spatial support.

    harmonics=1 gives a standard three-coefficient ATC; 2 adds a half-year
    harmonic (five coefficients). Coverage is 1 minus the largest circular
    phase gap, after QA filtering. Repeated years alone do not improve seasonal
    coverage. Each valid sample carries the supplied weight; years are not
    implicitly balanced. A multi-year fit is a shared seasonal climatology.
    """
    if isinstance(harmonics, bool) or harmonics not in (1,2):
        raise ValueError('harmonics must be 1 or 2')
    harmonics = int(harmonics)
    if not np.isfinite(minimum_coverage) or not 0 < minimum_coverage < 1:
        raise ValueError('minimum_coverage must be between 0 and 1')
    phase = annual_phase(dates_or_doy, year_length=year_length)
    t, phase, w, flags = np.broadcast_arrays(*[np.asarray(x) for x in (temperature_k,phase,weights,quality_flag)])
    valid = (np.isfinite(t) & (t >= 150) & (t <= 400) & np.isfinite(phase)
             & np.isfinite(w) & (w > 0) & usable(quality_flags(flags)))
    t, phase, w = t[valid],phase[valid],w[valid]
    if len(t) <= 1+2*harmonics:
        raise ValueError('insufficient samples for ATC with residual degrees of freedom')
    ordered = np.sort(np.unique(phase))
    coverage = float(1-np.max(np.diff(np.r_[ordered,ordered[0]+1])))
    if coverage < minimum_coverage:
        raise ValueError('insufficient seasonal coverage for ATC')
    coefficients, rmse = fit_linear(_annual_design(phase,harmonics),t,w)
    coefficients.setflags(write=False)
    return ATCFit(coefficients,harmonics,float(rmse),len(t),coverage)

# ---------- 案例自己的读写与批次；不调用仓库流程 ----------
def validate_storage():
    if DATA_ROOT is None or OUTPUT_DIR is None:
        raise ValueError("Set LS4T_DATA_ROOT and LS4T_PRODUCT_ROOT, or edit DATA_ROOT/OUTPUT_DIR explicitly")
    # 独立副本只识别目录边界，不导入或调用 LS4T 仓库。
    code_root = CASE_ROOT
    for parent in (CASE_ROOT, *CASE_ROOT.parents):
        if (parent / "base").is_dir() and (parent / "cases").is_dir():
            code_root = parent
            break
    code, data, product = code_root.resolve(), DATA_ROOT.resolve(), OUTPUT_DIR.resolve()
    def overlap(left, right):
        return left.is_relative_to(right) or right.is_relative_to(left)
    if overlap(code, data) or overlap(code, product):
        raise ValueError("Data and products must be outside the code directory")
    if overlap(data, product):
        raise ValueError("Data and products must use separate non-overlapping directories")


def inputs():
    validate_storage()
    if USE_DEMO:
        yield "demo", demo_input(), "synthetic demonstration"
        return
    if not INPUT_FILES:
        raise ValueError("Set INPUT_FILES before running real data")
    paths = [(DATA_ROOT / Path(p)).resolve() for p in INPUT_FILES]
    if any(not p.is_relative_to(DATA_ROOT.resolve()) for p in paths):
        raise ValueError("Inputs must stay within DATA_ROOT")
    if len({p.stem for p in paths}) != len(paths):
        raise ValueError("Input stems must be unique within this batch")
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(path)
        if (OUTPUT_DIR / (path.stem + ".npz")).exists():
            raise FileExistsError("Refusing to overwrite: " + path.stem)
    for path in paths:
        with np.load(path, allow_pickle=False) as data:
            yield path.stem, dict(data), str(path.resolve())


def save_result(name, source, **arrays):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / (name + ".npz")
    # Exclusive creation: repeated runs cannot silently replace an earlier result.
    with path.open("xb") as stream:
        np.savez_compressed(stream, **arrays, synthetic_demo=USE_DEMO,
                            input_source=source,
                            execution_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    print(path)

def demo_input():
    rng = np.random.default_rng(31)
    vza, sza, raa = rng.uniform(0, 65, 140), rng.uniform(15, 60, 140), rng.uniform(0, 360, 140)
    model = KernelModel(("isotropic", "lsf", KernelTerm("rl", {"k": .8})))
    doy = np.arange(1, 366)
    return dict(angular_temperature_k=model.design_matrix(vza, sza, raa) @ [300., 2., 3.],
                view_zenith_deg=vza, solar_zenith_deg=sza, relative_azimuth_deg=raa,
                angular_quality_flag=np.zeros(140, dtype=np.uint16), doy=doy,
                annual_temperature_k=_annual_design(annual_phase(doy), 2) @ [290., -8., 4., 2., 1.],
                annual_quality_flag=np.zeros(365, dtype=np.uint16))


def main():
    for name, data, source in inputs():
        # 两套独立样本：角度拟合同位置/同状态；ATC 拟合统一几何和时刻的年序列。
        # 核组合直接在代码中改。还可选 li_dense/li_sparse、ross_thick 等。
        model = KernelModel(("isotropic", "lsf", KernelTerm("rl", {"k": .8})))
        angular = fit_kernel_model(model, data["angular_temperature_k"],
                    data["view_zenith_deg"], data["solar_zenith_deg"], data["relative_azimuth_deg"],
                    quality_flag=data["angular_quality_flag"], solver="linear")
        # 若拟合形状：solver="minimize", parameter_bounds={"rl.k": (.1, 3.)}
        annual = fit_annual_cycle(data["annual_temperature_k"], data["doy"],
                    quality_flag=data["annual_quality_flag"], harmonics=2)
        # 闰年数值 DOY 应显式 year_length=366；也可用 ISO 日期数组。
        save_result(name, source, kernel_coefficients=angular.coefficients,
                    kernel_rmse_k=angular.rmse_k, atc_coefficients=annual.coefficients,
                    atc_rmse_k=annual.rmse_k, atc_prediction_k=annual.predict(data["doy"]))


if __name__ == "__main__":
    main()
