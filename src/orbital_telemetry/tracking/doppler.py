"""
RF Doppler shift calculation for satellite telemetry and radio tracking.
"""

import math
from orbital_telemetry.core.constants import SPEED_OF_LIGHT_KM_S
from orbital_telemetry.core.coordinates import ECICoordinates


class DopplerCalculator:
    """
    Computes line-of-sight relative velocity and RF Doppler shift.
    Delta_f = -f0 * (v_range / c)
    """

    @staticmethod
    def calculate_doppler(
        sat_pos_eci: ECICoordinates,
        sat_vel_eci_km_s: tuple,
        carrier_frequency_hz: float,
        station_pos_eci: ECICoordinates,
    ) -> dict:
        # Relative displacement vector
        dx = sat_pos_eci.x_km - station_pos_eci.x_km
        dy = sat_pos_eci.y_km - station_pos_eci.y_km
        dz = sat_pos_eci.z_km - station_pos_eci.z_km
        range_km = math.sqrt(dx**2 + dy**2 + dz**2)

        if range_km < 1e-6:
            return {"range_rate_km_s": 0.0, "doppler_shift_hz": 0.0, "received_frequency_hz": carrier_frequency_hz}

        # Unit vector from station to satellite
        ux = dx / range_km
        uy = dy / range_km
        uz = dz / range_km

        # Projection of relative velocity onto line of sight (range rate)
        vx, vy, vz = sat_vel_eci_km_s
        range_rate_km_s = vx * ux + vy * uy + vz * uz

        # Doppler shift: negative when approaching (+f), positive when receding (-f)
        shift_hz = -carrier_frequency_hz * (range_rate_km_s / SPEED_OF_LIGHT_KM_S)
        received_hz = carrier_frequency_hz + shift_hz

        return {
            "range_rate_km_s": round(range_rate_km_s, 4),
            "doppler_shift_hz": round(shift_hz, 2),
            "received_frequency_hz": round(received_hz, 2),
            "is_approaching": range_rate_km_s < 0,
        }
