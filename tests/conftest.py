"""Shared test fixtures and configuration."""

import asyncio
import os
from datetime import datetime, timedelta
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from solar_analyzer.api.pvs6_local import PVS6LocalAPI
from solar_analyzer.api.sunpower_cloud import SunPowerCloudAPI
from solar_analyzer.config import Settings
from solar_analyzer.data.database import Base, get_db
from solar_analyzer.data.models import SolarReading, PanelReading, SystemStatus
from solar_analyzer.main import app


# Test database URLs
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
TEST_SYNC_DATABASE_URL = "sqlite:///./test.db"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings() -> Settings:
    """Test settings with overrides."""
    return Settings(
        database_url=TEST_DATABASE_URL,
        app_env="testing",
        pvs6_host="127.0.0.1",
        pvs6_port=8080,
        sunpower_access_token="test_token",
        sunpower_site_key="test_site_key",
    )


@pytest.fixture
async def test_db_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def test_db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = sessionmaker(
        test_db_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session


@pytest.fixture
def test_client(test_db_session, test_settings) -> TestClient:
    """Create test client with dependency overrides."""
    
    async def override_get_db():
        yield test_db_session
    
    def override_get_settings():
        return test_settings
    
    app.dependency_overrides[get_db] = override_get_db
    
    client = TestClient(app)
    yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
async def async_test_client(test_db_session, test_settings) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""
    
    async def override_get_db():
        yield test_db_session
    
    def override_get_settings():
        return test_settings
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def mock_pvs6_api() -> MagicMock:
    """Mock PVS6 API for testing."""
    mock_api = MagicMock(spec=PVS6LocalAPI)
    mock_api.test_connection = AsyncMock(return_value=True)
    mock_api.get_device_list = AsyncMock(return_value={
        "devices": [
            {
                "DEVICE_TYPE": "PVS",
                "SERIAL": "PVS123456",
                "STATE": "working",
                "SWVER": "1.0.0",
                "MODEL": "PVS6"
            },
            {
                "DEVICE_TYPE": "Power Meter",
                "SERIAL": "PM123456",
                "subtype": "PVS-PRODUCTION-METER",
                "p_3phsum_kw": 5.5,
                "STATE": "working"
            },
            {
                "DEVICE_TYPE": "Inverter",
                "SERIAL": "INV123456",
                "PANEL": "Panel001",
                "p_3phsum_kw": 0.3,
                "t_htsnk_degc": 25.5,
                "STATE": "working"
            }
        ]
    })
    mock_api.parse_device_data = AsyncMock(return_value={
        "pvs": {"serial": "PVS123456", "state": "working"},
        "power_meters": [{"power_kw": 5.5, "subtype": "PRODUCTION"}],
        "inverters": [{"serial": "INV123456", "power_w": 300, "temperature_c": 25.5}],
        "total_power_kw": 5.5,
        "consumption_kw": 2.5,
        "grid_kw": 3.0
    })
    return mock_api


@pytest.fixture
def mock_sunpower_api() -> MagicMock:
    """Mock SunPower cloud API for testing."""
    mock_api = MagicMock(spec=SunPowerCloudAPI)
    mock_api.test_connection = AsyncMock(return_value=True)
    mock_api.get_current_power = AsyncMock(return_value={
        "data": {
            "site": {
                "currentPower": {
                    "production": 5500,
                    "consumption": 2500,
                    "grid": 3000,
                    "timestamp": "2025-08-03T12:00:00Z"
                }
            }
        }
    })
    mock_api.get_energy_data = AsyncMock(return_value={
        "data": {
            "site": {
                "energyData": [
                    {
                        "timestamp": "2025-08-03T10:00:00Z",
                        "production": 4000,
                        "consumption": 2000,
                        "grid": 2000
                    },
                    {
                        "timestamp": "2025-08-03T11:00:00Z",
                        "production": 5000,
                        "consumption": 2200,
                        "grid": 2800
                    }
                ]
            }
        }
    })
    return mock_api


@pytest.fixture
async def sample_solar_readings(test_db_session: AsyncSession):
    """Create sample solar readings for testing."""
    base_time = datetime.now()
    readings = []
    
    for i in range(24):  # 24 hours of data
        reading = SolarReading(
            timestamp=base_time - timedelta(hours=i),
            production_kw=5.0 + (i * 0.1),
            consumption_kw=2.5 + (i * 0.05),
            grid_kw=2.5 + (i * 0.05),
        )
        readings.append(reading)
        test_db_session.add(reading)
    
    await test_db_session.commit()
    return readings


@pytest.fixture
async def sample_panel_readings(test_db_session: AsyncSession):
    """Create sample panel readings for testing."""
    base_time = datetime.now()
    readings = []
    
    for panel_id in range(1, 6):  # 5 panels
        reading = PanelReading(
            timestamp=base_time,
            panel_id=f"Panel{panel_id:03d}",
            serial_number=f"INV{panel_id:06d}",
            power_w=300 + (panel_id * 10),
            voltage_v=240.0,
            current_a=1.25,
            temperature_c=25.0 + panel_id,
        )
        readings.append(reading)
        test_db_session.add(reading)
    
    await test_db_session.commit()
    return readings


@pytest.fixture
def mock_httpx_client():
    """Mock httpx AsyncClient for external API calls."""
    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "success"}
    mock_response.raise_for_status = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.post.return_value = mock_response
    return mock_client


# Pytest markers
pytestmark = [
    pytest.mark.asyncio,
]


# Clean up test database after each test
@pytest.fixture(autouse=True)
def cleanup_test_db():
    """Clean up test database files after each test."""
    yield
    
    # Remove test database files
    test_files = ["test.db", "test.db-shm", "test.db-wal"]
    for file in test_files:
        if os.path.exists(file):
            try:
                os.remove(file)
            except OSError:
                pass