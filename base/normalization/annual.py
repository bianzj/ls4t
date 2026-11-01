"""Annual temperature cycle (ATC): one or two harmonics, fitted by weighted LS.

T = mean + sum(c_j*cos(2*pi*j*phase) + s_j*sin(2*pi*j*phase)).
Phase zero is January 1; dates use their actual Gregorian year length.
Numeric DOY is ONE-based, with an explicit year_length (default 365).
This is a seasonal/climatological curve, not a weather-aware reconstruction.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from numbers import Real
import re
import numpy as np

from base.quality import usable
from ._fit import fit_linear
from ._validation import quality_flags


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


def _annual_design(phase, harmonics):
    columns = [np.ones_like(phase)]
    for j in range(1,harmonics+1):
        columns.extend((np.cos(2*np.pi*j*phase), np.sin(2*np.pi*j*phase)))
    return np.stack(columns, axis=-1)


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
