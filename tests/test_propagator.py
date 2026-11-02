import pytest

def test_kepler_solver(propagator):
    # For small e, M ~ E
    e_anom = propagator.solve_kepler(0.5)
    assert pytest.approx(e_anom, abs=1e-3) == 0.5

def test_propagation_dynamics(propagator):
    state_0 = propagator.propagate(0.0)
    state_1000 = propagator.propagate(1000.0)

    # Orbital velocity for LEO ~ 7.6 - 7.8 km/s
    assert 7.4 < state_0.orbital_speed_km_s < 7.9
    assert -90.0 <= state_0.geodetic.latitude_deg <= 90.0
    assert -180.0 <= state_0.geodetic.longitude_deg <= 180.0
    assert state_0.geodetic.altitude_km > 350.0
    assert state_1000.time_since_epoch_s == 1000.0
