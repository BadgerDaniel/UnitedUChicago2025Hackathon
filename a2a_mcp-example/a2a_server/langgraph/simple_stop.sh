#!/bin/bash

# Simple stop script

echo "🛑 Stopping Travel Analysis Services..."

if [ -f ".running_pids" ]; then
    pids=$(cat .running_pids | tr ',' ' ')
    for pid in $pids; do
        if ps -p $pid > /dev/null 2>&1; then
            echo "Stopping process $pid"
            kill $pid
        fi
    done
    rm .running_pids
else
    # Fallback - kill by port
    for port in 8000 10001; do
        pid=$(lsof -ti:$port 2>/dev/null)
        if [ ! -z "$pid" ]; then
            echo "Stopping process $pid on port $port"
            kill $pid
        fi
    done
fi

echo "✅ Services stopped!"
