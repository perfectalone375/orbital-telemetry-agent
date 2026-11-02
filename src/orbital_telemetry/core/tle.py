"""
Two-Line Element (TLE) set ingestion, parsing, and validation.
"""

import math
from dataclasses import dataclass


@dataclass
class TLE:
    """
    Structured representation of a NORAD Two-Line Element set.
    """
    name: str
    norad_id: int
    classification: str
    epoch_year: int
    epoch_day: float
    inclination_deg: float
    raan_deg: float  # Right Ascension of Ascending Node
    eccentricity: float
    arg_perigee_deg: float
    mean_anomaly_deg: float
    mean_motion_rev_day: float  # Revolutions per day
    bstar_drag: float
    revolution_number: int

    @property
    def inclination_rad(self) -> float:
        return math.radians(self.inclination_deg)

    @property
    def raan_rad(self) -> float:
        return math.radians(self.raan_deg)

    @property
    def arg_perigee_rad(self) -> float:
        return math.radians(self.arg_perigee_deg)

    @property
    def mean_anomaly_rad(self) -> float:
        return math.radians(self.mean_anomaly_deg)

    @property
    def mean_motion_rad_s(self) -> float:
        # 1 rev/day = 2*pi / 86400 rad/s
        return self.mean_motion_rev_day * (2.0 * math.pi / 86400.0)

    @property
    def orbital_period_minutes(self) -> float:
        if self.mean_motion_rev_day <= 0:
            return 0.0
        return 1440.0 / self.mean_motion_rev_day

    @property
    def semi_major_axis_km(self) -> float:
        # a = (mu / n^2)^(1/3)
        mu = 398600.4418
        n = self.mean_motion_rad_s
        return (mu / (n ** 2)) ** (1.0 / 3.0)

    @property
    def perigee_altitude_km(self) -> float:
        r_earth = 6378.137
        return self.semi_major_axis_km * (1.0 - self.eccentricity) - r_earth

    @property
    def apogee_altitude_km(self) -> float:
        r_earth = 6378.137
        return self.semi_major_axis_km * (1.0 + self.eccentricity) - r_earth

    @classmethod
    def from_lines(cls, name: str, line1: str, line2: str) -> "TLE":
        line1 = line1.strip()
        line2 = line2.strip()

        if len(line1) < 68 or len(line2) < 68:
            raise ValueError("Invalid TLE line length")

        norad_id = int(line1[2:7])
        classification = line1[7].strip() or "U"
        epoch_yr_raw = int(line1[18:20])
        epoch_year = 2000 + epoch_yr_raw if epoch_yr_raw < 57 else 1900 + epoch_yr_raw
        epoch_day = float(line1[20:32])

        # BSTAR
        bstar_mantissa = float(line1[53:59]) * 1e-5
        bstar_exp = int(line1[59:61])
        bstar = bstar_mantissa * (10 ** bstar_exp)

        # Line 2
        inc = float(line2[8:16])
        raan = float(line2[17:25])
        ecc = float("0." + line2[26:33])
        arg_p = float(line2[34:42])
        m_anom = float(line2[43:51])
        mm = float(line2[52:63])
        rev_num = int(line2[63:68].strip() or 0)

        return cls(
            name=name.strip(),
            norad_id=norad_id,
            classification=classification,
            epoch_year=epoch_year,
            epoch_day=epoch_day,
            inclination_deg=inc,
            raan_deg=raan,
            eccentricity=ecc,
            arg_perigee_deg=arg_p,
            mean_anomaly_deg=m_anom,
            mean_motion_rev_day=mm,
            bstar_drag=bstar,
            revolution_number=rev_num,
        )
