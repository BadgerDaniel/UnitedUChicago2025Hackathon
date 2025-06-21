#!/bin/bash

echo "🚀 Starting Enhanced Travel Analysis System with Real APIs"
echo "========================================================="

# Navigate to correct directory
cd "$(dirname "$0")/.."

# Check for environment file
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.example .env
    echo "📝 Please edit .env file and add your API keys:"
    echo "   • OPENAI_API_KEY (required)"
    echo "   • TICKETMASTER_API_KEY (optional but recommended)"
    echo ""
    echo "Then run this script again."
    exit 1
fi

# Check for required API key
if ! grep -q "OPENAI_API_KEY=sk-" .env; then
    echo "❌ OPENAI_API_KEY not found in .env file"
    echo "Please add your OpenAI API key to the .env file"
    exit 1
fi

# Check for optional Ticketmaster API key
if grep -q "TICKETMASTER_API_KEY=your_ticketmaster" .env; then
    echo "⚠️  Ticketmaster API key not configured - will use fallback event data"
    echo "   For real event data, get an API key from: https://developer.ticketmaster.com/"
else
    echo "✅ Ticketmaster API key configured for real event data"
fi

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>/dev/null ; then
        echo "Port $1 is already in use"
        return 1
    else
        return 0
    fi
}

# Kill any existing processes on our ports
echo "🧹 Cleaning up any existing services..."
for port in 8000 10001; do
    pid=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        echo "  Stopping process $pid on port $port"
        kill -9 $pid 2>/dev/null
    fi
done

echo ""
echo "1. Starting Enhanced Travel MCP Server with Real APIs (port 8000)..."
cd mcp_server
python travel_mcp_server.py &
MCP_PID=$!
echo "   Enhanced MCP Server started with PID $MCP_PID"

# Give MCP server time to start
sleep 4

echo ""
echo "2. Starting Travel Analysis Agent (port 10001)..."
cd ../travel_agent
python main.py &
AGENT_PID=$!
echo "   Travel Agent started with PID $AGENT_PID"

# Give agent time to start
sleep 3

echo ""
echo "✅ ENHANCED SYSTEM STARTED SUCCESSFULLY!"
echo "========================================"
echo ""
echo "📊 Available Services:"
echo "   • Enhanced Travel MCP Server: http://localhost:8000"
echo "   • Travel Analysis Agent: http://localhost:10001"
echo ""
echo "🌐 Real API Integrations:"
echo "   • ✅ NWS Weather API (National Weather Service)"
if grep -q "TICKETMASTER_API_KEY=your_ticketmaster" .env; then
echo "   • ⚠️  Ticketmaster Events API (fallback data - add API key for real data)"
else
echo "   • ✅ Ticketmaster Events API (real event data)"
fi
echo ""
echo "🎯 Enhanced Capabilities:"
echo "   • Real-time weather impact analysis"
echo "   • Live event data and attendance estimates"
echo "   • Sophisticated correlation algorithms"
echo "   • Multi-factor pricing impact analysis"
echo ""
echo "💬 Example Queries with Real Data:"
echo "   • 'Why are flights from NYC to Chicago expensive on July 15th?'"
echo "   • 'How do current weather conditions affect Miami flight pricing?'"
echo "   • 'Analyze real-time travel factors for Boston to Denver route'"
echo "   • 'What events in Las Vegas this weekend will impact travel costs?'"
echo ""
echo "🔧 Management:"
echo "   • Test real APIs: python tests/test_real_apis.py"
echo "   • Demo with real data: python tests/demo.py"
echo "   • Stop: ./scripts/stop.sh"
echo ""

# Save PIDs for cleanup
echo "$MCP_PID,$AGENT_PID" > .running_pids

echo "🎉 System ready with real-time data integrations!"
echo ""
echo "📈 The system now provides:"
echo "   • Actual weather conditions and impact scores"
echo "   • Real event listings and attendance estimates"
echo "   • Data-driven correlation analysis"
echo "   • Accurate travel recommendations"
