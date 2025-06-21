#!/bin/bash

echo "🛑 Stopping Enhanced Travel Analysis System"
echo "==========================================="

# Navigate to correct directory
cd "$(dirname "$0")/.."

# Read PIDs from file if it exists
if [ -f ".running_pids" ]; then
    pids=$(cat .running_pids | tr ',' ' ')
    for pid in $pids; do
        if ps -p $pid > /dev/null 2>&1; then
            echo "  Stopping process $pid"
            kill $pid 2>/dev/null
            sleep 1
            # Force kill if still running
            if ps -p $pid > /dev/null 2>&1; then
                kill -9 $pid 2>/dev/null
            fi
        fi
    done
    rm .running_pids
else
    echo "No PID file found, killing by port..."
fi

# Fallback - kill by port
for port in 8000 10001; do
    pid=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        echo "  Stopping process $pid on port $port"
        kill -9 $pid 2>/dev/null
    fi
done

# Clean up any remaining travel analysis processes
pkill -f "travel_mcp_server" 2>/dev/null
pkill -f "travel_analysis_agent" 2>/dev/null

echo ""
echo "✅ All services stopped successfully!"
echo ""
echo "🧹 System cleaned up and ready for next session"
