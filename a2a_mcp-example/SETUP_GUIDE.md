# SETUP GUIDE: Enhanced Travel Analysis Multi-Agent System

## Quick Setup Instructions

### 1. Prerequisites Check
- [ ] Python 3.8+ installed
- [ ] Virtual environment activated (`source venv/bin/activate`)
- [ ] OpenAI API key set in environment (`export OPENAI_API_KEY=your_key`)
- [ ] All requirements installed (`pip install -r requirements.txt`)

### 2. Make Scripts Executable
```bash
cd a2a_mcp-example/a2a_server/langgraph
chmod +x start_services.sh
chmod +x stop_services.sh
```

### 3. Start the System
```bash
# Start all services
./start_services.sh

# OR start manually:
# Terminal 1: python ../../mcp_server/enhanced_mcp_server.py
# Terminal 2: python enhanced_main.py
# Terminal 3: python main.py (original agent for comparison)
```

### 4. Test the System
```bash
# Run system tests
python test_system.py

# Run comprehensive demo
python demo.py
```

### 5. Stop the System
```bash
./stop_services.sh
```

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                 Enhanced Travel Analysis System              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │ Travel Analysis │    │ Enhanced MCP    │                │
│  │ Agent (10001)   │◄──►│ Server (8001)   │                │
│  └─────────────────┘    └─────────────────┘                │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────────────────────────────────────────────┤
│  │            Orchestrator Agent                           │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│  │  │   Weather   │ │    Event    │ │   Flight    │       │
│  │  │    Agent    │ │    Agent    │ │    Agent    │       │
│  │  └─────────────┘ └─────────────┘ └─────────────┘       │
│  │         ▲               ▲               ▲               │
│  │         └───────────────┼───────────────┘               │
│  │                         │                               │
│  │              Agent-to-Agent Communication               │
│  └─────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────────┤
│  │                  MCP Tools Layer                        │
│  │  • Weather Forecast      • Event Search                │
│  │  • Weather Impact        • Event Impact Analysis       │
│  │  • Flight Search         • Cross-Factor Analysis       │
│  │  • Flight Pricing        • Correlation Analysis        │
│  └─────────────────────────────────────────────────────────┘
└─────────────────────────────────────────────────────────────┘
```

## Example Queries to Test

### Simple Queries
- "What's the weather like in Miami this weekend?"
- "Find events in Las Vegas next month"
- "Search flights from NYC to LA"

### Complex Multi-Agent Queries
- "Why are flights from Boston to Denver expensive on July 20th?"
- "How do weather conditions affect flight prices to Miami?"
- "What events are causing high travel costs to Las Vegas?"
- "Analyze correlation between weather and flight pricing patterns"

### Agent Communication Queries
- "Get weather impact analysis and correlate with flight pricing"
- "Cross-reference event data with weather conditions for travel planning"

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using the port
   lsof -i :8001
   lsof -i :10001
   
   # Kill process if needed
   kill -9 <PID>
   ```

2. **Import Errors**
   ```bash
   # Make sure you're in the right directory and venv is activated
   cd a2a_mcp-example/a2a_server/langgraph
   source ../../../venv/bin/activate
   ```

3. **OpenAI API Errors**
   ```bash
   # Set your API key
   export OPENAI_API_KEY=your_actual_key_here
   
   # Or add to .env file
   echo "OPENAI_API_KEY=your_key" > .env
   ```

4. **MCP Connection Issues**
   - Ensure Enhanced MCP Server starts before the agents
   - Check MCP server logs for errors
   - Verify port 8001 is available

### Service Status Check
```bash
# Check if services are running
ps aux | grep python
netstat -tulpn | grep :8001
netstat -tulpn | grep :10001
```

## File Structure Summary

```
a2a_mcp-example/
├── agents/                          # Specialized agents
│   ├── __init__.py
│   ├── weather_agent.py            # Weather analysis
│   ├── event_agent.py              # Event impact analysis  
│   ├── flight_agent.py             # Flight pricing analysis
│   └── orchestrator_agent.py       # Multi-agent coordination
├── mcp_server/
│   ├── mcp_server.py               # Original MCP server
│   └── enhanced_mcp_server.py      # Enhanced with travel tools
└── a2a_server/langgraph/
    ├── agent.py                    # Original Linux agent
    ├── enhanced_agent.py           # Enhanced travel agent
    ├── main.py                     # Original main
    ├── enhanced_main.py            # Enhanced main
    ├── task_manager.py             # Task management
    ├── start_services.sh           # Start all services
    ├── stop_services.sh            # Stop all services
    ├── demo.py                     # Comprehensive demo
    └── test_system.py              # System tests
```

## Next Steps

1. **Test the Basic Setup**
   - Run `./start_services.sh`
   - Run `python test_system.py`
   - Run `python demo.py`

2. **Try Real Queries**
   - Use your A2A client to send travel analysis queries
   - Test complex multi-factor queries
   - Experiment with agent communication

3. **Extend with Real APIs**
   - Replace mock data in `enhanced_mcp_server.py`
   - Add real weather API integration (OpenWeatherMap, etc.)
   - Add real event API integration (Ticketmaster, etc.)
   - Add real flight API integration (Amadeus, etc.)

4. **Customize for Your Needs**
   - Modify agent logic in the `/agents/` directory
   - Add new MCP tools in `enhanced_mcp_server.py`
   - Extend correlation analysis algorithms
   - Add new agent types

## Support

If you encounter issues:
1. Check the logs from each service
2. Verify all dependencies are installed
3. Make sure ports are available
4. Test with simple queries first
5. Check the GitHub issues or create a new one

The system is designed to be extensible and production-ready while maintaining full compatibility with your existing A2A infrastructure.
