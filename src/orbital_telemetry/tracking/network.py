"""
Multi-station ground station network, continuous contact tracking, and handover scheduling.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from orbital_telemetry.core.constants import OMEGA_EARTH_RAD_S
from orbital_telemetry.core.propagator import KeplerianPropagator
from orbital_telemetry.tracking.ground_station import GroundStation


@dataclass
class NetworkCoverageSummary:
    """Consolidated 24-hour telemetry contact and gap metrics across ground network."""

    total_passes: int
    stations_contacted: List[str]
    total_contact_minutes: float
    coverage_percentage_24h: float
    max_contact_gap_minutes: float
    station_breakdown: Dict[str, int]
    timeline: List[Dict[str, Any]] = field(default_factory=list)


def create_global_ground_network() -> List[GroundStation]:
    """Returns a realistic worldwide 6-station satellite tracking network."""
    return [
        GroundStation(
            name="Goldstone DSN",
            latitude_deg=35.426,
            longitude_deg=-116.89,
            altitude_m=1036.0,
            min_elevation_deg=5.0,
        ),
        GroundStation(
            name="Madrid DSN",
            latitude_deg=40.431,
            longitude_deg=-4.248,
            altitude_m=780.0,
            min_elevation_deg=5.0,
        ),
        GroundStation(
            name="Canberra DSN",
            latitude_deg=-35.401,
            longitude_deg=148.981,
            altitude_m=650.0,
            min_elevation_deg=5.0,
        ),
        GroundStation(
            name="Svalbard Polar",
            latitude_deg=78.229,
            longitude_deg=15.407,
            altitude_m=498.0,
            min_elevation_deg=5.0,
        ),
        GroundStation(
            name="Hyderabad Master",
            latitude_deg=17.385,
            longitude_deg=78.486,
            altitude_m=542.0,
            min_elevation_deg=5.0,
        ),
        GroundStation(
            name="Santiago Tracking",
            latitude_deg=-33.15,
            longitude_deg=-70.667,
            altitude_m=730.0,
            min_elevation_deg=5.0,
        ),
    ]


class GroundStationNetwork:
    """Orchestrates pass prediction and tracking handovers across multiple worldwide ground stations."""

    def __init__(self, stations: List[GroundStation] | None = None) -> None:
        self.stations = stations or create_global_ground_network()

    def analyze_coverage(
        self,
        propagator: KeplerianPropagator,
        duration_hours: float = 12.0,
        step_s: float = 30.0,
    ) -> NetworkCoverageSummary:
        """Scan trajectory timeline and calculate contact intervals across all network stations."""
        total_steps = int((duration_hours * 3600.0) / step_s)
        in_contact_steps = 0
        timeline: List[Dict[str, Any]] = []

        active_station: str | None = None
        pass_start_t = 0.0
        max_el = 0.0

        station_counts: Dict[str, int] = {s.name: 0 for s in self.stations}
        contacted_names: set[str] = set()

        last_contact_end_s = 0.0
        max_gap_s = 0.0

        for step in range(total_steps):
            t = step * step_s
            state = propagator.propagate(t)
            gmst = (OMEGA_EARTH_RAD_S * t) % 6.28318530718

            # Check visibility across stations, picking highest elevation station
            best_station: GroundStation | None = None
            best_elevation = -90.0

            for st in self.stations:
                topo = st.compute_topocentric(state.position_eci, gmst)
                if topo.is_visible and topo.elevation_deg > best_elevation:
                    best_elevation = topo.elevation_deg
                    best_station = st

            if best_station is not None:
                in_contact_steps += 1
                contacted_names.add(best_station.name)

                if active_station is None:
                    # New contact window begins
                    active_station = best_station.name
                    pass_start_t = t
                    max_el = best_elevation
                    gap = t - last_contact_end_s
                    if gap > max_gap_s:
                        max_gap_s = gap
                elif active_station == best_station.name:
                    if best_elevation > max_el:
                        max_el = best_elevation
                else:
                    # Handover to new station!
                    station_counts[active_station] += 1
                    timeline.append(
                        {
                            "station": active_station,
                            "aos_s": pass_start_t,
                            "los_s": t,
                            "duration_min": round((t - pass_start_t) / 60.0, 2),
                            "max_elevation_deg": round(max_el, 2),
                            "event": "HANDOVER",
                        }
                    )
                    active_station = best_station.name
                    pass_start_t = t
                    max_el = best_elevation
            else:
                if active_station is not None:
                    # Contact lost
                    station_counts[active_station] += 1
                    timeline.append(
                        {
                            "station": active_station,
                            "aos_s": pass_start_t,
                            "los_s": t,
                            "duration_min": round((t - pass_start_t) / 60.0, 2),
                            "max_elevation_deg": round(max_el, 2),
                            "event": "LOS",
                        }
                    )
                    last_contact_end_s = t
                    active_station = None

        total_contact_sec = in_contact_steps * step_s
        total_time_sec = duration_hours * 3600.0
        coverage_pct = (total_contact_sec / total_time_sec) * 100.0

        return NetworkCoverageSummary(
            total_passes=len(timeline),
            stations_contacted=sorted(list(contacted_names)),
            total_contact_minutes=round(total_contact_sec / 60.0, 2),
            coverage_percentage_24h=round(coverage_pct, 2),
            max_contact_gap_minutes=round(max_gap_s / 60.0, 2),
            station_breakdown=station_counts,
            timeline=timeline,
        )
