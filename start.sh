#!/bin/bash
# Production start script

echo "🚀 Starting QR Business Cards Application..."

# Set production environment
export FLASK_ENV=production

# Get port from environment or default to 8080
PORT=${PORT:-8080}

echo "📊 Environment: $FLASK_ENV"
echo "🌐 Port: $PORT"

# Start the application with Gunicorn
echo "🔄 Starting Gunicorn server..."
exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 main:app
