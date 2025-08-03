"""PVS6 local API client for direct device access."""

import asyncio
import json
from typing import Any, Dict, List, Optional

import httpx

from solar_analyzer.config import settings


class PVS6LocalAPI:
    """Client for accessing SunPower PVS6 data locally."""

    def __init__(self):
        """Initialize the API client."""
        self.host = settings.pvs6_host
        self.port = settings.pvs6_port
        self.base_url = f"http://{self.host}:{self.port}"
        self.timeout = httpx.Timeout(15.0, connect=5.0)

    async def get_device_list(self) -> Dict[str, Any]:
        """Get device list from PVS6."""
        url = f"{self.base_url}/cgi-bin/dl_cgi?Command=DeviceList"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def parse_device_data(self, device_list: Dict[str, Any]) -> Dict[str, Any]:
        """Parse device list data into structured format."""
        result = {
            "pvs": None,
            "power_meters": [],
            "inverters": [],
            "total_power_kw": 0.0,
            "consumption_kw": 0.0,
            "grid_kw": 0.0,
        }

        devices = device_list.get("devices", [])

        for device in devices:
            device_type = device.get("DEVICE_TYPE", "")

            if device_type == "PVS":
                result["pvs"] = {
                    "serial": device.get("SERIAL", ""),
                    "state": device.get("STATE", ""),
                    "software_version": device.get("SWVER", ""),
                    "model": device.get("MODEL", ""),
                }
            elif device_type == "Power Meter":
                # Handle production meter (positive power)
                power_kw = float(device.get("p_3phsum_kw", 0))
                subtype = device.get("subtype", "")
                
                meter_data = {
                    "serial": device.get("SERIAL", ""),
                    "type": device.get("TYPE", ""),
                    "subtype": subtype,
                    "power_kw": power_kw,
                    "energy_kwh": float(device.get("net_ltea_3phsum_kwh", 0)),
                    "voltage_v": float(device.get("v12_v", 0)),
                    "current_a": float(device.get("i_a", 0)),
                    "frequency_hz": float(device.get("freq_hz", 0)),
                    "state": device.get("STATE", ""),
                }
                
                result["power_meters"].append(meter_data)
                
                # Track production and consumption
                if "PRODUCTION" in subtype.upper():
                    result["total_power_kw"] = max(result["total_power_kw"], power_kw)
                elif "CONSUMPTION" in subtype.upper():
                    result["consumption_kw"] = abs(power_kw)  # Consumption is usually negative
                    
            elif device_type == "Inverter":
                power_kw = float(device.get("p_3phsum_kw", 0))
                power_w = power_kw * 1000
                
                inverter_data = {
                    "serial": device.get("SERIAL", ""),
                    "model": device.get("MODEL", ""),
                    "panel": device.get("PANEL", ""),
                    "module_serial": device.get("MOD_SN", ""),
                    "power_w": power_w,
                    "power_kw": power_kw,
                    "energy_kwh": float(device.get("ltea_3phsum_kwh", 0)),
                    "voltage_v": float(device.get("vln_3phavg_v", 0)),
                    "current_a": float(device.get("i_3phsum_a", 0)),
                    "frequency_hz": float(device.get("freq_hz", 0)),
                    "temperature_c": float(device.get("t_htsnk_degc", 0)),
                    "mppt_voltage_v": float(device.get("v_mppt1_v", 0)),
                    "mppt_current_a": float(device.get("i_mppt1_a", 0)),
                    "state": device.get("STATE", ""),
                    "datatime": device.get("DATATIME", ""),
                }
                
                result["inverters"].append(inverter_data)

        # Calculate grid power (production - consumption)
        result["grid_kw"] = result["total_power_kw"] - result["consumption_kw"]

        return result

    async def get_current_production(self) -> float:
        """Get current total production in kW."""
        try:
            device_list = await self.get_device_list()
            data = await self.parse_device_data(device_list)
            return data["total_power_kw"]
        except Exception:
            return 0.0

    async def get_panel_details(self) -> List[Dict[str, Any]]:
        """Get individual panel/inverter details."""
        try:
            device_list = await self.get_device_list()
            data = await self.parse_device_data(device_list)
            return data["inverters"]
        except Exception:
            return []

    async def test_connection(self) -> bool:
        """Test the PVS6 connection."""
        try:
            await self.get_device_list()
            return True
        except Exception:
            return False

    async def monitor_production(self, callback, interval: int = 15):
        """Monitor production data at specified interval."""
        while True:
            try:
                device_list = await self.get_device_list()
                data = await self.parse_device_data(device_list)
                await callback(data)
            except Exception as e:
                print(f"Error monitoring production: {e}")

            await asyncio.sleep(interval)