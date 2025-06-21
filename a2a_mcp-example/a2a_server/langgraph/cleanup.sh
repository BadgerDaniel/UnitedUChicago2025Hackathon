#!/bin/bash

# Quick cleanup script for any running services

echo "🧹 Cleaning up any running services..."

# Kill processes on our target ports
for port in 8000 8001 10000 10001; do
    pid=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        echo "Killing process $pid on port $port"
        kill -9 $pid 2>/dev/null
    fi
done

echo "✅ Cleanup complete!"
echo ""
echo "Now you can start the services:"
echo "./start_services.sh"
