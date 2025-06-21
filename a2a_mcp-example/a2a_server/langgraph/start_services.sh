#!/bin/bash

# Enhanced Travel Analysis Multi-Agent System Startup Script

echo "=== Enhanced Travel Analysis Multi-Agent System ==="
echo "Starting all components..."

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>/dev/null ; then
        echo "Port $1 is already in use"
        return 1
    else
        return 0
    fi
}

# Function to start a service in background
start_service() {
    local name=$1
    local command=$2
    local port=$3
    
    echo "Starting $name on port $port..."
    
    if check_port $port; then
        eval $command &
        local pid=$!
        echo "$name started with PID $pid"
        sleep 3  # Give service more time to start
        
        # Verify service started successfully
        if ps -p $pid > /dev/null 2>&1; then
            echo "$name is running successfully"
        else
            echo "Failed to start $name"
            exit 1
        fi
    else
        echo "Cannot start $name - port $port is already in use"
        echo "To kill existing process: kill -9 \$(lsof -ti:$port)"
        exit 1
    fi
}

# Navigate to the correct directory
cd "$(dirname "$0")"

echo ""
echo "1. Starting Enhanced MCP Server (Weather, Events, Flight tools)..."
start_service "Enhanced MCP Server" "cd ../../mcp_server && python enhanced_mcp_server.py" 8001

echo ""
echo "2. Starting Travel Analysis Agent Server..."
start_service "Travel Analysis Agent" "python enhanced_main.py --port 10001" 10001

echo ""
echo "3. Starting Original Linux Agent Server (for comparison)..."
start_service "Linux Agent" "python main.py" 10000

echo ""
echo "=== All Services Started Successfully ==="
echo ""
echo "Available Services:"
echo "- Enhanced MCP Server: http://localhost:8001"
echo "- Travel Analysis Agent: http://localhost:10001"
echo "- Linux Agent: http://localhost:10000"
echo ""
echo "Agent Capabilities:"
echo "🌦️  Weather-Flight correlation analysis"
echo "🎫  Event impact assessment"
echo "✈️  Flight pricing analysis"
echo "🤝  Multi-agent coordination"
echo "📊  Real-time streaming analysis"
echo ""
echo "Example Queries for Travel Analysis Agent:"
echo "- 'Why are flights from NYC to Chicago expensive on July 15th?'"
echo "- 'How do weather conditions affect flight prices to Miami?'"
echo "- 'What events are driving up travel costs to Las Vegas next month?'"
echo "- 'Analyze correlation between weather and flight pricing for Denver flights'"
echo ""
echo "Testing commands:"
echo "- python test_system.py  # Quick system verification"
echo "- python demo.py         # Full system demonstration"
echo ""
echo "To stop all services, run: ./stop_services.sh"
echo "To view logs, check the terminal outputs"

# Create a PID file for easy cleanup
echo "Enhanced MCP Server,8001" > .running_services
echo "Travel Analysis Agent,10001" >> .running_services  
echo "Linux Agent,10000" >> .running_services

echo ""
echo "System ready for queries! 🚀"
echo ""
echo "Note: If you see import errors, the system will use fallback functionality."
echo "The MCP tools will still work for basic weather, event, and flight analysis."
