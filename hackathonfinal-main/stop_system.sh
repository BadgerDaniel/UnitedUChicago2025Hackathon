#!/bin/bash

# Multi-Agent MCP System Stop Script
# This script kills all system components and closes their terminals

echo "🛑 Stopping Multi-Agent MCP System..."

# Kill processes on target ports
echo "🔪 Killing processes on ports 10000, 10003, 10002, 10004, 10005, 10006, 10007, 10008..."
lsof -ti:10000 | xargs kill -9 2>/dev/null && echo "✅ Stopped process on port 10000" || echo "No process on port 10000"
lsof -ti:10003 | xargs kill -9 2>/dev/null && echo "✅ Stopped process on port 10003" || echo "No process on port 10003"
lsof -ti:10002 | xargs kill -9 2>/dev/null && echo "✅ Stopped process on port 10002" || echo "No process on port 10002"
lsof -ti:10004 | xargs kill -9 2>/dev/null && echo "✅ Stopped process on port 10004" || echo "No process on port 10004"
lsof -ti:10005 | xargs kill -9 2>/dev/null && echo "✅ Stopped process on port 10005" || echo "No process on port 10005"
lsof -ti:10006 | xargs kill -9 2>/dev/null && echo "✅ Stopped process on port 10006" || echo "No process on port 10006"
lsof -ti:10007 | xargs kill -9 2>/dev/null && echo "✅ Stopped process on port 10007" || echo "No process on port 10007"
lsof -ti:10008 | xargs kill -9 2>/dev/null && echo "✅ Stopped process on port 10008" || echo "No process on port 10008"

# Also kill any Python processes related to our agents
echo "🔍 Cleaning up any remaining agent processes..."
pkill -f "agents.web_scraping_agent" 2>/dev/null || true
pkill -f "agents.greeting_agent" 2>/dev/null || true
pkill -f "agents.host_agent" 2>/dev/null || true
pkill -f "agents.live_events_agent" 2>/dev/null || true
pkill -f "agents.aviation_weather_agent" 2>/dev/null || true
pkill -f "agents.economic_indicators_agent" 2>/dev/null || true
pkill -f "agents.google_news_agent" 2>/dev/null || true
pkill -f "agents.flight_agent" 2>/dev/null || true
pkill -f "app.cmd.cmd" 2>/dev/null || true

# Close Terminal windows with specific titles
echo "🪟 Closing terminal windows..."

osascript <<'EOF'
tell application "Terminal"
    set windowTitles to {"WebScrapingAgent (Port 10002)", "GreetingAgent (Port 10003)", "LiveEventsAgent (Port 10004)", "AviationWeatherAgent (Port 10005)", "EconomicIndicatorsAgent (Port 10006)", "GoogleNewsAgent (Port 10007)", "FlightAgent (Port 10008)", "Host Orchestrator (Port 10000)", "A2A MCP Client"}
    
    set windowsClosed to 0
    
    -- First attempt: Try to close matching windows gracefully
    repeat with w in windows
        try
            set windowTitle to custom title of w
            if windowTitle is in windowTitles then
                close w saving no
                set windowsClosed to windowsClosed + 1
            end if
        end try
    end repeat
    
    -- Force close any remaining windows that match our titles
    repeat with w in windows
        try
            set windowTitle to custom title of w
            if windowTitle is in windowTitles then
                -- Force close by getting the window ID and closing it
                set wID to id of w
                do script "exit" in w
                delay 0.1
                close window id wID saving no
            end if
        end try
    end repeat
    
    if windowsClosed > 0 then
        return "✅ Closed " & windowsClosed & " terminal windows"
    else
        return "ℹ️  No matching terminal windows found"
    end if
end tell
EOF

echo "✅ System stopped successfully"

# Final cleanup - wait a moment then check if any processes remain
sleep 1
remaining=$(lsof -ti:10000,10003,10002,10004,10005,10006,10007,10008 2>/dev/null | wc -l)
if [ "$remaining" -gt 0 ]; then
    echo "⚠️  Warning: $remaining processes still running on monitored ports"
    echo "   Run 'lsof -i:10000,10003,10002,10004,10005,10006,10007,10008' to see details"
else
    echo "✅ All processes cleaned up successfully"
fi