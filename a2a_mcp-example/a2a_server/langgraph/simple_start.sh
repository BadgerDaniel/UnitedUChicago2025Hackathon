#!/bin/bash

# Simple startup script that works with existing infrastructure

echo "🚀 Starting Enhanced Travel Analysis System (Simplified)"
echo "=" * 60

# Kill any existing processes on our ports
echo "🧹 Cleaning up existing processes..."
for port in 8000 8001 10000 10001; do
    pid=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        echo "Killing process $pid on port $port"
        kill -9 $pid 2>/dev/null
    fi
done

cd "$(dirname "$0")"

echo ""
echo "1. Starting Original MCP Server (with enhanced tools)..."
cd ../../mcp_server
cp mcp_server.py mcp_server_backup.py
cat > mcp_server.py << 'EOF'
from mcp.server.fastmcp import FastMCP
import subprocess
import random
from datetime import datetime, timedelta

mcp = FastMCP("TravelAgents")

def run_command(command):
    try:
        result = subprocess.run(
            command, shell=True, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr.strip()}"

@mcp.tool()
def execute_linux_command(command: str) -> str:
    """Executes linux command"""
    return run_command(command)

@mcp.tool()
def get_weather_by_city(city: str) -> str:
    """Get weather forecast for a city"""
    conditions = ["Clear", "Cloudy", "Rainy", "Stormy"]
    temp = round(20 + random.uniform(-10, 15), 1)
    condition = random.choice(conditions)
    impact = random.uniform(1, 8)
    
    return f"Weather in {city}: {temp}°C, {condition}. Travel impact score: {impact:.1f}/10"

@mcp.tool()
def search_events_in_city(city: str, date: str) -> str:
    """Search for events in a city on a specific date"""
    events = ["Rock Concert", "Basketball Game", "Food Festival", "Theater Show"]
    num_events = random.randint(2, 6)
    event_list = random.sample(events, min(num_events, len(events)))
    impact = random.uniform(2, 9)
    
    return f"Events in {city} on {date}: {', '.join(event_list)}. Event impact score: {impact:.1f}/10"

@mcp.tool()
def search_flights(origin: str, destination: str, date: str) -> str:
    """Search for flights between cities"""
    price = random.randint(200, 800)
    airlines = ["American", "Delta", "United"]
    airline = random.choice(airlines)
    
    return f"Flight {origin} to {destination} on {date}: {airline} Airlines, ${price}"

@mcp.tool()
def analyze_travel_correlation(origin: str, destination: str, date: str) -> str:
    """Analyze correlation between weather, events, and flight pricing"""
    weather_impact = random.uniform(1, 8)
    event_impact = random.uniform(2, 9)
    base_price = random.randint(200, 600)
    
    # Simple correlation simulation
    weather_factor = 1 + (weather_impact / 20)
    event_factor = 1 + (event_impact / 15)
    final_price = base_price * weather_factor * event_factor
    
    correlation = (weather_impact + event_impact) / 2
    
    analysis = f"""
Travel Analysis for {origin} to {destination} on {date}:

Weather Impact: {weather_impact:.1f}/10
Event Impact: {event_impact:.1f}/10
Base Flight Price: ${base_price}
Adjusted Price: ${final_price:.2f}

Correlation Analysis:
- Weather-Flight Correlation: {weather_impact * 0.8:.1f}/10
- Event-Flight Correlation: {event_impact * 0.9:.1f}/10
- Overall Impact Score: {correlation:.1f}/10

Recommendations:
"""
    
    if correlation > 7:
        analysis += "- High impact factors detected - consider alternative dates\n"
        analysis += "- Book immediately or expect higher prices\n"
    elif correlation > 4:
        analysis += "- Moderate impact expected - monitor prices\n"
        analysis += "- Consider flexible booking options\n"
    else:
        analysis += "- Normal conditions expected\n"
        analysis += "- Good time to book at regular prices\n"
    
    return analysis

mcp.run(transport="sse")
EOF

python mcp_server.py &
MCP_PID=$!
echo "MCP Server started with PID $MCP_PID on port 8000"

sleep 3

echo ""
echo "2. Starting Enhanced Travel Analysis Agent..."
cd ../a2a_server/langgraph

# Create a simplified enhanced agent that connects to port 8000
cat > simple_enhanced_agent.py << 'EOF'
import logging
from collections.abc import AsyncIterable
from typing import Any, Literal

from langchain_core.runnables.config import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel
from langchain_mcp_adapters.client import MultiServerMCPClient

logger = logging.getLogger(__name__)
memory = MemorySaver()

class ResponseFormat(BaseModel):
    status: Literal['input_required', 'completed', 'error'] = 'input_required'
    message: str

