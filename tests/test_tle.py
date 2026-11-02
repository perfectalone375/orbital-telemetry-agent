import pytest

def test_tle_parsing(iss_tle):
    assert iss_tle.name == "ISS (ZARYA)"
    assert iss_tle.norad_id == 25544
    assert pytest.approx(iss_tle.inclination_deg, abs=1e-2) == 51.64
    assert pytest.approx(iss_tle.eccentricity, abs=1e-4) == 0.0005
    assert pytest.approx(iss_tle.orbital_period_minutes, abs=1e-1) == 92.9
    assert iss_tle.perigee_altitude_km > 350.0
    assert iss_tle.apogee_altitude_km < 450.0
