#!/usr/bin/env python3
"""Debug script for PVS6 connection and data parsing."""

import asyncio
import sys

# Add src to path
sys.path.insert(0, 'src')

from solar_analyzer.api.pvs6_local import PVS6LocalAPI


async def test_pvs6():
    """Test PVS6 connection and data parsing."""
    print("🔍 Testing PVS6 Connection...")

    api = PVS6LocalAPI()

    try:
        # Test basic connection
        print(f"Testing connection to {api.host}:{api.port}")
        if not await api.test_connection():
            print("❌ Connection test failed")
            return

        print("✅ Connection test passed")

        # Get device list
        print("📊 Fetching device list...")
        device_list = await api.get_device_list()

        print(f"📋 Found {len(device_list.get('devices', []))} devices")

        # Parse the data
        print("🔧 Parsing device data...")
        parsed_data = await api.parse_device_data(device_list)

        print("📈 Parsed Results:")
        print(f"  PVS Status: {parsed_data['pvs']}")
        print(f"  Total Production: {parsed_data['total_power_kw']:.3f} kW")
        print(f"  Consumption: {parsed_data['consumption_kw']:.3f} kW")
        print(f"  Grid: {parsed_data['grid_kw']:.3f} kW")
        print(f"  Power Meters: {len(parsed_data['power_meters'])}")
        print(f"  Inverters: {len(parsed_data['inverters'])}")

        # Show first few inverters
        print("\n🔋 First 3 Inverters:")
        for i, inverter in enumerate(parsed_data['inverters'][:3]):
            print(f"  {i+1}. {inverter['serial']}: {inverter['power_w']:.1f}W @ {inverter['temperature_c']:.1f}°C")

        # Show power meters
        print("\n⚡ Power Meters:")
        for meter in parsed_data['power_meters']:
            print(f"  {meter['subtype']}: {meter['power_kw']:.3f} kW ({meter['state']})")

        print("\n✅ PVS6 test completed successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_pvs6())
