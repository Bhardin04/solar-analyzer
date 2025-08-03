"""Unit tests for data models."""

from datetime import datetime

import pytest
from sqlalchemy.exc import IntegrityError

from solar_analyzer.data.models import PanelReading, SolarReading, SystemStatus


@pytest.mark.unit
class TestSolarReading:
    """Test SolarReading model."""

    async def test_create_solar_reading(self, test_db_session):
        """Test creating a solar reading."""
        reading = SolarReading(
            timestamp=datetime.now(),
            production_kw=5.5,
            consumption_kw=2.5,
            grid_kw=3.0,
        )

        test_db_session.add(reading)
        await test_db_session.commit()

        assert reading.id is not None
        assert reading.production_kw == 5.5
        assert reading.consumption_kw == 2.5
        assert reading.grid_kw == 3.0
        assert reading.created_at is not None

    async def test_solar_reading_with_battery(self, test_db_session):
        """Test solar reading with battery data."""
        reading = SolarReading(
            timestamp=datetime.now(),
            production_kw=5.5,
            consumption_kw=2.5,
            grid_kw=3.0,
            battery_kw=-1.0,
            battery_soc=75.5,
        )

        test_db_session.add(reading)
        await test_db_session.commit()

        assert reading.battery_kw == -1.0
        assert reading.battery_soc == 75.5

    async def test_solar_reading_constraints(self, test_db_session):
        """Test solar reading model constraints."""
        # Test that timestamp is required
        with pytest.raises(IntegrityError):
            reading = SolarReading(
                production_kw=5.5,
                consumption_kw=2.5,
                grid_kw=3.0,
            )
            test_db_session.add(reading)
            await test_db_session.commit()


@pytest.mark.unit
class TestPanelReading:
    """Test PanelReading model."""

    async def test_create_panel_reading(self, test_db_session):
        """Test creating a panel reading."""
        reading = PanelReading(
            timestamp=datetime.now(),
            panel_id="Panel001",
            serial_number="INV123456",
            power_w=300.0,
            voltage_v=240.0,
            current_a=1.25,
            temperature_c=25.5,
        )

        test_db_session.add(reading)
        await test_db_session.commit()

        assert reading.id is not None
        assert reading.panel_id == "Panel001"
        assert reading.serial_number == "INV123456"
        assert reading.power_w == 300.0
        assert reading.voltage_v == 240.0
        assert reading.current_a == 1.25
        assert reading.temperature_c == 25.5

    async def test_panel_reading_constraints(self, test_db_session):
        """Test panel reading model constraints."""
        # Test that panel_id is required
        with pytest.raises(IntegrityError):
            reading = PanelReading(
                timestamp=datetime.now(),
                serial_number="INV123456",
                power_w=300.0,
            )
            test_db_session.add(reading)
            await test_db_session.commit()


@pytest.mark.unit
class TestSystemStatus:
    """Test SystemStatus model."""

    async def test_create_system_status(self, test_db_session):
        """Test creating a system status."""
        status = SystemStatus(
            timestamp=datetime.now(),
            status="operational",
            message="System running normally",
            data_source="pvs6_local",
        )

        test_db_session.add(status)
        await test_db_session.commit()

        assert status.id is not None
        assert status.status == "operational"
        assert status.message == "System running normally"
        assert status.data_source == "pvs6_local"

    async def test_system_status_with_details(self, test_db_session):
        """Test system status with additional details."""
        status = SystemStatus(
            timestamp=datetime.now(),
            status="warning",
            message="Panel temperature high",
            data_source="pvs6_local",
            details={"panel_id": "Panel001", "temperature": 85.5},
        )

        test_db_session.add(status)
        await test_db_session.commit()

        assert status.details["panel_id"] == "Panel001"
        assert status.details["temperature"] == 85.5
