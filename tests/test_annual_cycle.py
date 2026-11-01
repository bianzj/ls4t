import numpy as np
import pytest

from base.normalization import annual as atc


def test_atc_recovers_single_cycle_and_normalizes_preserving_anomalies():
    doy = np.arange(1., 366., 9.)
    y = 291 + 13*np.cos(2*np.pi*(doy-201)/365)
    fit = atc.fit_annual_cycle(y, doy)
    assert fit.mean_k == pytest.approx(291.)
    assert fit.amplitudes_k[0] == pytest.approx(13.)
    assert fit.peak_days()[0] == pytest.approx(201.)
    holdout = np.arange(4.,366.,9.)
    np.testing.assert_allclose(fit.predict(holdout), 291+13*np.cos(2*np.pi*(holdout-201)/365))
    np.testing.assert_allclose(fit.normalize(y+1.5, doy, reference=201.), 305.5)
    assert np.isnan(fit.normalize(np.nan, 30., reference=201.))


def test_double_harmonic_recovery_and_missing_qa():
    doy = np.arange(1., 366., 5.)
    phase = (doy-1)/365
    y = 290+9*np.cos(2*np.pi*phase)+3*np.sin(2*np.pi*phase)+2*np.cos(4*np.pi*phase)-np.sin(4*np.pi*phase)
    y[0] = np.nan; y[1] = 350
    qa = np.zeros(len(y)); qa[1] = 2; qa[2] = np.nan
    fit = atc.fit_annual_cycle(y, doy, harmonics=2, quality_flag=qa)
    np.testing.assert_allclose(fit.coefficients, [290,9,3,2,-1], atol=1e-10)
    assert fit.sample_count == len(y)-3
    assert fit.harmonics == 2


def test_calendar_dates_and_explicit_leap_year_agree():
    dates = np.array(['2024-01-01','2024-02-29','2024-12-31','2023-12-31'],dtype='datetime64[D]')
    phase = atc.annual_phase(dates)
    np.testing.assert_allclose(phase, [0,59/366,365/366,364/365])
    np.testing.assert_allclose(atc.annual_phase([1,60,366],year_length=366),phase[:3])
    assert np.isnan(atc.annual_phase(np.datetime64('NaT')))
    assert np.isnan(atc.annual_phase(366,year_length=365))
    assert np.isnan(atc.annual_phase(0))


def test_atc_does_not_accept_short_season_or_underdetermined_samples():
    with pytest.raises(ValueError, match='coverage'):
        atc.fit_annual_cycle(np.full(30,300.),np.arange(1,31))
    with pytest.raises(ValueError, match='samples'):
        atc.fit_annual_cycle([290,300,290],[1,120,240])
    with pytest.raises(ValueError, match='harmonics'):
        atc.fit_annual_cycle(np.full(12,300.),np.arange(1,361,30),harmonics=3)


def test_multiyear_dates_fit_shared_seasonal_climatology():
    dates = np.arange('2023-01-01','2025-01-01',dtype='datetime64[D]')[::10]
    phase = atc.annual_phase(dates)
    y = 295 + 10*np.cos(2*np.pi*phase-.8)
    fit = atc.fit_annual_cycle(y,dates)
    np.testing.assert_allclose(fit.predict(dates),y,atol=1e-10)
    assert fit.peak_days(366)[0] == pytest.approx(1+.8/(2*np.pi)*366)


def test_object_numeric_days_are_not_interpreted_as_epoch_microseconds():
    values = np.array([1,180.,365,None,np.nan],dtype=object)
    np.testing.assert_allclose(atc.annual_phase(values),[0,179/365,364/365,np.nan,np.nan])
    with pytest.raises(ValueError,match='mix'):
        atc.annual_phase(np.array(['2024-01-01',180],dtype=object))


def test_datetime_objects_and_timezone_policy():
    from datetime import date, datetime, timezone
    np.testing.assert_allclose(atc.annual_phase([date(2024,1,1),datetime(2024,2,29)]),[0,59/366])
    with pytest.raises(ValueError,match='timezone'):
        atc.annual_phase([datetime(2024,1,1,tzinfo=timezone.utc)])
    with pytest.raises(ValueError,match='timezone'):
        atc.annual_phase(['2024-01-01T00:00:00+08:00'])
    for offset in ('+08','-05'):
        with pytest.raises(ValueError,match='timezone'):
            atc.annual_phase(['2024-01-01T00:00:00'+offset])

