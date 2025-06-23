# United Airlines Flight Demand Prediction System

## Overview
This multi-agent system is specifically configured to analyze and predict flight demand for United Airlines. Each agent is specialized to provide United-focused insights.

## Agent Specializations for United Airlines

### 1. **GoogleNewsAgent** (Port 10007)
- Searches news specifically impacting United Airlines
- Monitors competitor news (Delta, American, Southwest)
- Tracks industry developments affecting United's routes
- **Special Feature**: Can collaborate with EconomicIndicatorsAgent for enriched analysis

### 2. **EconomicIndicatorsAgent** (Port 10006)
- Analyzes IMF data for United's key markets
- Focuses on United hub economies (Chicago, Denver, Houston, etc.)
- Tracks exchange rates for United's international routes
- Provides revenue optimization recommendations

### 3. **AviationWeatherAgent** (Port 10005)
- Monitors weather at all United hubs
- Predicts weather-related demand shifts
- Identifies opportunities when competitor hubs have bad weather
- Analyzes seasonal patterns affecting United's network

### 4. **LiveEventsAgent** (Port 10004)
- Tracks events in United hub cities
- Identifies high-yield event opportunities
- Monitors multi-city tours hitting United hubs
- Flags business events driving premium cabin demand

### 5. **OrchestratorAgent** (Port 10000)
- Coordinates multi-agent analysis for United
- Implements dynamic agent discovery
- Handles complex United-specific queries
- Ensures integrated insights, not isolated data

## United-Specific Query Examples

### Basic Hub Analysis
```
"Analyze flight demand factors for United's Chicago hub this week"
```

### Competitive Intelligence
```
"Find news about Delta and American Airlines that might affect United's competitive position"
```

### Route-Specific Analysis
```
"Provide a demand forecast for United's SFO-NRT route considering all factors"
```

### Economic Impact
```
"How will the current USD/EUR exchange rate affect United's Atlantic business class revenue?"
```

### Event-Driven Demand
```
"What conferences in San Francisco next month could drive United's premium cabin bookings?"
```

### Weather Disruption Opportunities
```
"Check if bad weather at Atlanta (Delta hub) could benefit United's connecting traffic"
```

## Agent-to-Agent Collaboration

The GoogleNewsAgent can now directly collaborate with the EconomicIndicatorsAgent:

1. **News Event Found** → GoogleNewsAgent identifies economic news
2. **Economic Context Request** → Automatically queries EconomicIndicatorsAgent
3. **Integrated Analysis** → Combines news impact with economic data
4. **United-Specific Recommendations** → Provides actionable insights

### Example Collaboration Flow:
```
User: "Find news about oil prices affecting United"
  ↓
GoogleNewsAgent: Searches for oil price news
  ↓
GoogleNewsAgent → EconomicIndicatorsAgent: "Analyze economic impact for United"
  ↓
EconomicIndicatorsAgent: Provides GDP, exchange rate context
  ↓
Combined Response: Oil price impact + economic indicators + United route recommendations
```

## Key United Airlines Focus Areas

### Hubs
- **ORD** (Chicago) - Major domestic connections
- **DEN** (Denver) - Ski season leisure, geographic advantage
- **IAH** (Houston) - Energy sector, Latin America gateway
- **EWR** (Newark) - NYC financial sector, Atlantic gateway
- **SFO** (San Francisco) - Tech sector, Pacific gateway
- **IAD** (Washington DC) - Government, international
- **LAX** (Los Angeles) - Entertainment, Pacific routes

### Key International Routes
- **Trans-Pacific**: Focus on Japan (NRT/HND), China (PEK/PVG), Hong Kong (HKG)
- **Trans-Atlantic**: London (LHR), Frankfurt (FRA), Munich (MUC)
- **Latin America**: Mexico City (MEX), São Paulo (GRU), Buenos Aires (EZE)

### Revenue Optimization Focus
- Premium cabin (Business/First) yield management
- Corporate contract utilization
- MileagePlus high-value members
- Cargo opportunities on wide-body routes

## Testing the System

Run the test script to see United-focused analysis:
```bash
python test_united_analysis.py
```

This will demonstrate:
- Multi-agent coordination
- Agent-to-agent communication
- United-specific insights
- Integrated demand predictions

## Dynamic Agent Discovery

The system now supports:
- **Automatic re-discovery** when agents fail
- **Periodic discovery** every 5 minutes
- **Resilient operations** as agents come and go
- **No orchestrator restart needed** when adding/removing agents