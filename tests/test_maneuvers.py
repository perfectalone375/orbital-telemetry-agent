"""
Tests for orbital transfer maneuvers and delta-v budgets.
"""

import pytest
import math
from orbital_telemetry.core.maneuvers import (
    hohmann_transfer,
    plane_change_delta_v,
    combined_hohmann_plane_change,
)


def test_leo_to_geo_hohmann_transfer():
    r1 = 6700.0  # LEO
    r2 = 42164.0  # GEO

    res = hohmann_transfer(r1, r2)

    # Check semi-major axis
    assert res.semi_major_axis_km == pytest.approx(24432.0, rel=1e-4)

    # Circular velocities
    assert res.v_c1_km_s == pytest.approx(7.713, rel=1e-2)
    assert res.v_c2_km_s == pytest.approx(3.075, rel=1e-2)

    # Delta-v burns
    assert res.delta_v1_km_s == pytest.approx(2.416, rel=1e-2)
    assert res.delta_v2_km_s == pytest.approx(1.465, rel=1e-2)
    assert res.total_delta_v_km_s == pytest.approx(3.88, rel=1e-2)

    # Time of flight approx 5.27 hours
    assert res.transfer_duration_hours == pytest.approx(5.27, rel=1e-2)


def test_hohmann_symmetry_circular():
    # If r1 == r2, transfer delta-v is 0
    res = hohmann_transfer(7000.0, 7000.0)
    assert res.delta_v1_km_s == pytest.approx(0.0, abs=1e-6)
    assert res.delta_v2_km_s == pytest.approx(0.0, abs=1e-6)
    assert res.total_delta_v_km_s == pytest.approx(0.0, abs=1e-6)


def test_plane_change_delta_v():
    v = 3.075  # GEO speed
    di = 28.5  # Cape Canaveral inclination
    dv = plane_change_delta_v(v, di)
    expected = 2.0 * v * math.sin(math.radians(di / 2.0))
    assert dv == pytest.approx(expected, rel=1e-5)


def test_combined_hohmann_plane_change():
    res = combined_hohmann_plane_change(6700.0, 42164.0, 28.5)
    # Combined burn at apoapsis should be less than separate Hohmann dv2 + plane change
    hohmann = hohmann_transfer(6700.0, 42164.0)
    separate_dv2 = hohmann.delta_v2_km_s + plane_change_delta_v(hohmann.v_c2_km_s, 28.5)
    assert res["combined_delta_v2_km_s"] < separate_dv2
    assert res["total_delta_v_km_s"] < (hohmann.total_delta_v_km_s + plane_change_delta_v(hohmann.v_c2_km_s, 28.5))


def test_invalid_radii():
    with pytest.raises(ValueError, match="strictly positive"):
        hohmann_transfer(-100.0, 42000.0)
