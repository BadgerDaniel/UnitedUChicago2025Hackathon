# A2A v2 - Streamlined Travel Analysis Multi-Agent System

## 🎯 Purpose
Clean, production-ready implementation of the travel analysis multi-agent system with:
- ✅ No duplicate files
- ✅ No unused legacy code  
- ✅ Clear separation of concerns
- ✅ Essential functionality only

## 📁 Directory Structure

```
A2A_v2/
├── agents/                    # Specialized agent classes
│   ├── __init__.py
│   ├── weather_agent.py      # Weather analysis specialist
│   ├── event_agent.py        # Event impact specialist  
│   ├── flight_agent.py       # Flight pricing specialist
│   └── orchestrator_agent.py # Multi-agent coordinator
├── mcp_server/               # MCP server with travel tools
│   └── travel_mcp_server.py  # Unified MCP server
├── travel_agent/             # Main A2A travel agent
│   ├── travel_analysis_agent.py  # Main agent class
│   ├── main.py               # A2A server startup
│   └── task_manager.py       # Task management
├── scripts/                  # Utility scripts
│   ├── start.sh             # Start all services
│   ├── stop.sh              # Stop all services
│   └── cleanup.sh           # Complete cleanup
├── tests/                    # Test files
│   ├── test_mcp_tools.py    # MCP tools testing
│   ├── demo.py              # System demonstration
│   └── langgraph_demo.py    # LangGraph workflow demo
├── docs/                     # Documentation
│   ├── SETUP.md             # Setup instructions
│   └── ARCHITECTURE.md      # System architecture
├── requirements.txt          # Dependencies
├── pyproject.toml           # Project configuration
└── README.md                # Main documentation
```

## 🚀 Quick Start

1. **Setup Environment**:
```bash
cd A2A_v2
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
export OPENAI_API_KEY="your_key_here"
```

2. **Start System**:
```bash
chmod +x scripts/*.sh
./scripts/start.sh
```

3. **Test System**:
```bash
python tests/test_mcp_tools.py
python tests/demo.py
```

4. **Stop System**:
```bash
./scripts/stop.sh
```

## 🎯 Key Features

### ✅ What's Included:
- **Multi-Agent Coordination**: Weather, Event, Flight, and Orchestrator agents
- **Cross-Correlation Analysis**: How weather and events affect flight pricing
- **A2A Integration**: Compatible with existing A2A infrastructure
- **MCP Tools**: Weather, event, and flight analysis tools
- **LangGraph Workflows**: True multi-agent coordination (optional)
- **Clean Architecture**: No duplicate or legacy code

### ❌ What's Removed:
- Linux agent (not needed for travel analysis)
- Duplicate MCP servers
- Legacy test files
- Unused helper files
- Development artifacts

## 🏗️ Architecture

```
User Query → Travel Analysis Agent → MCP Tools → Specialized Analysis
                    ↓
         (Optional LangGraph Flow)
                    ↓
Orchestrator → Weather Agent → Event Agent → Flight Agent → Correlation → Response
```

## 📊 Services

1. **MCP Server** (Port 8000): Provides weather, event, and flight tools
2. **Travel Analysis Agent** (Port 10001): Main A2A-compatible agent
3. **LangGraph Orchestrator** (Optional): Advanced multi-agent workflows

## 🎮 Example Queries

- *"Why are flights from NYC to Chicago expensive on July 15th?"*
- *"How do weather conditions affect Miami flight pricing?"*
- *"Analyze correlation between events and travel costs to Las Vegas"*

## 🛠️ Development

The system is designed for easy extension:
- Add new specialist agents in `/agents/`
- Add new MCP tools in `/mcp_server/travel_mcp_server.py`
- Extend LangGraph workflows in `/tests/langgraph_demo.py`

This streamlined version focuses on the core travel analysis functionality while maintaining full compatibility with your A2A infrastructure.
