"""
Coordinate transformations: ECI (Inertial), ECEF (Terrestrial), and WGS-84 Geodetic.
"""

import math
from dataclasses import dataclass
from orbital_telemetry.core.constants import (
    R_EARTH_EQUATORIAL_KM,
    WGS84_FLATTENING,
    WGS84_E2,
)


@dataclass
class ECICoordinates:
    """Earth-Centered Inertial (J2000 / TEME) position in kilometers."""
    x_km: float
    y_km: float
    z_km: float

    @property
    def radius_km(self) -> float:
        return math.sqrt(self.x_km ** 2 + self.y_km ** 2 + self.z_km ** 2)

    def to_ecef(self, gmst_rad: float) -> "ECEFCoordinates":
        """Rotate ECI to ECEF by Greenwich Mean Sidereal Time (GMST)."""
        cos_theta = math.cos(gmst_rad)
        sin_theta = math.sin(gmst_rad)

        x_ecef = cos_theta * self.x_km + sin_theta * self.y_km
        y_ecef = -sin_theta * self.x_km + cos_theta * self.y_km
        z_ecef = self.z_km
        return ECEFCoordinates(x_km=x_ecef, y_km=y_ecef, z_km=z_ecef)


@dataclass
class ECEFCoordinates:
    """Earth-Centered Earth-Fixed position in kilometers."""
    x_km: float
    y_km: float
    z_km: float

    def to_geodetic(self) -> "GeodeticCoordinates":
        """Bowring's closed-form algorithm for WGS-84 Geodetic Coordinates."""
        a = R_EARTH_EQUATORIAL_KM
        b = a * (1.0 - WGS84_FLATTENING)
        e2 = WGS84_E2
        e_prime2 = (a ** 2 - b ** 2) / (b ** 2)

        p = math.sqrt(self.x_km ** 2 + self.y_km ** 2)
        theta = math.atan2(self.z_km * a, p * b)

        sin_t = math.sin(theta)
        cos_t = math.cos(theta)

        lat = math.atan2(
            self.z_km + e_prime2 * b * (sin_t ** 3),
            p - e2 * a * (cos_t ** 3)
        )
        lon = math.atan2(self.y_km, self.x_km)

        sin_lat = math.sin(lat)
        n = a / math.sqrt(1.0 - e2 * (sin_lat ** 2))
        alt = (p / math.cos(lat)) - n

        return GeodeticCoordinates(
            latitude_deg=math.degrees(lat),
            longitude_deg=math.degrees(lon),
            altitude_km=alt
        )


@dataclass
class GeodeticCoordinates:
    """WGS-84 Sub-satellite point geodetic coordinates."""
    latitude_deg: float
    longitude_deg: float
    altitude_km: float

    @property
    def latitude_rad(self) -> float:
        return math.radians(self.latitude_deg)

    @property
    def longitude_rad(self) -> float:
        return math.radians(self.longitude_deg)

    def to_ecef(self) -> ECEFCoordinates:
        a = R_EARTH_EQUATORIAL_KM
        e2 = WGS84_E2
        lat_rad = self.latitude_rad
        lon_rad = self.longitude_rad

        sin_lat = math.sin(lat_rad)
        cos_lat = math.cos(lat_rad)
        n = a / math.sqrt(1.0 - e2 * (sin_lat ** 2))

        x = (n + self.altitude_km) * cos_lat * math.cos(lon_rad)
        y = (n + self.altitude_km) * cos_lat * math.sin(lon_rad)
        z = (n * (1.0 - e2) + self.altitude_km) * sin_lat

        return ECEFCoordinates(x_km=x, y_km=y, z_km=z)

    def footprint_radius_km(self) -> float:
        r_earth = R_EARTH_EQUATORIAL_KM
        if self.altitude_km <= 0:
            return 0.0
        theta = math.acos(r_earth / (r_earth + self.altitude_km))
        return r_earth * theta
