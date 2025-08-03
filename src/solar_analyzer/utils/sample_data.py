"""Generate sample solar data for testing."""

import asyncio
import random
from datetime import datetime, timedelta
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from solar_analyzer.data.database import async_session, engine
from solar_analyzer.data.models import Base, PanelReading, SolarReading


def generate_solar_curve(hour: int) -> float:
    """Generate realistic solar production curve based on time of day."""
    if hour < 6 or hour > 20:
        return 0.0
    
    # Peak at noon (12), with bell curve
    peak_hour = 12
    intensity = max(0, 1 - ((hour - peak_hour) / 8) ** 2)
    
    # Add some randomness
    randomness = random.uniform(0.8, 1.2)
    
    # Maximum production of 8kW system
    max_production = 8.0
    
    return max_production * intensity * randomness


def generate_consumption_pattern(hour: int) -> float:
    """Generate realistic home consumption pattern."""
    base_consumption = 0.5  # Always using some power
    
    if 6 <= hour <= 9:  # Morning peak
        return base_consumption + random.uniform(2.0, 4.0)
    elif 17 <= hour <= 22:  # Evening peak
        return base_consumption + random.uniform(3.0, 6.0)
    elif 22 <= hour or hour <= 6:  # Night
        return base_consumption + random.uniform(0.5, 1.5)
    else:  # Daytime
        return base_consumption + random.uniform(1.0, 2.5)


async def generate_sample_readings(days: int = 7) -> List[SolarReading]:
    """Generate sample solar readings for the specified number of days."""
    readings = []
    
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    
    current_time = start_time
    
    while current_time <= end_time:
        hour = current_time.hour
        
        production_kw = generate_solar_curve(hour)
        consumption_kw = generate_consumption_pattern(hour)
        
        # Calculate grid based on production vs consumption
        grid_kw = production_kw - consumption_kw
        
        # Add some battery simulation (if you have one)
        battery_kw = None
        battery_soc = None
        
        if random.random() > 0.7:  # 30% chance of having battery data
            battery_soc = random.uniform(20, 95)
            if grid_kw > 2:  # Excess production, charge battery
                battery_kw = min(2.0, grid_kw * 0.3)
                grid_kw -= battery_kw
            elif grid_kw < -1:  # High consumption, discharge battery
                battery_kw = max(-2.0, grid_kw * 0.2)
                grid_kw -= battery_kw
        
        reading = SolarReading(
            timestamp=current_time,
            production_kw=round(production_kw, 3),
            consumption_kw=round(consumption_kw, 3),
            grid_kw=round(grid_kw, 3),
            battery_kw=round(battery_kw, 3) if battery_kw else None,
            battery_soc=round(battery_soc, 1) if battery_soc else None,
        )
        
        readings.append(reading)
        current_time += timedelta(minutes=15)  # Reading every 15 minutes
    
    return readings


async def generate_sample_panel_readings(num_panels: int = 24, hours: int = 24) -> List[PanelReading]:
    """Generate sample panel readings."""
    readings = []
    
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)
    
    # Generate panel IDs
    panel_ids = [f"INV{i:03d}" for i in range(1, num_panels + 1)]
    
    current_time = start_time
    
    while current_time <= end_time:
        hour = current_time.hour
        base_production = generate_solar_curve(hour)
        
        for panel_id in panel_ids:
            # Each panel produces roughly 1/24th of total, with variation
            panel_production = (base_production / num_panels) * random.uniform(0.8, 1.2)
            panel_watts = panel_production * 1000  # Convert to watts
            
            # Add some panels with issues
            if random.random() < 0.05:  # 5% chance of panel issue
                panel_watts *= random.uniform(0.0, 0.3)
            
            # Generate realistic electrical values
            if panel_watts > 0:
                voltage = random.uniform(35, 45)
                current = panel_watts / voltage if voltage > 0 else 0
                temperature = random.uniform(25, 65) if hour >= 6 and hour <= 20 else random.uniform(15, 30)
            else:
                voltage = 0
                current = 0
                temperature = random.uniform(15, 25)
            
            reading = PanelReading(
                timestamp=current_time,
                panel_id=panel_id,
                serial_number=f"SN{random.randint(100000, 999999)}",
                power_w=round(panel_watts, 1),
                voltage_v=round(voltage, 1),
                current_a=round(current, 2),
                temperature_c=round(temperature, 1),
            )
            
            readings.append(reading)
        
        current_time += timedelta(hours=1)  # Panel readings every hour
    
    return readings


async def create_sample_data():
    """Create sample data in the database."""
    print("🎯 Creating sample solar data...")
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as session:
        # Generate solar readings for last 7 days
        print("📊 Generating solar readings...")
        solar_readings = await generate_sample_readings(days=7)
        session.add_all(solar_readings)
        
        # Generate panel readings for last 24 hours
        print("🔋 Generating panel readings...")
        panel_readings = await generate_sample_panel_readings(num_panels=24, hours=24)
        session.add_all(panel_readings)
        
        await session.commit()
        
        print(f"✅ Created {len(solar_readings)} solar readings")
        print(f"✅ Created {len(panel_readings)} panel readings")
        print("🎉 Sample data generation complete!")


if __name__ == "__main__":
    asyncio.run(create_sample_data())