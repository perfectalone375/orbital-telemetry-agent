"""
Autonomous ground station pass prediction and AOS/LOS scheduler.
"""

from dataclasses import dataclass
from typing import List
from orbital_telemetry.core.propagator import KeplerianPropagator
from orbital_telemetry.core.constants import OMEGA_EARTH_RAD_S
from orbital_telemetry.tracking.ground_station import GroundStation


@dataclass
class SatellitePass:
    """A single ground station visible satellite pass."""
    aos_time_s: float
    los_time_s: float
    duration_seconds: float
    max_elevation_deg: float
    max_elevation_time_s: float
    aos_azimuth_deg: float
    los_azimuth_deg: float


class PassPredictor:
    """
    Scans orbital timeline to detect Acquisition of Signal (AOS) and Loss of Signal (LOS).
    """

    def __init__(self, propagator: KeplerianPropagator, station: GroundStation) -> None:
        self.propagator = propagator
        self.station = station

    def predict_passes(self, start_time_s: float = 0.0, duration_hours: float = 24.0, step_s: float = 30.0) -> List[SatellitePass]:
        passes = []
        in_pass = False

        aos_t = 0.0
        aos_az = 0.0
        max_el = 0.0
        max_el_t = 0.0

        total_steps = int((duration_hours * 3600.0) / step_s)

        for step in range(total_steps):
            t = start_time_s + step * step_s
            state = self.propagator.propagate(t)
            gmst = (OMEGA_EARTH_RAD_S * t) % (6.28318530718)
            topo = self.station.compute_topocentric(state.position_eci, gmst)

            if topo.is_visible:
                if not in_pass:
                    in_pass = True
                    aos_t = t
                    aos_az = topo.azimuth_deg
                    max_el = topo.elevation_deg
                    max_el_t = t
                else:
                    if topo.elevation_deg > max_el:
                        max_el = topo.elevation_deg
                        max_el_t = t
            else:
                if in_pass:
                    in_pass = False
                    los_t = t
                    los_az = topo.azimuth_deg
                    passes.append(
                        SatellitePass(
                            aos_time_s=aos_t,
                            los_time_s=los_t,
                            duration_seconds=round(los_t - aos_t, 1),
                            max_elevation_deg=round(max_el, 2),
                            max_elevation_time_s=max_el_t,
                            aos_azimuth_deg=aos_az,
                            los_azimuth_deg=los_az
                        )
                    )

        return passes
