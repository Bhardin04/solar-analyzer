#!/bin/bash

# Solar Analyzer Local Development Setup Script

echo "🌞 Solar Analyzer Local Development Setup"
echo "========================================"

# Check if PostgreSQL is running
if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "❌ PostgreSQL is not running on localhost:5432"
    echo ""
    echo "Please start PostgreSQL first:"
    echo "  - On macOS with Homebrew: brew services start postgresql"
    echo "  - On Ubuntu/Debian: sudo systemctl start postgresql"
    echo "  - Or use Docker: docker run -d --name postgres -e POSTGRES_PASSWORD=solar_password -p 5432:5432 postgres:16"
    echo ""
    exit 1
fi

echo "✅ PostgreSQL is running"

# Create database and user if they don't exist
echo "📦 Setting up database..."

createdb solar_analyzer 2>/dev/null || echo "Database 'solar_analyzer' already exists"

# Try to create user (may already exist)
psql -d solar_analyzer -c "CREATE USER solar_user WITH PASSWORD 'solar_password';" 2>/dev/null || echo "User 'solar_user' already exists"
psql -d solar_analyzer -c "GRANT ALL PRIVILEGES ON DATABASE solar_analyzer TO solar_user;" 2>/dev/null
psql -d solar_analyzer -c "GRANT ALL ON SCHEMA public TO solar_user;" 2>/dev/null

echo "✅ Database setup complete"

# Install dependencies
echo "📦 Installing dependencies with uv..."
uv sync

echo "✅ Dependencies installed"

# Run migrations
echo "🔄 Running database migrations..."
uv run alembic upgrade head

echo "✅ Migrations complete"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "✅ Created .env file - please edit it with your SunPower credentials"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🚀 Setup complete! To start the development server:"
echo "   uv run uvicorn solar_analyzer.main:app --reload"
echo ""
echo "📖 The application will be available at: http://localhost:8000"
echo ""
echo "⚙️  Don't forget to configure your SunPower credentials in .env or the Settings page"