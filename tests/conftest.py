import pytest
from orbital_telemetry.core.tle import TLE
from orbital_telemetry.core.propagator import KeplerianPropagator
from orbital_telemetry.tracking.ground_station import GroundStation


@pytest.fixture
def iss_tle():
    return TLE.from_lines(
        "ISS (ZARYA)",
        "1 25544U 98067A   26034.50000000  .00016717  00000-0  10270-3 0  9001",
        "2 25544  51.6400 208.5000 0005000 130.0000 230.0000 15.50000000450001",
    )


@pytest.fixture
def propagator(iss_tle):
    return KeplerianPropagator(iss_tle)


@pytest.fixture
def hyderabad_station():
    return GroundStation(name="Hyderabad-GS", latitude_deg=17.3850, longitude_deg=78.4867, min_elevation_deg=5.0)
