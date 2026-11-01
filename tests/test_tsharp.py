"""TsHARP scale order, vegetation transform, closure and QA contracts."""
import numpy as np
import pytest

from base.normalization import downscale as ds
from base.quality import QualityFlag


def scene():
    means = np.array([[.18,.28,.38],[.48,.58,.68]])
    spread = np.array([[.12,.08,.16],[.04,.10,.20]])
    expand = lambda x: np.repeat(np.repeat(x,2,0),2,1)
    ndvi = expand(means)+expand(spread)*np.tile([[-1.,-.25],[.25,1.]],(2,3))
    coarse = 310-20*(1-(1-means)**.625)
    return coarse,ndvi


def block_mean(values, weights=None):
    weights = np.ones_like(values) if weights is None else weights
    return ((values*weights).reshape(2,2,3,2).sum((1,3))
            /weights.reshape(2,2,3,2).sum((1,3)))


def test_standard_tsharp_cover_fraction_and_invalid_ndvi():
    assert hasattr(ds,'tsharp_cover_fraction'), 'TsHARP vegetation transform is missing'
    ndvi = np.array([0,.25,.8,1,-.2,1.1,np.nan])
    result = ds.tsharp_cover_fraction(ndvi)
    np.testing.assert_allclose(result[:4],1-(1-ndvi[:4])**.625)
    assert np.isnan(result[4:]).all()


def test_tsharp_aggregates_ndvi_before_transform_then_closes_fine_predictions():
    coarse,ndvi = scene()
    original = ndvi.copy()
    result = ds.downscale_temperature(coarse,ndvi,method='tsharp')
    np.testing.assert_allclose(result.coefficients,[310.,-20.],atol=1e-10)
    assert result.method == 'tsharp'
    # Nonlinear transformation and aggregation do not commute.
    fine_prediction = 310-20*(1-(1-ndvi)**.625)
    correction = coarse-block_mean(fine_prediction)
    assert np.max(np.abs(correction)) > .05
    expected = fine_prediction+np.repeat(np.repeat(correction,2,0),2,1)
    np.testing.assert_allclose(result.temperature_k,expected,atol=1e-10)
    np.testing.assert_allclose(result.coarse_residual_k,correction,atol=1e-10)
    np.testing.assert_allclose(block_mean(result.temperature_k),coarse,atol=1e-10)
    np.testing.assert_array_equal(ndvi,original)
    assert result.training_count == 6 and result.training_rmse_k < 1e-10


def test_tsharp_weighted_closure_and_array_convenience_api():
    assert hasattr(ds,'downscale_tsharp'), 'public TsHARP entry is missing'
    coarse,ndvi = scene()
    coarse[0,0] += 2
    weights = np.tile([[1.,2.],[3.,4.]],(2,3))
    result = ds.downscale_tsharp(coarse,ndvi,fine_weights=weights)
    np.testing.assert_allclose(block_mean(result.temperature_k,weights),coarse,atol=1e-10)
    assert result.training_rmse_k > .1


def test_tsharp_invalid_ndvi_and_clouds_are_not_filled():
    coarse,ndvi = scene()
    flags = np.zeros(coarse.shape,dtype='uint16'); flags[0,0] = QualityFlag.CLOUD
    ndvi[-1,-1] = -.1
    result = ds.downscale_temperature(coarse,ndvi,method='tsharp',coarse_quality_flag=flags)
    assert np.isnan(result.temperature_k[:2,:2]).all()
    assert np.isnan(result.temperature_k[-2:,-2:]).all()
    assert result.coarse_coverage[-1,-1] == .75
    assert result.quality_flag[-1,-1] & QualityFlag.INPUT_INVALID
    assert (result.quality_flag[-2:,-2:] & QualityFlag.LOW_SUPPORT).all()
    partial = ds.downscale_temperature(coarse,ndvi,method='tsharp',minimum_coverage=.75)
    assert np.isnan(partial.temperature_k[-1,-1])
    assert np.nanmean(partial.temperature_k[-2:,-2:]) == pytest.approx(coarse[-1,-1])


@pytest.mark.parametrize('kind',['method','features','constant'])
def test_tsharp_rejects_unsupported_or_unidentifiable_inputs(kind):
    coarse,ndvi = scene()
    method = 'tsharp'
    if kind == 'method':
        method = 'tshapp'  # no silently accepted typo in machine configuration
    elif kind == 'features':
        ndvi = np.stack([ndvi,ndvi*10],axis=-1)
    else:
        ndvi[:] = .5
    with pytest.raises(ValueError):
        ds.downscale_temperature(coarse,ndvi,method=method)


def test_linear_downscaling_remains_default():
    coarse,ndvi = scene()
    implicit = ds.downscale_temperature(coarse,ndvi)
    explicit = ds.downscale_temperature(coarse,ndvi,method='linear')
    np.testing.assert_array_equal(implicit.temperature_k,explicit.temperature_k)
    assert implicit.method == 'linear'
