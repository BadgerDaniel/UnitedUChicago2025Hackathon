#!/bin/bash

echo "🚀 Creating Streamlined A2A_v2 Travel Analysis System"
echo "========================================================="

# Create the clean directory structure
echo "📁 Creating directory structure..."
mkdir -p A2A_v2/{agents,mcp_server,travel_agent,scripts,docs,tests}

# Copy and streamline the essential agent files
echo "🤖 Copying specialized agents..."
cp a2a_mcp-example/agents/weather_agent.py A2A_v2/agents/
cp a2a_mcp-example/agents/event_agent.py A2A_v2/agents/
cp a2a_mcp-example/agents/flight_agent.py A2A_v2/agents/
cp a2a_mcp-example/agents/orchestrator_agent.py A2A_v2/agents/
cp a2a_mcp-example/agents/__init__.py A2A_v2/agents/

# Copy the working MCP server (simplified version)
echo "🔧 Copying MCP server..."
cp a2a_mcp-example/mcp_server/mcp_server.py A2A_v2/mcp_server/travel_mcp_server.py

# Copy the working travel agent files
echo "✈️ Copying travel agent..."
cp a2a_mcp-example/a2a_server/langgraph/simple_enhanced_agent.py A2A_v2/travel_agent/travel_analysis_agent.py
cp a2a_mcp-example/a2a_server/langgraph/simple_enhanced_main.py A2A_v2/travel_agent/main.py
cp a2a_mcp-example/a2a_server/langgraph/task_manager.py A2A_v2/travel_agent/
cp a2a_mcp-example/a2a_server/langgraph/pyproject.toml A2A_v2/

# Copy utility scripts
echo "📜 Copying scripts..."
cp a2a_mcp-example/a2a_server/langgraph/simple_start.sh A2A_v2/scripts/start.sh
cp a2a_mcp-example/a2a_server/langgraph/simple_stop.sh A2A_v2/scripts/stop.sh
cp a2a_mcp-example/a2a_server/langgraph/complete_cleanup.sh A2A_v2/scripts/cleanup.sh

# Copy test files
echo "🧪 Copying tests..."
cp a2a_mcp-example/a2a_server/langgraph/test_mcp_only.py A2A_v2/tests/
cp a2a_mcp-example/a2a_server/langgraph/working_demo.py A2A_v2/tests/
cp a2a_mcp-example/a2a_server/langgraph/true_langgraph_demo.py A2A_v2/tests/

# Copy documentation
echo "📚 Copying documentation..."
cp a2a_mcp-example/SETUP_GUIDE.md A2A_v2/docs/
cp a2a_mcp-example/requirements.txt A2A_v2/

echo ""
echo "✅ Base files copied! Now streamlining..."
