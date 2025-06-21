#!/bin/bash

# Stop all services script

echo "=== Stopping Enhanced Travel Analysis Multi-Agent System ==="

# Function to stop service by port
stop_by_port() {
    local port=$1
    local name=$2
    
    echo "Stopping $name on port $port..."
    
    # Find process using the port
    local pid=$(lsof -ti:$port)
    
    if [ ! -z "$pid" ]; then
        kill $pid
        echo "$name (PID $pid) stopped"
    else
        echo "No process found on port $port"
    fi
}

# Stop services
if [ -f ".running_services" ]; then
    while IFS=',' read -r service port; do
        stop_by_port $port "$service"
    done < .running_services
    
    rm .running_services
    echo "Services file cleaned up"
else
    echo "No running services file found, stopping by known ports..."
    stop_by_port 8001 "Enhanced MCP Server"
    stop_by_port 10001 "Travel Analysis Agent"
    stop_by_port 10000 "Linux Agent"
fi

echo ""
echo "All services stopped! 🛑"
