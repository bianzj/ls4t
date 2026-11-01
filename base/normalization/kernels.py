"""Composable angular kernels, fixed-shape WLS and bounded shape fitting.

Angles are degrees; temperature is kelvin. Legacy formulas remain in
base.kernel. Adapters broadcast, copy and flatten inputs so legacy kernels
cannot mutate the caller's relative azimuth arrays. Geometry is daylight:
abs(VZA) < 90, 0 <= SZA < 90. Nonfinite/invalid geometry evaluates to NaN.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

import numpy as np
from scipy.optimize import minimize

from base import kernel as legacy
from base.quality import usable
from ._fit import fit_linear
from ._validation import quality_flags


# name: (legacy function, view-only, physical role, default shape parameters)
_REGISTRY = {
    'isotropic': (None, True, 'isotropic', {}),
    'vin': (legacy.kernel_Vin, True, 'emissivity', {}),
    'lsf': (legacy.kernel_LSF, True, 'layer_difference', {}),
    'lsf_analytical': (legacy.kernel_LSF_analytical, True, 'layer_difference', {}),
    'tlsf': (legacy.kernel_TLSF, True, 'layer_difference', {'w': .10}),
    'vlsf': (legacy.kernel_VLSF, True, 'layer_difference', {'w': .15}),
    'thapke': (legacy.kernel_Thapke, True, 'layer_difference', {'w': .10, 'K': 1.}),
    'li_dense': (legacy.kernel_LiDense, False, 'geometric_optical', {'h': 2., 'r': 1., 'b': 1.}),
    'li_sparse': (legacy.kernel_LiSparse, False, 'geometric_optical', {'h': 2., 'r': 1., 'b': 1.}),
    'ross_thick': (legacy.kernel_RossThick, False, 'volumetric', {}),
    'ross_thin': (legacy.kernel_RossThin, False, 'volumetric', {}),
    'solar': (legacy.kernel_Solar, False, 'solar_geometry', {}),
    'rl_distance': (legacy.kernel_RLf, False, 'angular_distance', {}),
    'r': (None, False, 'hotspot', {'k': 1.}),
    'rl': (None, False, 'hotspot', {'k': 1.}),
}

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


def available_kernels() -> dict:
    """Return independent metadata dictionaries, safe for JSON configuration."""
    return {name: {'family': family, 'parameters': dict(defaults)}
            for name, (_, _, family, defaults) in _REGISTRY.items()}


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
            f = legacy.kernel_RLf(v, s, a)
            values = np.exp(-term.parameters['k'] * f)
            if term.name == 'rl':
                reference = np.exp(-term.parameters['k'] * np.tan(np.deg2rad(s)))
                values = (values-reference)/(1.0001-reference)
        else:
            args = (v,) if view_only else (v, s, a)
            values = function(*args, **term.parameters)
    out[mask] = np.where(np.isfinite(values), values, np.nan)
    return out.reshape(shape)


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


def kernel_model(preset: str) -> KernelModel:
    if preset not in PRESETS:
        raise ValueError(f'unknown kernel preset: {preset}; choices: {list(PRESETS)}')
    return KernelModel(PRESETS[preset])


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


def _replace_parameters(model, keys, values):
    changes = dict(zip(keys, values))
    return KernelModel(tuple(KernelTerm(t.name, {k: changes.get(f'{t.name}.{k}', v)
                                               for k, v in t.parameters.items()}) for t in model.terms))


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
