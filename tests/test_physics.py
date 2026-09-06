import numpy as np

from base.radiometry import decode_temperature, inverse_planck, planck_radiance


def test_planck_round_trip():
    temperature = np.array([250.0, 300.0, 330.0])
    recovered = inverse_planck(10.8, planck_radiance(10.8, temperature))
    np.testing.assert_allclose(recovered, temperature, rtol=1e-12)


def test_temperature_decoding_is_explicit():
    raw = np.array([30000, 65535], dtype=np.uint16)
    decoded = decode_temperature(raw, scale=0.01, fill_value=65535)
    assert decoded[0] == 300.0
    assert np.isnan(decoded[1])
