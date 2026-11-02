"""
Command Line Interface (CLI) for orbital-telemetry-agent (orbitctl).
"""

import argparse
import sys
from orbital_telemetry.core.tle import TLE
from orbital_telemetry.core.propagator import KeplerianPropagator
from orbital_telemetry.tracking.ground_station import GroundStation
from orbital_telemetry.tracking.pass_predictor import PassPredictor

SAMPLE_ISS_TLE = (
    "ISS (ZARYA)",
    "1 25544U 98067A   26034.50000000  .00016717  00000-0  10270-3 0  9001",
    "2 25544  51.6400 208.5000 0005000 130.0000 230.0000 15.50000000450001"
)

def handle_track(args):
    tle = TLE.from_lines(*SAMPLE_ISS_TLE)
    prop = KeplerianPropagator(tle)
    state = prop.propagate(args.seconds)

    print("=" * 65)
    print("  ORBITAL TELEMETRY AGENT - SATELLITE TRACKER")
    print(f"  Target: {tle.name} (NORAD #{tle.norad_id})")
    print("=" * 65)
    print(f"  Time Since Epoch : {args.seconds:,.1f} s")
    print(f"  Sub-Satellite Lat: {state.geodetic.latitude_deg:>8.4f} deg")
    print(f"  Sub-Satellite Lon: {state.geodetic.longitude_deg:>8.4f} deg")
    print(f"  Altitude (WGS-84): {state.geodetic.altitude_km:>8.2f} km")
    print(f"  Orbital Velocity : {state.orbital_speed_km_s:>8.3f} km/s ({state.orbital_speed_km_s * 3600:,.0f} km/h)")
    print(f"  Orbital Period   : {tle.orbital_period_minutes:>8.2f} minutes")
    print("=" * 65)

def handle_passes(args):
    tle = TLE.from_lines(*SAMPLE_ISS_TLE)
    prop = KeplerianPropagator(tle)
    station = GroundStation(
        name=args.name,
        latitude_deg=args.lat,
        longitude_deg=args.lon,
        min_elevation_deg=args.min_el
    )
    predictor = PassPredictor(prop, station)
    passes = predictor.predict_passes(duration_hours=args.hours, step_s=30.0)

    print("=" * 75)
    print(f"  PREDICTED SATELLITE PASSES: {tle.name} over {station.name}")
    print(f"  Station Coordinates: Lat {station.latitude_deg:.4f}, Lon {station.longitude_deg:.4f}")
    print("=" * 75)
    print(f"{'Pass #':<8} | {'AOS (s)':<12} | {'LOS (s)':<12} | {'Duration':<10} | {'Max El':<10}")
    print("-" * 75)
    for i, p in enumerate(passes, 1):
        print(f"{i:<8} | {p.aos_time_s:<12.1f} | {p.los_time_s:<12.1f} | {p.duration_seconds:<8.0f} s | {p.max_elevation_deg:>6.1f} deg")
    print("=" * 75)

def main():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(prog="orbitctl", description="Autonomous Satellite Tracking & Orbit Dynamics CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_track = sub.add_parser("track", help="Query real-time satellite position and telemetry")
    p_track.add_argument("-s", "--seconds", type=float, default=0.0, help="Seconds from epoch")

    p_passes = sub.add_parser("passes", help="Predict ground station visible passes")
    p_passes.add_argument("--name", type=str, default="Hyderabad-GS")
    p_passes.add_argument("--lat", type=float, default=17.3850)
    p_passes.add_argument("--lon", type=float, default=78.4867)
    p_passes.add_argument("--min-el", type=float, default=5.0)
    p_passes.add_argument("--hours", type=float, default=24.0)

    args = parser.parse_args()
    if args.command == "track":
        handle_track(args)
    elif args.command == "passes":
        handle_passes(args)

if __name__ == "__main__":
    main()
