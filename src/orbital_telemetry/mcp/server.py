"""
Model Context Protocol (MCP) Server for orbital-telemetry-agent.
"""

import json
import sys
from typing import Any, Dict
from orbital_telemetry.core.tle import TLE
from orbital_telemetry.core.propagator import KeplerianPropagator
from orbital_telemetry.core.maneuvers import (
    hohmann_transfer,
    combined_hohmann_plane_change,
    bielliptic_transfer,
)
from orbital_telemetry.tracking.ground_station import GroundStation
from orbital_telemetry.tracking.pass_predictor import PassPredictor
from orbital_telemetry.tracking.doppler import DopplerCalculator
from orbital_telemetry.tracking.network import GroundStationNetwork

SAMPLE_ISS_TLE = (
    "ISS (ZARYA)",
    "1 25544U 98067A   26034.50000000  .00016717  00000-0  10270-3 0  9001",
    "2 25544  51.6400 208.5000 0005000 130.0000 230.0000 15.50000000450001",
)

TOOLS = [
    {
        "name": "propagate_orbit",
        "description": "Propagate satellite orbit to compute geodetic coordinates (lat, lon, alt) and speed.",
        "inputSchema": {
            "type": "object",
            "properties": {"dt_seconds": {"type": "number", "description": "Seconds from TLE epoch", "default": 0.0}},
        },
    },
    {
        "name": "predict_ground_passes",
        "description": "Predict satellite overhead passes for any ground station.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "station_name": {"type": "string", "default": "Hyderabad-GS"},
                "latitude_deg": {"type": "number", "default": 17.3850},
                "longitude_deg": {"type": "number", "default": 78.4867},
                "duration_hours": {"type": "number", "default": 12.0},
            },
        },
    },
    {
        "name": "calculate_doppler_shift",
        "description": "Calculate RF Doppler frequency shift for satellite downlink radio frequency.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "carrier_frequency_mhz": {"type": "number", "default": 437.5},
                "dt_seconds": {"type": "number", "default": 100.0},
            },
        },
    },
    {
        "name": "calculate_hohmann_transfer",
        "description": "Calculate orbital transfer Delta-V budget, burns, and time-of-flight between circular orbits.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "r1_km": {
                    "type": "number",
                    "description": "Initial orbit radius in km (e.g. LEO 6700)",
                    "default": 6700.0,
                },
                "r2_km": {
                    "type": "number",
                    "description": "Target orbit radius in km (e.g. GEO 42164)",
                    "default": 42164.0,
                },
                "inclination_change_deg": {
                    "type": "number",
                    "description": "Plane change angle in degrees (optional)",
                    "default": 0.0,
                },
            },
            "required": ["r1_km", "r2_km"],
        },
    },
    {
        "name": "calculate_bielliptic_transfer",
        "description": "Calculate 3-impulse bi-elliptic orbit transfer Delta-V budget and compare efficiency vs Hohmann transfer.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "r1_km": {"type": "number", "description": "Initial orbit radius in km", "default": 6700.0},
                "r2_km": {"type": "number", "description": "Final target orbit radius in km", "default": 105000.0},
                "rb_km": {
                    "type": "number",
                    "description": "Intermediate apoapsis radius in km (rb > r2)",
                    "default": 210000.0,
                },
            },
            "required": ["r1_km", "r2_km", "rb_km"],
        },
    },
    {
        "name": "calculate_ground_network_coverage",
        "description": "Analyze global multi-station satellite tracking coverage, handovers, and communication contact gaps.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "duration_hours": {
                    "type": "number",
                    "description": "Simulation timeline duration in hours",
                    "default": 12.0,
                }
            },
        },
    },
]


def handle_propagate(args: Dict[str, Any]) -> Dict[str, Any]:
    dt = float(args.get("dt_seconds", 0.0))
    tle = TLE.from_lines(*SAMPLE_ISS_TLE)
    prop = KeplerianPropagator(tle)
    state = prop.propagate(dt)
    return {
        "satellite": tle.name,
        "time_since_epoch_s": dt,
        "latitude_deg": round(state.geodetic.latitude_deg, 4),
        "longitude_deg": round(state.geodetic.longitude_deg, 4),
        "altitude_km": round(state.geodetic.altitude_km, 2),
        "speed_km_s": round(state.orbital_speed_km_s, 3),
        "period_minutes": round(tle.orbital_period_minutes, 2),
    }


