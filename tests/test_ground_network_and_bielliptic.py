"""
Tests for 3-impulse bi-elliptic orbital transfers and multi-station ground tracking network.
"""

import pytest

from orbital_telemetry.core.maneuvers import bielliptic_transfer
from orbital_telemetry.core.propagator import KeplerianPropagator
from orbital_telemetry.core.tle import TLE
from orbital_telemetry.mcp.server import (
    SAMPLE_ISS_TLE,
    handle_bielliptic,
    handle_network_coverage,
)
from orbital_telemetry.tracking.network import GroundStationNetwork


def test_bielliptic_transfer_high_ratio_efficiency():
    # Radius ratio r2 / r1 = 105000 / 6700 = 15.67 (> 11.94 critical ratio)
    # Intermediate apoapsis rb = 250000 km
    res = bielliptic_transfer(r1_km=6700.0, r2_km=105000.0, rb_km=250000.0)

    assert res.total_delta_v_km_s > 3.0
    assert res.total_duration_hours > 50.0
    assert res.is_more_efficient_than_hohmann is True


def test_bielliptic_transfer_moderate_ratio_hohmann_better():
    # LEO to GEO (r2 / r1 ~ 6.3 < 11.94): Hohmann is strictly more fuel-efficient
    res = bielliptic_transfer(r1_km=6700.0, r2_km=42164.0, rb_km=60000.0)

    assert res.is_more_efficient_than_hohmann is False
    assert res.delta_v1_km_s > 0.0
    assert res.delta_v2_km_s > 0.0
    assert res.delta_v3_km_s > 0.0


def test_bielliptic_invalid_radii_raises():
    with pytest.raises(ValueError, match="strictly positive"):
        bielliptic_transfer(r1_km=-100.0, r2_km=10000.0, rb_km=20000.0)

    with pytest.raises(ValueError, match="strictly greater than max"):
        bielliptic_transfer(r1_km=6700.0, r2_km=42164.0, rb_km=30000.0)


def test_ground_station_network_coverage():
    tle = TLE.from_lines(*SAMPLE_ISS_TLE)
    prop = KeplerianPropagator(tle)
    net = GroundStationNetwork()

    # Analyze 6 hours of orbital trajectory
    summary = net.analyze_coverage(prop, duration_hours=6.0, step_s=30.0)

    assert summary.total_passes >= 3
    assert len(summary.stations_contacted) >= 2
    assert summary.total_contact_minutes > 15.0
    assert summary.coverage_percentage_24h > 3.0


def test_mcp_bielliptic_and_network_tools():
    res_b = handle_bielliptic({"r1_km": 6700.0, "r2_km": 105000.0, "rb_km": 250000.0})
    assert res_b["is_more_efficient_than_hohmann"] is True
    assert res_b["total_delta_v_km_s"] > 3.0

    res_net = handle_network_coverage({"duration_hours": 4.0})
    assert res_net["total_passes"] > 0
    assert len(res_net["stations_contacted"]) > 0
