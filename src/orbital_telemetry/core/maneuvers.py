"""
Astrodynamics orbital maneuvers, transfer trajectory calculations, and delta-v budgets.
Includes two-impulse coplanar Hohmann transfer, plane change maneuvers, and bi-elliptic transfers.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Any

from orbital_telemetry.core.constants import MU_EARTH_KM3_S2


@dataclass
class HohmannResult:
    """Analytical parameters of a Hohmann orbital transfer."""
    r1_km: float
    r2_km: float
    semi_major_axis_km: float
    v_c1_km_s: float
    v_c2_km_s: float
    delta_v1_km_s: float
    delta_v2_km_s: float
    total_delta_v_km_s: float
    transfer_duration_s: float
    transfer_duration_hours: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "r1_km": self.r1_km,
            "r2_km": self.r2_km,
            "semi_major_axis_km": round(self.semi_major_axis_km, 3),
            "v_initial_circular_km_s": round(self.v_c1_km_s, 4),
            "v_target_circular_km_s": round(self.v_c2_km_s, 4),
            "delta_v1_km_s": round(self.delta_v1_km_s, 4),
            "delta_v2_km_s": round(self.delta_v2_km_s, 4),
            "total_delta_v_km_s": round(self.total_delta_v_km_s, 4),
            "transfer_duration_s": round(self.transfer_duration_s, 2),
            "transfer_duration_hours": round(self.transfer_duration_hours, 3),
        }


def hohmann_transfer(
    r1_km: float,
    r2_km: float,
    mu_km3_s2: float = MU_EARTH_KM3_S2,
) -> HohmannResult:
    """
    Calculate minimum two-impulse Hohmann transfer between two coplanar circular orbits.

    Parameters
    ----------
    r1_km : float
        Radius of the initial circular orbit (km) > 0.
    r2_km : float
        Radius of the target circular orbit (km) > 0.
    mu_km3_s2 : float
        Gravitational parameter (km^3/s^2), default Earth GM.

    Returns
    -------
    HohmannResult
        Comprehensive impulse, velocity, and time-of-flight budget.
    """
    if r1_km <= 0 or r2_km <= 0:
        raise ValueError("Orbit radii r1 and r2 must be strictly positive.")

    # Circular velocities
    v_c1 = math.sqrt(mu_km3_s2 / r1_km)
    v_c2 = math.sqrt(mu_km3_s2 / r2_km)

    # Semi-major axis of transfer ellipse
    a_trans = (r1_km + r2_km) / 2.0

    # Transfer velocities at periapsis and apoapsis
    v_trans_p = math.sqrt(mu_km3_s2 * (2.0 / r1_km - 1.0 / a_trans))
    v_trans_a = math.sqrt(mu_km3_s2 * (2.0 / r2_km - 1.0 / a_trans))

    # Delta-V burns
    dv1 = abs(v_trans_p - v_c1)
    dv2 = abs(v_c2 - v_trans_a)
    total_dv = dv1 + dv2

    # Half-period of transfer orbit (time of flight)
    t_tof = math.pi * math.sqrt((a_trans**3) / mu_km3_s2)

    return HohmannResult(
        r1_km=r1_km,
        r2_km=r2_km,
        semi_major_axis_km=a_trans,
        v_c1_km_s=v_c1,
        v_c2_km_s=v_c2,
        delta_v1_km_s=dv1,
        delta_v2_km_s=dv2,
        total_delta_v_km_s=total_dv,
        transfer_duration_s=t_tof,
        transfer_duration_hours=t_tof / 3600.0,
    )


def plane_change_delta_v(velocity_km_s: float, inclination_change_deg: float) -> float:
    """
    Calculate impulse delta-v for a simple orbital inclination change:
    Delta-V = 2 * V * sin(Delta-i / 2).
    """
    if velocity_km_s <= 0:
        raise ValueError("Velocity must be strictly positive.")
    di_rad = math.radians(abs(inclination_change_deg))
    return 2.0 * velocity_km_s * math.sin(di_rad / 2.0)


def combined_hohmann_plane_change(
    r1_km: float,
    r2_km: float,
    inclination_change_deg: float,
    mu_km3_s2: float = MU_EARTH_KM3_S2,
) -> Dict[str, Any]:
    """
    Combined Hohmann transfer and plane change at apoapsis where orbital velocity is lowest.
    Delta-V2 = sqrt(v_c2^2 + v_trans_a^2 - 2 * v_c2 * v_trans_a * cos(Delta-i)).
    """
    hohmann = hohmann_transfer(r1_km, r2_km, mu_km3_s2)
    v_c2 = hohmann.v_c2_km_s
    a_trans = hohmann.semi_major_axis_km
    v_trans_a = math.sqrt(mu_km3_s2 * (2.0 / r2_km - 1.0 / a_trans))

    di_rad = math.radians(abs(inclination_change_deg))
    # Combined burn at apoapsis via law of cosines
    combined_dv2 = math.sqrt(v_c2**2 + v_trans_a**2 - 2.0 * v_c2 * v_trans_a * math.cos(di_rad))
    total_dv = hohmann.delta_v1_km_s + combined_dv2

    return {
        "r1_km": r1_km,
        "r2_km": r2_km,
        "inclination_change_deg": inclination_change_deg,
        "delta_v1_km_s": round(hohmann.delta_v1_km_s, 4),
        "combined_delta_v2_km_s": round(combined_dv2, 4),
        "total_delta_v_km_s": round(total_dv, 4),
        "transfer_duration_hours": round(hohmann.transfer_duration_hours, 3),
    }

