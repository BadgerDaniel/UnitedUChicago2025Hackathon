#!/bin/bash

echo "🧹 Complete System Cleanup"
echo "========================="

# Kill by specific ports
echo "Stopping services on known ports..."
for port in 8000 8001 10000 10001; do
    pid=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        echo "  Killing process $pid on port $port"
        kill -9 $pid 2>/dev/null
        sleep 1
    fi
done

# Clean up any PID files
echo "Cleaning up PID files..."
rm -f .running_pids .running_services 2>/dev/null

# Kill any remaining MCP or travel analysis processes
echo "Stopping any remaining travel analysis processes..."
pkill -f "mcp_server.py" 2>/dev/null
pkill -f "enhanced_mcp_server" 2>/dev/null  
pkill -f "simple_enhanced_main" 2>/dev/null
pkill -f "TravelAgents" 2>/dev/null

# Restore original MCP server if we backed it up
if [ -f "../../mcp_server/mcp_server_backup.py" ]; then
    echo "Restoring original MCP server..."
    cd ../../mcp_server
    mv mcp_server_backup.py mcp_server.py 2>/dev/null
    cd - > /dev/null
fi

# Final verification
echo ""
echo "🔍 Verification:"
active_ports=""
for port in 8000 8001 10000 10001; do
    if lsof -i :$port >/dev/null 2>&1; then
        active_ports="$active_ports $port"
    fi
done

if [ -z "$active_ports" ]; then
    echo "✅ All services stopped successfully!"
else
    echo "⚠️  Some ports still active:$active_ports"
    echo "   You may need to manually kill remaining processes"
fi

echo ""
echo "System is clean and ready for next session! 🚀"
