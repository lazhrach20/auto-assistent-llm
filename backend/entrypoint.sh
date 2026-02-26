#!/bin/sh
set -e

echo "🔍 Waiting for PostgreSQL to be ready..."

# Wait for database to be ready (simple check with timeout)
max_attempts=30
attempt=0

until python -c "
import asyncio
import asyncpg
import sys
import os

async def check_db():
    try:
        # Extract connection details from DATABASE_URL
        db_url = os.environ.get('DATABASE_URL', '')
        db_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')
        conn = await asyncpg.connect(db_url, timeout=5)
        await conn.close()
        return True
    except Exception as e:
        print(f'Connection failed: {e}', file=sys.stderr)
        return False

sys.exit(0 if asyncio.run(check_db()) else 1)
" 2>/dev/null; do
  attempt=$((attempt + 1))
  if [ $attempt -eq $max_attempts ]; then
    echo "❌ Failed to connect to PostgreSQL after $max_attempts attempts"
    exit 1
  fi
  echo "⏳ PostgreSQL is unavailable - sleeping (attempt $attempt/$max_attempts)"
  sleep 2
done

echo "✅ PostgreSQL is ready!"

# Run migrations
echo "🔄 Running Alembic migrations..."
alembic upgrade head || {
    echo "❌ Migration failed!"
    exit 1
}

# Seed database (with idempotent check inside seed.py)
echo "🌱 Seeding database..."
python seed.py || {
    echo "⚠️  Seeding completed with warnings (admin may already exist)"
}

echo "🚀 Starting application..."
exec "$@"