class SimpleTravelAnalysisAgent:
    SYSTEM_INSTRUCTION = (
        'You are a travel analysis assistant that uses weather, event, and flight data to help users. '
        'You can analyze how weather conditions and events affect flight pricing. '
        'Use the available tools to gather information and provide comprehensive travel insights.'
    )

    RESPONSE_FORMAT_INSTRUCTION: str = (
        'Select status as completed if you have provided a comprehensive analysis. '
        'Select status as input_required if you need more information from the user. '
        'Set response status to error if there was an error in the analysis.'
    )

    def __init__(self):
        self.model = ChatOpenAI(model="gpt-4o", temperature=0.3)
        self.graph = None
        
    async def invoke(self, query: str, sessionId: str) -> dict[str, Any]:
        try:
            async with MultiServerMCPClient({
                "travel": {
                    "url": "http://localhost:8000/sse",
                    "transport": "sse",
                }
            }) as client:
                self.graph = create_react_agent(
                    self.model,
                    tools=client.get_tools(),
                    checkpointer=memory,
                    prompt=self.SYSTEM_INSTRUCTION,
                    response_format=(self.RESPONSE_FORMAT_INSTRUCTION, ResponseFormat),
                    debug=True
                )
                config: RunnableConfig = {'configurable': {'thread_id': sessionId}}
                await self.graph.ainvoke({'messages': [('user', query)]}, config)
                return self.get_agent_response(config)
                
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                'is_task_complete': False,
                'require_user_input': True,
                'content': f'Error processing request: {str(e)}'
            }

    async def stream(self, query: str, sessionId: str) -> AsyncIterable[dict[str, Any]]:
        result = await self.invoke(query, sessionId)
        yield result

    def get_agent_response(self, config: RunnableConfig) -> dict[str, Any]:
        current_state = self.graph.get_state(config)
        structured_response = current_state.values.get('structured_response')
        
        if structured_response and isinstance(structured_response, ResponseFormat):
            if structured_response.status in {'input_required', 'error'}:
                return {
                    'is_task_complete': False,
                    'require_user_input': True,
                    'content': structured_response.message,
                }
            if structured_response.status == 'completed':
                return {
                    'is_task_complete': True,
                    'require_user_input': False,
                    'content': structured_response.message,
                }

        return {
            'is_task_complete': False,
            'require_user_input': True,
            'content': 'Please specify cities, dates, or type of travel analysis you need.',
        }

    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']
EOF

# Update the main file to use the simple agent
cat > simple_enhanced_main.py << 'EOF'
import logging
from simple_enhanced_agent import SimpleTravelAnalysisAgent
from task_manager import AgentTaskManager
from google_a2a.common.server import A2AServer
from google_a2a.common.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from google_a2a.common.utils.push_notification_auth import PushNotificationSenderAuth

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main(host="localhost", port=10001):
    try:
        capabilities = AgentCapabilities(streaming=True, pushNotifications=True)
        
        skills = [
            AgentSkill(
                id='travel_analysis',
                name='Travel Analysis',
                description='Analyzes weather, events, and flight pricing correlations',
                tags=['travel', 'weather', 'events', 'flights'],
                examples=[
                    'Why are flights expensive from NYC to Chicago?',
                    'How does weather affect flight prices to Miami?',
                    'Analyze travel factors for Boston to Denver'
                ],
            )
        ]
        
        agent_card = AgentCard(
            name='Travel Analysis Agent',
            description='Analyzes correlations between weather, events, and flight pricing',
            url=f'http://{host}:{port}/',
            version='1.0.0',
            defaultInputModes=SimpleTravelAnalysisAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=SimpleTravelAnalysisAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=skills,
        )

        notification_sender_auth = PushNotificationSenderAuth()
        notification_sender_auth.generate_jwk()
        agent = SimpleTravelAnalysisAgent()
        
        server = A2AServer(
            agent_card=agent_card,
            task_manager=AgentTaskManager(
                agent=agent,
                notification_sender_auth=notification_sender_auth,
            ),
            host=host,
            port=port,
        )

        server.app.add_route(
            '/.well-known/jwks.json',
            notification_sender_auth.handle_jwks_endpoint,
            methods=['GET'],
        )

        logger.info(f'Starting Travel Analysis Agent on {host}:{port}')
        server.start()
        
    except Exception as e:
        logger.error(f'Error starting server: {e}')
        exit(1)

if __name__ == "__main__":
    main()
EOF

python simple_enhanced_main.py &
AGENT_PID=$!
echo "Travel Analysis Agent started with PID $AGENT_PID on port 10001"

echo ""
echo "✅ System Started Successfully!"
echo ""
echo "Available Services:"
echo "- MCP Server (with travel tools): http://localhost:8000"
echo "- Travel Analysis Agent: http://localhost:10001"
echo ""
echo "Example queries to test:"
echo "- 'Why are flights from NYC to Chicago expensive?'"
echo "- 'Analyze weather impact on Miami flights'"
echo "- 'How do events affect Boston to Denver travel costs?'"
echo ""

# Save PIDs for cleanup
echo "$MCP_PID,$AGENT_PID" > .running_pids

echo "To stop services: kill $MCP_PID $AGENT_PID"
echo "Or use: ./simple_stop.sh"
echo ""
echo "System ready! 🚀"
