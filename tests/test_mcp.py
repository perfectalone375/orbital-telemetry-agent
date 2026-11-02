import json
from orbital_telemetry.mcp.server import process_message

def test_mcp_handshake():
    resp = process_message({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    assert resp["result"]["serverInfo"]["name"] == "orbital-telemetry-mcp"

def test_mcp_tools():
    resp = process_message({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    tools = [t["name"] for t in resp["result"]["tools"]]
    assert "propagate_orbit" in tools
    assert "predict_ground_passes" in tools
    assert "calculate_doppler_shift" in tools

def test_mcp_tool_propagate():
    resp = process_message({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "propagate_orbit", "arguments": {"dt_seconds": 120.0}}})
    data = json.loads(resp["result"]["content"][0]["text"])
    assert "latitude_deg" in data
    assert "speed_km_s" in data
