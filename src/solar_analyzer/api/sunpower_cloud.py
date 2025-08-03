"""MySunPower API client for cloud-based data access."""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel

from solar_analyzer.config import settings


class SunPowerCloudAPI:
    """Client for accessing SunPower data via MySunPower API."""

    def __init__(self):
        """Initialize the API client."""
        self.base_url = "https://monitor.mysunpower.com/CustomerPortal/api/v1/"
        self.graphql_url = "https://monitor.mysunpower.com/CustomerPortal/graphql"
        self.access_token = settings.sunpower_access_token
        self.site_key = settings.sunpower_site_key
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    async def get_current_power(self) -> Dict[str, Any]:
        """Get current power production and consumption."""
        query = """
        query CurrentPower($siteKey: String!) {
            site(siteKey: $siteKey) {
                currentPower {
                    production
                    consumption
                    grid
                    battery
                    batterySOC
                    timestamp
                }
            }
        }
        """

        variables = {"siteKey": self.site_key}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.graphql_url,
                headers=self.headers,
                json={"query": query, "variables": variables},
            )
            response.raise_for_status()
            return response.json()

    async def get_energy_data(
        self, start_date: datetime, end_date: datetime, interval: str = "hour"
    ) -> Dict[str, Any]:
        """Get energy data for a specific time range."""
        query = """
        query EnergyData($siteKey: String!, $startDate: String!, $endDate: String!, $interval: String!) {
            site(siteKey: $siteKey) {
                energyData(startDate: $startDate, endDate: $endDate, interval: $interval) {
                    timestamp
                    production
                    consumption
                    grid
                    battery
                }
            }
        }
        """

        variables = {
            "siteKey": self.site_key,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "interval": interval,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.graphql_url,
                headers=self.headers,
                json={"query": query, "variables": variables},
            )
            response.raise_for_status()
            return response.json()

    async def get_panel_data(self) -> Dict[str, Any]:
        """Get individual panel production data."""
        query = """
        query PanelData($siteKey: String!) {
            site(siteKey: $siteKey) {
                panels {
                    id
                    serialNumber
                    currentPower
                    todayEnergy
                    totalEnergy
                    status
                    lastUpdate
                }
            }
        }
        """

        variables = {"siteKey": self.site_key}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.graphql_url,
                headers=self.headers,
                json={"query": query, "variables": variables},
            )
            response.raise_for_status()
            return response.json()

    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information and configuration."""
        query = """
        query SystemInfo($siteKey: String!) {
            site(siteKey: $siteKey) {
                info {
                    name
                    address
                    systemSize
                    panelCount
                    inverterCount
                    hasBattery
                    batteryCapacity
                    installDate
                }
            }
        }
        """

        variables = {"siteKey": self.site_key}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.graphql_url,
                headers=self.headers,
                json={"query": query, "variables": variables},
            )
            response.raise_for_status()
            return response.json()

    async def test_connection(self) -> bool:
        """Test the API connection."""
        try:
            await self.get_system_info()
            return True
        except Exception:
            return False