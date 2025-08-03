#!/usr/bin/env python3
"""Debug script for PVS6 sync including database operations."""

import asyncio
import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, 'src')

from solar_analyzer.api.pvs6_local import PVS6LocalAPI
from solar_analyzer.data.database import async_session
from solar_analyzer.data.models import PanelReading as PanelReadingModel
from solar_analyzer.data.models import SolarReading as SolarReadingModel
from solar_analyzer.data.schemas import PanelReadingCreate, SolarReadingCreate


async def test_full_sync():
    """Test the complete PVS6 sync process including database."""
    print("🔍 Testing Full PVS6 Sync Process...")

    try:
        # Test PVS6 connection
        api = PVS6LocalAPI()
        print(f"Testing connection to {api.host}:{api.port}")

        if not await api.test_connection():
            print("❌ PVS6 connection failed")
            return

        print("✅ PVS6 connection successful")

        # Get and parse data
        print("📊 Fetching and parsing data...")
        device_list = await api.get_device_list()
        data = await api.parse_device_data(device_list)

        print("📈 Data Summary:")
        print(f"  Production: {data['total_power_kw']:.3f} kW")
        print(f"  Consumption: {data['consumption_kw']:.3f} kW")
        print(f"  Grid: {data['grid_kw']:.3f} kW")
        print(f"  Inverters: {len(data['inverters'])}")

        # Test database connection
        print("🗄️  Testing database connection...")
        async with async_session() as db:
            print("✅ Database connection successful")

            # Create solar reading
            print("📝 Creating solar reading...")
            reading = SolarReadingCreate(
                timestamp=datetime.now(),
                production_kw=data["total_power_kw"],
                consumption_kw=data["consumption_kw"],
                grid_kw=data["grid_kw"],
            )

            db_reading = SolarReadingModel(**reading.model_dump())
            db.add(db_reading)
            print("✅ Solar reading created")

            # Create panel readings
            print(f"📝 Creating {len(data['inverters'])} panel readings...")
            panel_count = 0
            for inverter in data["inverters"]:
                try:
                    panel_reading = PanelReadingCreate(
                        timestamp=datetime.now(),
                        panel_id=inverter["serial"],
                        serial_number=inverter.get("module_serial", inverter["serial"]),
                        power_w=inverter["power_w"],
                        voltage_v=inverter.get("voltage_v", 0),
                        current_a=inverter.get("current_a", 0),
                        temperature_c=inverter.get("temperature_c", 0),
                    )
                    db_panel = PanelReadingModel(**panel_reading.model_dump())
                    db.add(db_panel)
                    panel_count += 1
                except Exception as e:
                    print(f"⚠️  Error with inverter {inverter['serial']}: {e}")

            print(f"✅ {panel_count} panel readings created")

            # Commit to database
            print("💾 Committing to database...")
            await db.commit()
            print("✅ Database commit successful")

        print("\n🎉 Full sync test completed successfully!")

    except Exception as e:
        print(f"❌ Error during sync: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_full_sync())
