#!/bin/bash
echo "🔧 Installing dependencies..."
pip install -r requirements.txt

echo "📦 Running migrations..."
python manage.py migrate

echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

echo "✅ Build complete!"