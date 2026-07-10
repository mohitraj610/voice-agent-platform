from typing import Any
import httpx

from mcp.server.fastmcp import FastMCP

#Intialize FastMCP server
mcp = FastMCP("weather")

#Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"

