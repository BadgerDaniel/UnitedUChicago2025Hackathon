# A2A v2 - Enhanced Travel Analysis Multi-Agent System

## 🎯 Overview

A streamlined, production-ready travel analysis system that integrates real-time weather and event data to provide intelligent travel recommendations through multi-factor correlation analysis.

## 🌟 Key Features

### ✅ Real API Integrations
- **🌦️ National Weather Service (NWS)** - Live weather conditions and impact analysis
- **🎫 Ticketmaster Events** - Real event data with attendance estimates
- **📊 Advanced Correlation Engine** - Multi-factor analysis algorithms

### ✅ Multi-Agent Architecture
- **Weather Agent** - Weather impact analysis specialist
- **Event Agent** - Event impact analysis specialist  
- **Flight Agent** - Flight pricing analysis specialist
- **Orchestrator Agent** - Multi-agent coordination and correlation

### ✅ A2A Integration
- Full compatibility with existing A2A infrastructure
- Streaming responses for complex analyses
- Structured response formats
- Push notification support

## 🚀 Quick Start

### 1. Setup Environment
```bash
cd A2A_v2
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure API Keys
```bash
cp .env.example .env
# Edit .env file and add your API keys:
# OPENAI_API_KEY=your_openai_key_here (required)
# TICKETMASTER_API_KEY=your_ticketmaster_key_here (optional but recommended)
```

### 3. Start System
```bash
chmod +x scripts/*.sh
./scripts/start.sh
```

### 4. Test System
```bash
# Test real API integrations
python tests/test_real_apis.py

# Run comprehensive demo
python tests/demo.py
```

### 5. Stop System
```bash
./scripts/stop.sh
```

## 📁 Directory Structure

```
A2A_v2/
├── agents/                           # Specialized agent classes
│   ├── __init__.py                  # Agent package initialization
│   ├── weather_agent.py            # Weather analysis specialist
│   ├── event_agent.py              # Event impact specialist
│   ├── flight_agent.py             # Flight pricing specialist
│   └── orchestrator_agent.py       # Multi-agent coordinator
├── mcp_server/                      # MCP server with real APIs
│   └── travel_mcp_server.py         # Enhanced MCP server with NWS & Ticketmaster
├── travel_agent/                    # Main A2A travel agent
│   ├── travel_analysis_agent.py     # Main agent class
│   ├── main.py                      # A2A server startup
│   └── task_manager.py             # Task management
├── scripts/                         # Utility scripts
│   ├── start.sh                     # Start all services
│   └── stop.sh                      # Stop all services
├── tests/                           # Test files
│   ├── test_real_apis.py           # Real API integration tests
│   └── demo.py                      # System demonstration
├── docs/                            # Documentation
├── .env.example                     # Environment template
├── requirements.txt                 # Dependencies
└── README.md                        # This file
```

## 🌐 API Integrations

### Weather API (National Weather Service)
- **No API key required** - Free government service
- Real-time weather conditions and forecasts
- Automated impact scoring for travel disruption
- Covers all US locations with high accuracy

### Events API (Ticketmaster)
- **API key recommended** - Get from [Ticketmaster Developer](https://developer.ticketmaster.com/)
- Live event listings and attendance estimates
- Automated impact scoring for travel demand
- Fallback data available without API key

### Flight API (Future Enhancement)
- Ready for integration with Amadeus, Skyscanner, or similar
- Currently uses intelligent pricing simulation
- Correlation analysis with weather and event factors

## 💡 Example Queries

### Simple Queries
- *"What's the weather like in Miami?"*
- *"Find events in Las Vegas this weekend"*
- *"Search flights from NYC to Chicago"*

### Complex Multi-Factor Analysis
- *"Why are flights from NYC to Chicago expensive on July 15th?"*
- *"How do current weather conditions affect Miami flight pricing?"*
- *"Analyze correlation between events and travel costs to Las Vegas"*
- *"What combination of factors is driving high travel costs to Denver?"*

### Real-Time Scenarios
- *"Are current weather conditions affecting flights to Seattle?"*
- *"What major events this weekend will impact Las Vegas travel costs?"*
- *"Compare real-time factors for Boston to Denver vs NYC to Chicago"*

## 🎯 Key Improvements Over Original

### ✅ Streamlined Architecture
- **No duplicate files** - Clean, single-purpose modules
- **No unused legacy code** - Only essential functionality
- **Clear separation** - MCP tools, agents, and A2A integration

### ✅ Real Data Integration
- **Live weather data** - National Weather Service API
- **Real event data** - Ticketmaster API integration
- **Accurate correlations** - Data-driven analysis instead of mock data

### ✅ Production Ready
- **Error handling** - Graceful fallbacks for API failures
- **Performance optimized** - Concurrent API calls
- **Scalable design** - Easy to add new data sources

### ✅ Enhanced Capabilities
- **Sophisticated scoring** - Weather and event impact algorithms
- **AI-powered insights** - Intelligent interpretation of correlation data
- **Real-time analysis** - Current conditions affecting travel

## 🔧 Development

### Adding New Data Sources
1. Add API integration to `mcp_server/travel_mcp_server.py`
2. Create corresponding agent in `agents/`
3. Update orchestrator for new correlations
4. Add tests in `tests/`

### Extending Correlation Analysis
- Modify correlation algorithms in the MCP server
- Add new impact scoring methods
- Extend the orchestrator agent coordination logic

### Adding New Routes/Cities
- Update `CITY_COORDINATES` in the MCP server
- Add new test scenarios in test files
- Extend coverage in correlation analysis

## 🧪 Testing

### API Integration Tests
```bash
python tests/test_real_apis.py
```
Tests all real API integrations and measures performance.

### System Demo
```bash
python tests/demo.py
```
Comprehensive demonstration of all system capabilities.

### Manual Testing via A2A Client
Connect your A2A client to `http://localhost:10001` and try complex queries.

## 🚀 Production Deployment

### Environment Variables
```bash
OPENAI_API_KEY=your_key_here          # Required
TICKETMASTER_API_KEY=your_key_here    # Optional but recommended
```

### Scaling Considerations
- Each component can run as separate microservice
- Add load balancing for high-volume queries
- Implement caching for API responses
- Use message queues for agent communication

### Monitoring
- API response times and error rates
- Correlation analysis accuracy
- User query patterns and satisfaction

## 🔒 Security

- API keys managed through environment variables
- Rate limiting for expensive operations
- Input validation for all queries
- Audit logging for business queries

## 📊 Performance

- **Concurrent API calls** - Multiple data sources fetched simultaneously
- **Intelligent caching** - Avoid redundant API requests
- **Optimized correlation algorithms** - Fast multi-factor analysis
- **Streaming responses** - Real-time progress for complex queries

## 🤝 Contributing

1. Test new features thoroughly
2. Maintain real API integrations
3. Follow existing code patterns
4. Add comprehensive tests
5. Update documentation

## 📝 License

Same as original A2A project.

---

## 🎉 What Makes This Special

This enhanced system provides **real-time, data-driven travel analysis** that goes far beyond simple flight search or weather lookup. It:

✅ **Correlates multiple real-world factors** affecting travel  
✅ **Provides actionable insights** based on live data  
✅ **Explains the reasoning** behind price fluctuations  
✅ **Offers intelligent recommendations** for optimal travel planning  
✅ **Integrates seamlessly** with your existing A2A infrastructure  

The result is a production-ready travel intelligence system that provides genuine value through sophisticated multi-factor analysis of real travel conditions.
