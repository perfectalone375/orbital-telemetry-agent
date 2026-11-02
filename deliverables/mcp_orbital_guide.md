# MCP Orbital Telemetry Integration Guide

Connect Claude Desktop, Cursor, or Antigravity to live satellite orbits.

## Configuration (Claude Desktop)
```json
{
  "mcpServers": {
    "orbital-telemetry": {
      "command": "python",
      "args": ["-m", "orbital_telemetry.mcp.server"]
    }
  }
}
```
