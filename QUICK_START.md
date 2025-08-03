# Quick Start Guide for Local Development

This guide will help you run the Solar Analyzer locally for testing without Docker.

## Prerequisites

1. **Python 3.12+** 
2. **PostgreSQL** (local installation or Docker)
3. **uv** package manager

## Step 1: Install PostgreSQL

### Option A: Using Homebrew (macOS)
```bash
brew install postgresql
brew services start postgresql
```

### Option B: Using Docker
```bash
docker run -d \
  --name postgres \
  -e POSTGRES_PASSWORD=solar_password \
  -e POSTGRES_USER=solar_user \
  -e POSTGRES_DB=solar_analyzer \
  -p 5432:5432 \
  postgres:16
```

### Option C: Using existing PostgreSQL
Make sure PostgreSQL is running and accessible on localhost:5432

## Step 2: Install uv (if not already installed)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Step 3: Run the Setup Script
```bash
chmod +x dev-setup.sh
./dev-setup.sh
```

The setup script will:
- Check PostgreSQL connection
- Create database and user
- Install Python dependencies
- Run database migrations
- Create .env file

## Step 4: Generate Sample Data (Optional)
```bash
uv run python -m solar_analyzer.utils.sample_data
```

This creates realistic sample solar data for testing the dashboard.

## Step 5: Start the Application
```bash
uv run uvicorn solar_analyzer.main:app --reload
```

## Step 6: Access the Dashboard
Open your browser to: http://localhost:8000

You'll see:
- Real-time power flow visualization with animated particles
- Live solar production and consumption metrics
- WebSocket connection status indicator
- Professional loading skeletons while data loads
- Solar-themed UI with golden gradients and energy colors

## Troubleshooting

### PostgreSQL Connection Issues
```bash
# Check if PostgreSQL is running
pg_isready -h localhost -p 5432

# If using Docker, check container
docker ps | grep postgres
```

### Database Permission Issues
```bash
# Connect to PostgreSQL and grant permissions
psql -d solar_analyzer
GRANT ALL PRIVILEGES ON DATABASE solar_analyzer TO solar_user;
GRANT ALL ON SCHEMA public TO solar_user;
```

### Missing Dependencies
```bash
# Reinstall dependencies
uv sync --refresh
```

### Port Already in Use
If port 8000 is busy, change it in .env:
```
APP_PORT=8001
```

## Configuration

Edit `.env` file to configure:
- Database connection
- SunPower API credentials (optional for testing)
- PVS6 device IP (optional for testing)

## Sample Data

The sample data generator creates:
- 7 days of realistic solar production data
- 24 hours of panel-level data
- Simulated consumption patterns
- Grid import/export calculations

This allows you to explore all dashboard features without real solar data.

## Next Steps

1. Configure your actual SunPower credentials in Settings
2. Set up automated data collection
3. Explore the dashboard features
4. Customize for your solar system

## API Documentation

Once running, visit http://localhost:8000/docs for interactive API documentation.