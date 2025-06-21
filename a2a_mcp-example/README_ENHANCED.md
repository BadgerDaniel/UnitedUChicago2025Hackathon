# Enhanced Travel Analysis Multi-Agent System

## Overview

This enhanced A2A (Agent-to-Agent) system extends your existing LangGraph implementation with a sophisticated multi-agent architecture for travel analysis. The system coordinates between Weather, Event, and Flight agents through an Orchestrator agent to provide comprehensive travel insights and pricing correlations.

## Architecture

### Core Agents

1. **Weather Agent** (`agents/weather_agent.py`)
   - Handles weather-related queries and forecasts
   - Analyzes weather impact on travel and events
   - Provides weather correlation data for pricing analysis

2. **Event Agent** (`agents/event_agent.py`)
   - Searches and analyzes events in cities
   - Calculates event impact on travel demand
   - Provides event-based pricing trend analysis

3. **Flight Agent** (`agents/flight_agent.py`)
   - Searches flights and analyzes pricing patterns
   - Predicts price changes based on external factors
   - Provides flight recommendation analysis

4. **Orchestrator Agent** (`agents/orchestrator_agent.py`)
   - Coordinates between all specialized agents
   - Performs cross-correlation analysis
   - Generates comprehensive travel insights

### Enhanced Components

- **Enhanced MCP Server** (`mcp_server/enhanced_mcp_server.py`)
  - Provides weather, event, and flight tools
  - Supports cross-factor analysis
  - Integrates with real APIs (extendable)

- **Travel Analysis Agent** (`a2a_server/langgraph/enhanced_agent.py`)
  - Main agent that coordinates the multi-agent system
  - Handles complex travel queries
  - Supports streaming responses

## Features

### Multi-Agent Coordination
- Agents communicate directly with each other
- Shared context and data exchange
- Collaborative analysis capabilities

### Comprehensive Analysis
- Weather-flight price correlations
- Event impact on travel demand
- Multi-factor travel recommendations
- Real-time streaming analysis

### Integration with Existing A2A Structure
- Maintains compatibility with your existing system
- Uses the same A2A server framework
- Extends the existing MCP pattern

## Setup and Installation

### Prerequisites
- Python 3.8+
- All dependencies from your existing `requirements.txt`
- OpenAI API key configured

### Quick Start

1. **Make scripts executable:**
   ```bash
   chmod +x a2a_mcp-example/a2a_server/langgraph/start_services.sh
   chmod +x a2a_mcp-example/a2a_server/langgraph/stop_services.sh
   ```

2. **Start all services:**
   ```bash
   cd a2a_mcp-example/a2a_server/langgraph
   ./start_services.sh
   ```

3. **Stop all services:**
   ```bash
   ./stop_services.sh
   ```

### Manual Startup

If you prefer to start services individually:

1. **Start Enhanced MCP Server:**
   ```bash
   cd a2a_mcp-example/mcp_server
   python enhanced_mcp_server.py
   ```

2. **Start Travel Analysis Agent:**
   ```bash
   cd a2a_mcp-example/a2a_server/langgraph
   python enhanced_main.py
   ```

## Usage Examples

### Complex Query Examples

1. **Weather-Flight Correlation:**
   ```
   "Why are flights from New York to Chicago more expensive on July 15th? 
   Was it due to weather conditions?"
   ```

2. **Event Impact Analysis:**
   ```
   "How do major events in Las Vegas affect flight prices from Los Angeles?"
   ```

3. **Multi-Factor Analysis:**
   ```
   "What's the best date to travel from Boston to Miami considering weather, 
   events, and pricing patterns?"
   ```

4. **Comprehensive Recommendations:**
   ```
   "Analyze all factors affecting travel costs for NYC to LA route in July 2025"
   ```

### Agent Communication Examples

The system demonstrates agent-to-agent communication:

```python
# Weather agent informs flight agent about severe weather
weather_to_flight = await orchestrator.agent_to_agent_communication(
    from_agent="weather",
    to_agent="flight", 
    message="Severe weather expected in Chicago",
    context={"weather_impact_score": 8.5}
)
```

## System Endpoints

- **Travel Analysis Agent:** `http://localhost:10001`
- **Enhanced MCP Server:** `http://localhost:8001`
- **Original Linux Agent:** `http://localhost:10000` (for comparison)

## Configuration

### MCP Server Ports
- Enhanced MCP Server: Port 8001
- Original MCP Server: Port 8000

### Agent Ports
- Travel Analysis Agent: Port 10001
- Linux Agent: Port 10000

### Customizing the System

1. **Add Real API Integration:**
   - Update `enhanced_mcp_server.py` with real weather/event APIs
   - Replace mock data with actual API calls
   - Add API keys to environment variables

2. **Extend Agent Capabilities:**
   - Add new tools to MCP server
   - Enhance agent processing logic
   - Add new correlation analysis methods

3. **Add New Agents:**
   - Create new agent classes following the existing pattern
   - Register with orchestrator
   - Add new MCP tools as needed

## Testing

### Running Tests
```bash
cd a2a_mcp-example/a2a_server/langgraph
python enhanced_agent.py
```

This will run built-in tests for:
- Complex query processing
- Agent-to-agent communication
- Streaming analysis

### Example Test Queries

Use these queries to test the system:

1. **Simple Weather Query:** "What's the weather impact for travel to Miami?"
2. **Event Analysis:** "Find major events in Chicago affecting travel costs"
3. **Complex Correlation:** "Analyze weather and event factors affecting NYC-LA flights"

## Integration Points

### With Existing A2A System
- Uses same `AgentTaskManager` and `A2AServer`
- Compatible with existing notification system
- Maintains same response format structure

### With Real APIs
- Weather: Integrate with OpenWeatherMap, Weather.gov, etc.
- Events: Use Ticketmaster API, Eventbrite API
- Flights: Integrate with Amadeus, Skyscanner APIs

## Troubleshooting

### Common Issues

1. **Port Conflicts:**
   - Check if ports 8001, 10001 are available
   - Use different ports if needed in configuration

2. **MCP Connection Issues:**
   - Ensure Enhanced MCP Server starts before agents
   - Check MCP server logs for errors

3. **Agent Communication Failures:**
   - Verify all agents are properly initialized
   - Check for import path issues

### Logs and Debugging
- Each service logs to console
- Use debug mode in LangGraph for detailed tracing
- Check MCP server health endpoint

## Future Enhancements

### Planned Features
- Real-time API integration
- Machine learning prediction models
- Historical data analysis
- Advanced visualization dashboard
- Mobile app integration

### Scalability Considerations
- Containerized deployment
- Load balancing for multiple agent instances
- Distributed caching for API responses
- Message queue for agent communication

## Contributing

When extending the system:
1. Follow the existing agent pattern
2. Add comprehensive error handling
3. Include logging for debugging
4. Write tests for new functionality
5. Document new features

## Support

For issues with the enhanced system:
1. Check service logs first
2. Verify all dependencies are installed
3. Ensure API keys are configured (when using real APIs)
4. Test with simple queries before complex ones

The system maintains full compatibility with your existing A2A structure while providing powerful new multi-agent capabilities for comprehensive travel analysis.
