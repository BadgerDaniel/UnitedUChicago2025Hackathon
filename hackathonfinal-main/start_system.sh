#!/bin/bash

# Multi-Agent MCP System Startup Script
# This script kills existing processes and starts all system components in new terminals

set -e  # Exit on any error

echo "🚀 Starting Multi-Agent MCP System..."

# Get the current directory
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Kill any existing processes on the target ports
echo "🔪 Killing existing processes on ports 10000-10008..."
lsof -ti:10000 | xargs kill -9 2>/dev/null || echo "No process on port 10000"
lsof -ti:10003 | xargs kill -9 2>/dev/null || echo "No process on port 10003" 
lsof -ti:10002 | xargs kill -9 2>/dev/null || echo "No process on port 10002"
lsof -ti:10004 | xargs kill -9 2>/dev/null || echo "No process on port 10004"
lsof -ti:10005 | xargs kill -9 2>/dev/null || echo "No process on port 10005"
lsof -ti:10006 | xargs kill -9 2>/dev/null || echo "No process on port 10006"
lsof -ti:10007 | xargs kill -9 2>/dev/null || echo "No process on port 10007"
lsof -ti:10008 | xargs kill -9 2>/dev/null || echo "No process on port 10008"

# Wait a moment for processes to fully terminate
sleep 2

# Check if .env file exists and has API key
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create .env file with your GOOGLE_API_KEY"
    exit 1
fi

if ! grep -q "GOOGLE_API_KEY=" .env || grep -q "your_google_api_key_here" .env; then
    echo "❌ Error: Please set your GOOGLE_API_KEY in .env file"
    echo "Edit .env and replace 'your_google_api_key_here' with your actual API key"
    exit 1
fi

echo "✅ Environment configured"

# Ensure playwright is installed
echo "🎭 Checking playwright installation..."
if ! uv pip show playwright > /dev/null 2>&1; then
    echo "Installing playwright..."
    uv pip install playwright
    uv run playwright install chromium
else
    echo "✅ Playwright is installed"
fi

# Check if MCP terminal server exists
if [ ! -f "mcp_servers/terminal_server/terminal_server.py" ]; then
    echo "⚠️  Warning: MCP terminal server not found"
    echo "   The system will work but MCP tools won't be available"
else
    echo "✅ MCP terminal server found"
fi

# Function to open a new terminal and run a command
open_terminal() {
    local title=$1
    local command=$2
    
    osascript <<EOF
tell application "Terminal"
    set newWindow to do script "cd \"$PROJECT_DIR\" && $command"
    set custom title of front window to "$title"
end tell
EOF
}

echo "🔄 Opening terminals for all components..."

# Start all regular agents simultaneously (except orchestrator)
echo "🚀 Launching all agents simultaneously..."
open_terminal "WebScrapingAgent (Port 10002)" "source .venv/bin/activate && uv run python3 -m agents.web_scraping_agent --host localhost --port 10002"
open_terminal "GreetingAgent (Port 10003)" "source .venv/bin/activate && uv run python3 -m agents.greeting_agent --host localhost --port 10003"
open_terminal "LiveEventsAgent (Port 10004)" "source .venv/bin/activate && uv run python3 -m agents.live_events_agent --host localhost --port 10004"
open_terminal "AviationWeatherAgent (Port 10005)" "source .venv/bin/activate && uv run python3 -m agents.aviation_weather_agent --host localhost --port 10005"
open_terminal "EconomicIndicatorsAgent (Port 10006)" "source .venv/bin/activate && uv run python3 -m agents.economic_indicators_agent --host localhost --port 10006"
open_terminal "GoogleNewsAgent (Port 10007)" "source .venv/bin/activate && uv run python3 -m agents.google_news_agent --host localhost --port 10007"
open_terminal "FlightAgent (Port 10008)" "source .venv/bin/activate && uv run python3 -m agents.flight_agent --host localhost --port 10008"

echo "✅ All agent terminals opened"
echo "⏳ Waiting 10 seconds for all agents to initialize..."
sleep 10

# Start Host OrchestratorAgent LAST so it can discover all other agents
open_terminal "Host Orchestrator (Port 10000)" "source .venv/bin/activate && uv run python3 -m agents.host_agent.entry --host localhost --port 10000"
echo "✅ Host Orchestrator terminal opened"
sleep 5

# Wait for all agents to be ready
echo "⏳ Waiting for all agents to initialize..."
sleep 3

# Open CLI client in new terminal
open_terminal "A2A MCP Client" "source .venv/bin/activate && uv run python3 -m app.cmd.cmd --agent http://localhost:10000"
echo "✅ Client terminal opened"

echo ""
echo "🎉 All components started successfully in separate terminals!"
echo ""
echo "📋 System Status:"
echo "   • WebScrapingAgent:      http://localhost:10002 (Terminal: WebScrapingAgent)"
echo "   • GreetingAgent:         http://localhost:10003 (Terminal: GreetingAgent)"  
echo "   • LiveEventsAgent:       http://localhost:10004 (Terminal: LiveEventsAgent)"
echo "   • AviationWeatherAgent:  http://localhost:10005 (Terminal: AviationWeatherAgent)"
echo "   • EconomicIndicatorsAgent: http://localhost:10006 (Terminal: EconomicIndicatorsAgent)"
echo "   • GoogleNewsAgent:       http://localhost:10007 (Terminal: GoogleNewsAgent)"
echo "   • FlightAgent:           http://localhost:10008 (Terminal: FlightAgent)"
echo "   • Host Orchestrator:     http://localhost:10000 (Terminal: Host Orchestrator)"
echo "   • Client CLI:            Terminal: A2A MCP Client"
echo ""
echo "🔧 Example queries to try in the client:"
echo '   - "What time is it?"'
echo '   - "Take a screenshot of google.com"'
echo '   - "Fetch content from example.com"'
echo '   - "Generate a greeting for me"'
echo '   - "What concerts are happening in Chicago next month?"'
echo '   - "Get the METAR for JFK airport"'
echo '   - "Show me weather briefing from KJFK to KLAX"'
echo '   - "Find major events in New York this weekend that could impact flight demand"'
echo '   - "Analyze economic conditions for USA to UK flights"'
echo '   - "How is GDP growth affecting travel demand in Asia?"'
echo '   - "What is the exchange rate impact on transatlantic routes?"'
echo '   - "What major events are happening in Europe next month?"'
echo '   - "Find news about airline industry developments"'
echo '   - "Search for events impacting travel to Asia"'
echo '   - "Search for round-trip flights from Chicago to London"'
echo '   - "Find the cheapest business class flights from SFO to Tokyo"'
echo '   - "Compare United vs Delta pricing on transatlantic routes"'
echo '   - "Plan a multi-city trip: NYC to London to Paris to NYC"'
echo '   - "What are the pricing trends for premium cabins from Denver?"'
echo '   - "Get detailed airline information about United Airlines"'
echo ""
echo "🛑 To stop all components, run: ./stop_system.sh"
echo ""