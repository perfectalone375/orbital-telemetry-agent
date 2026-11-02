"""
Astrodynamic and planetary constants for Earth orbit propagation.
Reference: WGS-84 & IAU standards.
"""

# Earth standard gravitational parameter mu = G * M (km^3 / s^2)
MU_EARTH_KM3_S2: float = 398600.4418

# WGS-84 Earth equatorial radius (km)
R_EARTH_EQUATORIAL_KM: float = 6378.137

# WGS-84 Earth polar semi-minor axis (km)
R_EARTH_POLAR_KM: float = 6356.7523142

# WGS-84 Earth flattening factor f = (a - b) / a
WGS84_FLATTENING: float = 1.0 / 298.257223563

# First eccentricity squared e^2 = 2f - f^2
WGS84_E2: float = 2.0 * WGS84_FLATTENING - (WGS84_FLATTENING ** 2)

# Earth J2 zonal harmonic oblateness coefficient
J2_EARTH: float = 1.08262668e-3

# Earth angular rotation rate omega (rad/s)
OMEGA_EARTH_RAD_S: float = 7.292115e-5

# Speed of light in vacuum (km/s)
SPEED_OF_LIGHT_KM_S: float = 299792.458