def handle_passes(args: Dict[str, Any]) -> Dict[str, Any]:
    tle = TLE.from_lines(*SAMPLE_ISS_TLE)
    prop = KeplerianPropagator(tle)
    station = GroundStation(
        name=args.get("station_name", "Hyderabad-GS"),
        latitude_deg=float(args.get("latitude_deg", 17.3850)),
        longitude_deg=float(args.get("longitude_deg", 78.4867)),
        min_elevation_deg=5.0,
    )
    predictor = PassPredictor(prop, station)
    hours = float(args.get("duration_hours", 12.0))
    passes = predictor.predict_passes(duration_hours=hours, step_s=30.0)
    return {
        "satellite": tle.name,
        "ground_station": station.name,
        "total_passes_found": len(passes),
        "passes": [
            {
                "aos_time_s": p.aos_time_s,
                "los_time_s": p.los_time_s,
                "duration_s": p.duration_seconds,
                "max_elevation_deg": p.max_elevation_deg,
            }
            for p in passes[:5]
        ],
    }


def handle_doppler(args: Dict[str, Any]) -> Dict[str, Any]:
    f_mhz = float(args.get("carrier_frequency_mhz", 437.5))
    f_hz = f_mhz * 1e6
    dt = float(args.get("dt_seconds", 100.0))
    tle = TLE.from_lines(*SAMPLE_ISS_TLE)
    prop = KeplerianPropagator(tle)
    state = prop.propagate(dt)
    gs = GroundStation(name="Hyderabad", latitude_deg=17.3850, longitude_deg=78.4867)
    station_eci = gs.geodetic.to_ecef()  # Approximate at epoch
    res = DopplerCalculator.calculate_doppler(state.position_eci, state.velocity_eci_km_s, f_hz, station_eci)
    return {
        "carrier_mhz": f_mhz,
        "doppler_shift_hz": res["doppler_shift_hz"],
        "received_mhz": round(res["received_frequency_hz"] / 1e6, 6),
        "range_rate_km_s": res["range_rate_km_s"],
    }


def handle_hohmann(args: Dict[str, Any]) -> Dict[str, Any]:
    r1 = float(args.get("r1_km", 6700.0))
    r2 = float(args.get("r2_km", 42164.0))
    di = float(args.get("inclination_change_deg", 0.0))
    if di > 0:
        return combined_hohmann_plane_change(r1, r2, di)
    return hohmann_transfer(r1, r2).to_dict()


def handle_bielliptic(args: Dict[str, Any]) -> Dict[str, Any]:
    r1 = float(args.get("r1_km", 6700.0))
    r2 = float(args.get("r2_km", 105000.0))
    rb = float(args.get("rb_km", 210000.0))
    res = bielliptic_transfer(r1, r2, rb)
    return {
        "r1_km": res.r1_km,
        "r2_km": res.r2_km,
        "rb_km": res.rb_km,
        "delta_v1_km_s": res.delta_v1_km_s,
        "delta_v2_km_s": res.delta_v2_km_s,
        "delta_v3_km_s": res.delta_v3_km_s,
        "total_delta_v_km_s": res.total_delta_v_km_s,
        "total_duration_hours": res.total_duration_hours,
        "is_more_efficient_than_hohmann": res.is_more_efficient_than_hohmann,
    }


def handle_network_coverage(args: Dict[str, Any]) -> Dict[str, Any]:
    hours = float(args.get("duration_hours", 12.0))
    tle = TLE.from_lines(*SAMPLE_ISS_TLE)
    prop = KeplerianPropagator(tle)
    net = GroundStationNetwork()
    summary = net.analyze_coverage(prop, duration_hours=hours, step_s=30.0)
    return {
        "duration_hours": hours,
        "total_passes": summary.total_passes,
        "stations_contacted": summary.stations_contacted,
        "total_contact_minutes": summary.total_contact_minutes,
        "coverage_percentage_24h": summary.coverage_percentage_24h,
        "max_contact_gap_minutes": summary.max_contact_gap_minutes,
        "station_breakdown": summary.station_breakdown,
        "sample_timeline": summary.timeline[:5],
    }


def process_message(msg: Dict[str, Any]) -> Dict[str, Any]:
    method = msg.get("method")
    msg_id = msg.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "orbital-telemetry-mcp", "version": "0.1.0"},
            },
        }
    elif method == "tools/list":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": TOOLS}}
    elif method == "tools/call":
        name = msg.get("params", {}).get("name")
        args = msg.get("params", {}).get("arguments", {})
        if name == "propagate_orbit":
            res = handle_propagate(args)
        elif name == "predict_ground_passes":
            res = handle_passes(args)
        elif name == "calculate_doppler_shift":
            res = handle_doppler(args)
        elif name == "calculate_hohmann_transfer":
            res = handle_hohmann(args)
        elif name == "calculate_bielliptic_transfer":
            res = handle_bielliptic(args)
        elif name == "calculate_ground_network_coverage":
            res = handle_network_coverage(args)
        else:
            return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": "Unknown tool"}}
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {"content": [{"type": "text", "text": json.dumps(res, indent=2)}]},
        }

    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": "Unsupported method"}}


def run_stdio_server():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            resp = process_message(req)
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
        except Exception:
            pass


if __name__ == "__main__":
    run_stdio_server()
