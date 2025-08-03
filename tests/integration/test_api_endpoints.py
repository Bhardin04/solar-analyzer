"""Integration tests for API endpoints."""

import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.database
class TestSolarReadingsAPI:
    """Test solar readings API endpoints."""
    
    async def test_get_current_reading(self, async_test_client: AsyncClient, sample_solar_readings):
        """Test getting current reading."""
        response = await async_test_client.get("/api/v1/current")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "production_kw" in data
        assert "consumption_kw" in data
        assert "grid_kw" in data
        assert "timestamp" in data
        assert isinstance(data["production_kw"], float)
    
    async def test_get_current_reading_no_data(self, async_test_client: AsyncClient):
        """Test getting current reading when no data exists."""
        response = await async_test_client.get("/api/v1/current")
        
        assert response.status_code == 404
    
    async def test_get_readings_with_limit(self, async_test_client: AsyncClient, sample_solar_readings):
        """Test getting readings with limit."""
        response = await async_test_client.get("/api/v1/readings?limit=5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) <= 5
        
        for reading in data:
            assert "production_kw" in reading
            assert "consumption_kw" in reading
            assert "grid_kw" in reading
    
    async def test_get_readings_with_date_range(self, async_test_client: AsyncClient, sample_solar_readings):
        """Test getting readings with date range."""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=12)
        
        response = await async_test_client.get(
            f"/api/v1/readings?start={start_time.isoformat()}&end={end_time.isoformat()}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        # Verify all readings are within the time range
        for reading in data:
            reading_time = datetime.fromisoformat(reading["timestamp"].replace("Z", "+00:00"))
            assert start_time <= reading_time.replace(tzinfo=None) <= end_time
    
    async def test_create_reading(self, async_test_client: AsyncClient):
        """Test creating a new reading."""
        reading_data = {
            "timestamp": datetime.now().isoformat(),
            "production_kw": 5.5,
            "consumption_kw": 2.5,
            "grid_kw": 3.0,
        }
        
        response = await async_test_client.post("/api/v1/readings", json=reading_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["production_kw"] == 5.5
        assert data["consumption_kw"] == 2.5
        assert data["grid_kw"] == 3.0
        assert "id" in data


@pytest.mark.integration
@pytest.mark.database
class TestStatsAPI:
    """Test statistics API endpoints."""
    
    async def test_get_today_stats(self, async_test_client: AsyncClient, sample_solar_readings):
        """Test getting today's statistics."""
        response = await async_test_client.get("/api/v1/stats/today")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["period"] == "today"
        assert "total_production_kwh" in data
        assert "total_consumption_kwh" in data
        assert "total_export_kwh" in data
        assert "total_import_kwh" in data
        assert "self_consumption_rate" in data
        assert "peak_production_kw" in data
        assert "average_production_kw" in data
        
        # Verify data types
        assert isinstance(data["total_production_kwh"], (int, float))
        assert isinstance(data["self_consumption_rate"], (int, float))
    
    async def test_get_week_stats(self, async_test_client: AsyncClient, sample_solar_readings):
        """Test getting weekly statistics."""
        response = await async_test_client.get("/api/v1/stats/week")
        
        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "week"
    
    async def test_get_stats_invalid_period(self, async_test_client: AsyncClient):
        """Test getting stats with invalid period."""
        response = await async_test_client.get("/api/v1/stats/invalid")
        
        assert response.status_code == 400


@pytest.mark.integration
@pytest.mark.database
class TestPanelReadingsAPI:
    """Test panel readings API endpoints."""
    
    async def test_get_panel_readings(self, async_test_client: AsyncClient, sample_panel_readings):
        """Test getting panel readings."""
        response = await async_test_client.get("/api/v1/panels")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        
        for reading in data:
            assert "panel_id" in reading
            assert "serial_number" in reading
            assert "power_w" in reading
            assert "temperature_c" in reading
    
    async def test_create_panel_reading(self, async_test_client: AsyncClient):
        """Test creating a panel reading."""
        reading_data = {
            "timestamp": datetime.now().isoformat(),
            "panel_id": "Panel001",
            "serial_number": "INV123456",
            "power_w": 300.0,
            "voltage_v": 240.0,
            "current_a": 1.25,
            "temperature_c": 25.5,
        }
        
        response = await async_test_client.post("/api/v1/panels", json=reading_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["panel_id"] == "Panel001"
        assert data["power_w"] == 300.0
        assert data["temperature_c"] == 25.5


@pytest.mark.integration
@pytest.mark.external_api
class TestSyncEndpoints:
    """Test data sync endpoints."""
    
    async def test_sync_local_data(self, async_test_client: AsyncClient, mock_pvs6_api):
        """Test syncing data from local PVS6."""
        # Mock the PVS6LocalAPI in the route
        with pytest.mock.patch('solar_analyzer.api.routes.PVS6LocalAPI', return_value=mock_pvs6_api):
            response = await async_test_client.post("/api/v1/sync/local")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert "message" in data
    
    async def test_sync_local_data_connection_failed(self, async_test_client: AsyncClient):
        """Test sync when PVS6 connection fails."""
        with pytest.mock.patch(
            'solar_analyzer.api.routes.PVS6LocalAPI'
        ) as mock_api_class:
            mock_api = mock_api_class.return_value
            mock_api.test_connection.return_value = False
            
            response = await async_test_client.post("/api/v1/sync/local")
        
        assert response.status_code == 503
    
    async def test_sync_cloud_data(self, async_test_client: AsyncClient, mock_sunpower_api):
        """Test syncing data from SunPower cloud."""
        with pytest.mock.patch(
            'solar_analyzer.api.routes.SunPowerCloudAPI', 
            return_value=mock_sunpower_api
        ):
            response = await async_test_client.post("/api/v1/sync/cloud")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"


@pytest.mark.integration
class TestSystemStatusAPI:
    """Test system status API endpoints."""
    
    async def test_get_system_status(self, async_test_client: AsyncClient, test_db_session):
        """Test getting system status."""
        # Create some status entries
        from solar_analyzer.data.models import SystemStatus
        
        status1 = SystemStatus(
            timestamp=datetime.now(),
            status="operational",
            component="pvs6",
            message="System running normally"
        )
        status2 = SystemStatus(
            timestamp=datetime.now() - timedelta(minutes=5),
            status="warning",
            component="database",
            message="High connection count"
        )
        
        test_db_session.add_all([status1, status2])
        await test_db_session.commit()
        
        response = await async_test_client.get("/api/v1/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 2
        
        for status in data:
            assert "status" in status
            assert "component" in status
            assert "message" in status
            assert "timestamp" in status