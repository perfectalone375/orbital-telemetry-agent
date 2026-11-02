"""
Ground station antenna coordinates and Topocentric (Azimuth, Elevation, Range) calculation.
"""

import math
from dataclasses import dataclass
from orbital_telemetry.core.coordinates import GeodeticCoordinates, ECICoordinates


@dataclass
class TopocentricCoordinates:
    """Observer-centric relative tracking coordinates."""
    azimuth_deg: float
    elevation_deg: float
    slant_range_km: float
    is_visible: bool  # Elevation > minimum mask


@dataclass
class GroundStation:
    """Tracking earth station model."""
    name: str
    latitude_deg: float
    longitude_deg: float
    altitude_m: float = 0.0
    min_elevation_deg: float = 5.0  # Antenna horizon mask

    @property
    def geodetic(self) -> GeodeticCoordinates:
        return GeodeticCoordinates(
            latitude_deg=self.latitude_deg,
            longitude_deg=self.longitude_deg,
            altitude_km=self.altitude_m / 1000.0
        )

    def compute_topocentric(self, sat_eci: ECICoordinates, gmst_rad: float) -> TopocentricCoordinates:
        """Compute Azimuth, Elevation, and Range to satellite."""
        gs_ecef = self.geodetic.to_ecef()
        sat_ecef = sat_eci.to_ecef(gmst_rad)

        # Relative vector in ECEF (dx, dy, dz)
        dx = sat_ecef.x_km - gs_ecef.x_km
        dy = sat_ecef.y_km - gs_ecef.y_km
        dz = sat_ecef.z_km - gs_ecef.z_km

        range_km = math.sqrt(dx ** 2 + dy ** 2 + dz ** 2)

        # Transform to Topocentric South-East-Zenith (SEZ) frame
        lat_rad = self.geodetic.latitude_rad
        lon_rad = self.geodetic.longitude_rad

        sin_lat = math.sin(lat_rad)
        cos_lat = math.cos(lat_rad)
        sin_lon = math.sin(lon_rad)
        cos_lon = math.cos(lon_rad)

        # SEZ components
        s = sin_lat * cos_lon * dx + sin_lat * sin_lon * dy - cos_lat * dz
        e = -sin_lon * dx + cos_lon * dy
        z = cos_lat * cos_lon * dx + cos_lat * sin_lon * dy + sin_lat * dz

        # Elevation = asin(z / range)
        el_rad = math.asin(max(-1.0, min(1.0, z / range_km)))
        el_deg = math.degrees(el_rad)

        # Azimuth = atan2(E, -S) from True North
        az_rad = math.atan2(e, -s)
        az_deg = (math.degrees(az_rad) + 360.0) % 360.0

        is_vis = el_deg >= self.min_elevation_deg

        return TopocentricCoordinates(
            azimuth_deg=round(az_deg, 2),
            elevation_deg=round(el_deg, 2),
            slant_range_km=round(range_km, 2),
            is_visible=is_vis
        )
