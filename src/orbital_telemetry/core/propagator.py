"""
Keplerian orbit propagator with J2 secular oblateness perturbation correction.
"""

import math
from dataclasses import dataclass
from orbital_telemetry.core.constants import (
    MU_EARTH_KM3_S2,
    R_EARTH_EQUATORIAL_KM,
    J2_EARTH,
    OMEGA_EARTH_RAD_S,
)
from orbital_telemetry.core.tle import TLE
from orbital_telemetry.core.coordinates import ECICoordinates, GeodeticCoordinates


@dataclass
class OrbitState:
    """Instantaneous dynamic orbit state."""

    time_since_epoch_s: float
    position_eci: ECICoordinates
    velocity_eci_km_s: tuple
    geodetic: GeodeticCoordinates
    orbital_speed_km_s: float
    true_anomaly_deg: float


class KeplerianPropagator:
    """
    Propagates satellite state vectors through time with J2 oblateness regression.
    """

    def __init__(self, tle: TLE) -> None:
        self.tle = tle
        self.a = tle.semi_major_axis_km
        self.e = tle.eccentricity
        self.inc = tle.inclination_rad
        self.n0 = tle.mean_motion_rad_s

        # J2 secular perturbations
        # Nodal regression rate (dRAAN/dt)
        p = self.a * (1.0 - self.e**2)
        factor = -1.5 * J2_EARTH * (R_EARTH_EQUATORIAL_KM / p) ** 2 * self.n0
        self.raan_dot = factor * math.cos(self.inc)

        # Perigee precession rate (domega/dt)
        self.omega_dot = factor * (2.0 - 2.5 * (math.sin(self.inc) ** 2))

    def solve_kepler(self, mean_anomaly_rad: float, tolerance: float = 1e-8) -> float:
        """Newton-Raphson solver for Kepler's Equation: M = E - e*sin(E)."""
        m = mean_anomaly_rad % (2.0 * math.pi)
        e_anomaly = m if self.e < 0.8 else math.pi

        for _ in range(50):
            f = e_anomaly - self.e * math.sin(e_anomaly) - m
            f_prime = 1.0 - self.e * math.cos(e_anomaly)
            delta = f / f_prime
            e_anomaly -= delta
            if abs(delta) < tolerance:
                break

        return e_anomaly

    def propagate(self, dt_seconds: float) -> OrbitState:
        """Propagate orbit dt_seconds forward from TLE epoch."""
        # Mean anomaly advancement
        m_t = self.tle.mean_anomaly_rad + self.n0 * dt_seconds

        # Solve for Eccentric Anomaly E
        e_anom = self.solve_kepler(m_t)

        # True anomaly nu
        sin_nu = (math.sqrt(1.0 - self.e**2) * math.sin(e_anom)) / (1.0 - self.e * math.cos(e_anom))
        cos_nu = (math.cos(e_anom) - self.e) / (1.0 - self.e * math.cos(e_anom))
        nu = math.atan2(sin_nu, cos_nu)

        # Radius r
        r = self.a * (1.0 - self.e * math.cos(e_anom))

        # Secular perturbation on RAAN and argument of perigee
        raan = self.tle.raan_rad + self.raan_dot * dt_seconds
        arg_p = self.tle.arg_perigee_rad + self.omega_dot * dt_seconds
        u = arg_p + nu  # Argument of latitude

        # ECI Position
        x_orb = r * math.cos(u)
        y_orb = r * math.sin(u)

        x_eci = x_orb * math.cos(raan) - y_orb * math.cos(self.inc) * math.sin(raan)
        y_eci = x_orb * math.sin(raan) + y_orb * math.cos(self.inc) * math.cos(raan)
        z_eci = y_orb * math.sin(self.inc)

        # Orbital speed via vis-viva equation: v^2 = mu * (2/r - 1/a)
        v_mag = math.sqrt(MU_EARTH_KM3_S2 * (2.0 / r - 1.0 / self.a))

        # Velocity components in orbital plane
        p = self.a * (1.0 - self.e**2)
        h = math.sqrt(MU_EARTH_KM3_S2 * p)  # Specific angular momentum
        vr = (MU_EARTH_KM3_S2 / h) * self.e * math.sin(nu)
        vt = (MU_EARTH_KM3_S2 / h) * (1.0 + self.e * math.cos(nu))

        vx_orb = vr * math.cos(u) - vt * math.sin(u)
        vy_orb = vr * math.sin(u) + vt * math.cos(u)

        vx_eci = vx_orb * math.cos(raan) - vy_orb * math.cos(self.inc) * math.sin(raan)
        vy_eci = vx_orb * math.sin(raan) + vy_orb * math.cos(self.inc) * math.cos(raan)
        vz_eci = vy_orb * math.sin(self.inc)

        eci_pos = ECICoordinates(x_km=x_eci, y_km=y_eci, z_km=z_eci)

        # Earth rotation (GMST approximation relative to epoch)
        gmst = (OMEGA_EARTH_RAD_S * dt_seconds) % (2.0 * math.pi)
        ecef_pos = eci_pos.to_ecef(gmst)
        geodetic = ecef_pos.to_geodetic()

        return OrbitState(
            time_since_epoch_s=dt_seconds,
            position_eci=eci_pos,
            velocity_eci_km_s=(vx_eci, vy_eci, vz_eci),
            geodetic=geodetic,
            orbital_speed_km_s=v_mag,
            true_anomaly_deg=math.degrees(nu) % 360.0,
        )
