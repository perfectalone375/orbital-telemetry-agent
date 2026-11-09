from orbital_telemetry.core.coordinates import GeodeticCoordinates


def test_footprint_radius():
    # At 420 km altitude (ISS), footprint radius is approximately 2200 - 2400 km
    geo = GeodeticCoordinates(latitude_deg=0.0, longitude_deg=0.0, altitude_km=420.0)
    radius = geo.footprint_radius_km()
    assert 2100.0 < radius < 2500.0
