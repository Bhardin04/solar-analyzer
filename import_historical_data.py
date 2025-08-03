#!/usr/bin/env python3
"""Script to import historical data from MySunPower cloud API."""

import asyncio
import sys
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, 'src')

from solar_analyzer.api.sunpower_cloud import SunPowerCloudAPI
from solar_analyzer.data.database import async_session
from solar_analyzer.data.models import SolarReading as SolarReadingModel
from solar_analyzer.data.schemas import SolarReadingCreate


async def import_historical_data(start_date: datetime, end_date: datetime, interval: str = "hour"):
    """Import historical data from SunPower cloud API."""
    print(f"🔍 Importing historical data from {start_date.date()} to {end_date.date()}")

    api = SunPowerCloudAPI()

    try:
        # Test connection first
        print("Testing cloud API connection...")
        if not await api.test_connection():
            print("❌ Cannot connect to SunPower cloud API")
            print("   Check your SUNPOWER_ACCESS_TOKEN and SUNPOWER_SITE_KEY in .env")
            return

        print("✅ Cloud API connection successful")

        # Get historical data
        print(f"📊 Fetching historical data (interval: {interval})...")
        energy_data = await api.get_energy_data(start_date, end_date, interval)

        site_data = energy_data.get("data", {}).get("site", {})
        readings_data = site_data.get("energyData", [])

        if not readings_data:
            print("❌ No historical data found")
            return

        print(f"📈 Found {len(readings_data)} historical readings")

        # Import to database
        async with async_session() as db:
            imported_count = 0
            skipped_count = 0

            for reading_data in readings_data:
                try:
                    # Check if reading already exists
                    timestamp = datetime.fromisoformat(reading_data["timestamp"])

                    # Create reading
                    reading = SolarReadingCreate(
                        timestamp=timestamp,
                        production_kw=reading_data.get("production", 0) / 1000,  # Convert W to kW
                        consumption_kw=reading_data.get("consumption", 0) / 1000,
                        grid_kw=reading_data.get("grid", 0) / 1000,
                        battery_kw=reading_data.get("battery", 0) / 1000 if reading_data.get("battery") else None,
                    )

                    db_reading = SolarReadingModel(**reading.model_dump())
                    db.add(db_reading)
                    imported_count += 1

                    if imported_count % 100 == 0:
                        print(f"  Imported {imported_count} readings...")
                        await db.commit()

                except Exception as e:
                    print(f"⚠️  Error importing reading: {e}")
                    skipped_count += 1

            # Final commit
            await db.commit()
            print(f"✅ Import completed: {imported_count} imported, {skipped_count} skipped")

    except Exception as e:
        print(f"❌ Error during import: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main function to run historical data import."""
    print("🌞 SunPower Historical Data Importer")
    print("=====================================")

    # Example: Import last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    print(f"Default import range: {start_date.date()} to {end_date.date()}")

    # You can modify these dates to import different ranges
    # For example, to import from installation date:
    # start_date = datetime(2020, 1, 1)  # Replace with your installation date

    await import_historical_data(start_date, end_date, interval="hour")

    print("\n📋 To import different date ranges, modify the dates in this script")
    print("   Example date ranges:")
    print("   - Last year: start_date = datetime.now() - timedelta(days=365)")
    print("   - Since installation: start_date = datetime(2020, 1, 1)")  # Replace with your date
    print("   - Specific range: start_date = datetime(2024, 1, 1), end_date = datetime(2024, 12, 31)")


if __name__ == "__main__":
    asyncio.run(main())
