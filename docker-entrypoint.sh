#!/bin/sh
set -e

echo "Waiting for PostgreSQL database to be ready..."
python << 'EOF'
import os
import sys
import time
import psycopg2

db_url = os.environ.get("DATABASE_URL")
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
elif not db_url:
    host = os.environ.get("POSTGRES_HOST", "db")
    port = os.environ.get("POSTGRES_PORT", "5432")
    user = os.environ.get("POSTGRES_USER", "tracker_user")
    password = os.environ.get("POSTGRES_PASSWORD", "tracker_pass")
    dbname = os.environ.get("POSTGRES_DB", "tracker_db")
    db_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"

for i in range(30):
    try:
        conn = psycopg2.connect(db_url)
        conn.close()
        print("Connected to PostgreSQL successfully!")
        sys.exit(0)
    except Exception as e:
        time.sleep(1)

print("Timed out waiting for PostgreSQL.")
sys.exit(1)
EOF

echo "Running Django migrations..."
python manage.py migrate --noinput

echo "Seeding initial data..."
python manage.py seed_data

echo "Collecting static files..."
python manage.py collectstatic --noinput || true

echo "Starting application server..."
exec "$@"
