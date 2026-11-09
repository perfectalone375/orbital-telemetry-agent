"""
orbital-telemetry-agent: Autonomous Satellite Orbit Propagator & MCP Tracking Engine.
"""

from orbital_telemetry.core.tle import TLE
from orbital_telemetry.core.coordinates import GeodeticCoordinates, ECICoordinates
from orbital_telemetry.core.propagator import KeplerianPropagator, OrbitState
from orbital_telemetry.core.maneuvers import (
    HohmannResult,
    BiEllipticResult,
    hohmann_transfer,
    bielliptic_transfer,
    plane_change_delta_v,
    combined_hohmann_plane_change,
)
from orbital_telemetry.tracking.ground_station import GroundStation
from orbital_telemetry.tracking.doppler import DopplerCalculator
from orbital_telemetry.tracking.pass_predictor import PassPredictor, SatellitePass
from orbital_telemetry.tracking.network import (
    GroundStationNetwork,
    NetworkCoverageSummary,
    create_global_ground_network,
)

__version__ = "0.1.0"
__author__ = "Gopi Naga Vignesh Thirupati"
__license__ = "MIT"

__all__ = [
    "TLE",
    "GeodeticCoordinates",
    "ECICoordinates",
    "KeplerianPropagator",
    "OrbitState",
    "GroundStation",
    "DopplerCalculator",
    "PassPredictor",
    "SatellitePass",
    "HohmannResult",
    "BiEllipticResult",
    "hohmann_transfer",
    "bielliptic_transfer",
    "plane_change_delta_v",
    "combined_hohmann_plane_change",
    "GroundStationNetwork",
    "NetworkCoverageSummary",
    "create_global_ground_network",
]
