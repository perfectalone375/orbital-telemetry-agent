from orbital_telemetry.tracking.pass_predictor import PassPredictor
from orbital_telemetry.tracking.doppler import DopplerCalculator


def test_ground_station_topocentric(propagator, hyderabad_station):
    state = propagator.propagate(0.0)
    topo = hyderabad_station.compute_topocentric(state.position_eci, 0.0)
    assert 0.0 <= topo.azimuth_deg <= 360.0
    assert -90.0 <= topo.elevation_deg <= 90.0
    assert topo.slant_range_km > 0.0


def test_pass_predictor(propagator, hyderabad_station):
    predictor = PassPredictor(propagator, hyderabad_station)
    passes = predictor.predict_passes(duration_hours=24.0, step_s=60.0)
    # Over 24 hours in LEO, ISS passes within visibility cone multiple times
    assert len(passes) >= 1
    assert passes[0].max_elevation_deg >= 5.0
    assert passes[0].duration_seconds > 0.0


def test_doppler_calculation(propagator, hyderabad_station):
    state = propagator.propagate(500.0)
    station_pos = hyderabad_station.geodetic.to_ecef()
    res = DopplerCalculator.calculate_doppler(state.position_eci, state.velocity_eci_km_s, 437.5e6, station_pos)
    assert "doppler_shift_hz" in res
    assert "received_frequency_hz" in res
