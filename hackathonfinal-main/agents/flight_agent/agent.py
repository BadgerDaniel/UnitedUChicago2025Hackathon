# =============================================================================
# agents/flight_agent/agent.py
# =============================================================================
# Purpose:
# This agent specializes in flight pricing intelligence and route analysis using
# both Amadeus and Duffel APIs. It provides comprehensive flight search, pricing
# trends, competitive analysis, route performance, and demand patterns specifically
# for United Airlines.
# =============================================================================

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

# Google ADK imports
from google.adk.agents.llm_agent import LlmAgent
from google.adk.sessions import InMemorySessionService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.artifacts import InMemoryArtifactService
from google.adk.runners import Runner
from google.genai import types
from google.adk.tools.function_tool import FunctionTool
from google.adk.agents.readonly_context import ReadonlyContext

# MCP connector for flight tools (Amadeus and Duffel)
from utilities.mcp.mcp_connect import MCPConnector

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)


class FlightIntelligenceAgent:
    """
    An agent that provides flight pricing and route intelligence using both Amadeus 
    and Duffel APIs. Focuses on United Airlines demand forecasting and competitive analysis
    with comprehensive flight search capabilities.
    """
    
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        """
        Initialize the FlightIntelligenceAgent with MCP tools from both Amadeus and Duffel.
        """
        # Load MCP tools
        self.mcp = MCPConnector()
        mcp_tools = self.mcp.get_tools()
        
        # Find flight tools from both Amadeus and Duffel
        self.flight_tools = []
        
        # Amadeus tool names
        amadeus_tool_names = [
            "flight-price-analysis",
            "flight-offers-search",
            "flight-inspiration-search",
            "airport-routes",
            "airline-routes",
            "flight-delay-prediction",
            "airport-on-time-performance"
        ]
        
        # Duffel tool names (based on the actual MCP server implementation)
        duffel_tool_names = [
            "search_flights",
            "get_offer_details",
            "search_multi_city"
        ]
        
        # SQL/DuckDB tool names for historical analysis
        sql_tool_names = [
            "analyze-flight-sql",
            "get-route-prices",
            "analyze-price-trends",
            "check-weather-impact"
        ]
        
        # Combine all tool names
        all_flight_tools = amadeus_tool_names + duffel_tool_names + sql_tool_names
        
        for tool in mcp_tools:
            if tool.name in all_flight_tools:
                self.flight_tools.append(tool)
                source = 'Amadeus' if tool.name in amadeus_tool_names else ('Duffel' if tool.name in duffel_tool_names else 'SQL/DuckDB')
                logger.info(f"Loaded MCP tool: {tool.name} from {source}")
        
        self._agent = self._build_agent()
        self._user_id = "flight_intelligence_user"

        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

    def _build_agent(self) -> LlmAgent:
        """
        Create the Gemini agent with flight tools from both Amadeus and Duffel.
        """
        tools = []
        
        # Add MCP flight tools from both providers
        for mcp_tool in self.flight_tools:
            # Create a wrapper factory to avoid closure issues
            def create_tool_wrapper(tool):
                async def wrapper(**kwargs) -> str:
                    """Execute flight tool from Amadeus or Duffel."""
                    logger.info(f"Calling MCP tool {tool.name} with args: {kwargs}")
                    result = await tool.run(kwargs)
                    logger.info(f"MCP tool {tool.name} returned: {result[:200]}...")
                    return result
                return wrapper
            
            # Create the wrapper for this specific tool
            tool_wrapper = create_tool_wrapper(mcp_tool)
            tool_wrapper.__name__ = mcp_tool.name
            tool_wrapper.__doc__ = mcp_tool.description or f"Flight tool: {mcp_tool.name}"
            
            # Wrap as FunctionTool
            tools.append(FunctionTool(tool_wrapper))
        
        return LlmAgent(
            model="gemini-2.5-flash",
            name="flight_intelligence_agent",
            description="Comprehensive flight search and analysis using Amadeus, Duffel APIs, and historical DuckDB data for United Airlines demand forecasting",
            instruction=self._system_instruction,
            tools=tools
        )
    
    def _system_instruction(self, context: ReadonlyContext) -> str:
        """System instruction for comprehensive flight intelligence capabilities."""
        return (
            "You are United Airlines' Flight Intelligence Specialist, powered by real-time data from both Amadeus and Duffel APIs.\n\n"
            
            "PRIMARY MISSION:\n"
            "Provide comprehensive flight search and actionable pricing intelligence to optimize United's revenue and market position.\n\n"
            
            "AVAILABLE TOOLS AND THEIR USAGE:\n\n"
            
            "=== AMADEUS TOOLS (GDS-based, comprehensive coverage) ===\n"
            "1. flight-offers-search - Search real-time flight prices from GDS\n"
            "   Parameters: originLocationCode (e.g. 'ORD'), destinationLocationCode (e.g. 'LHR'), departureDate (YYYY-MM-DD)\n"
            "   Example: flight-offers-search(originLocationCode='ORD', destinationLocationCode='LHR', departureDate='2025-07-20')\n\n"
            
            "2. airport-routes - Get all destinations from an airport\n"
            "   Parameters: airportCode (e.g. 'DEN')\n"
            "   Example: airport-routes(airportCode='DEN')\n\n"
            
            "3. flight-inspiration-search - Find cheapest destinations from an origin\n"
            "   Parameters: origin (e.g. 'NYC'), departureDate (optional), maxPrice (optional)\n"
            "   Example: flight-inspiration-search(origin='NYC', maxPrice=500)\n\n"
            
            "4. airline-routes - Get all routes for a specific airline\n"
            "   Parameters: airlineCode (e.g. 'UA' for United)\n\n"
            
            "5. flight-delay-prediction - Predict delays for a route\n"
            "   Parameters: originLocationCode, destinationLocationCode, departureDate, departureTime, etc.\n\n"
            
            "6. airport-on-time-performance - Get punctuality statistics\n"
            "   Parameters: airportCode, date\n\n"
            
            "7. flight-price-analysis - Analyze historical pricing\n"
            "   Parameters: originLocationCode, destinationLocationCode, departureDate\n\n"
            
            "=== DUFFEL TOOLS (Modern API, test data) ===\n"
            "8. search_flights - Comprehensive flight search (one-way, round-trip, multi-city)\n"
            "   Parameters: params object with type, origin, destination, departure_date, return_date, passengers\n"
            "   Example: search_flights(params={type: 'round_trip', origin: 'ORD', destination: 'LHR', departure_date: '2025-07-20', return_date: '2025-07-27'})\n\n"
            
            "9. get_offer_details - Get detailed information about a specific flight offer\n"
            "   Parameters: offer_id\n"
            "   Example: get_offer_details(offer_id='off_1234567890')\n\n"
            
            "10. search_multi_city - Complex multi-city itinerary search\n"
            "    Parameters: request object with origin, destination, departure_date, additional_stops\n"
            "    Example: For multi-city trips with multiple segments\n\n"
            
            "=== SQL/DUCKDB TOOLS (Historical data analysis) ===\n"
            "11. analyze-flight-sql - Natural language queries on historical flight/weather data\n"
            "    Parameters: question (natural language query)\n"
            "    Example: analyze-flight-sql(question='Show price spikes for Chicago to London flights during storms')\n\n"
            
            "12. get-route-prices - Get historical prices for specific routes\n"
            "    Parameters: origin_city, destination_city, start_date (optional), end_date (optional)\n"
            "    Example: get-route-prices(origin_city='Chicago', destination_city='London')\n\n"
            
            "13. analyze-price-trends - Analyze pricing trends over time\n"
            "    Parameters: origin_city, destination_city, time_period (monthly/weekly/daily)\n"
            "    Example: analyze-price-trends(origin_city='Chicago', destination_city='London', time_period='monthly')\n\n"
            
            "14. check-weather-impact - Check weather conditions and price impacts\n"
            "    Parameters: city, date (YYYY-MM-DD)\n"
            "    Example: check-weather-impact(city='Chicago', date='2025-01-15')\n\n"
            
            "TOOL SELECTION STRATEGY:\n"
            "- Use Amadeus for: GDS inventory, route analysis, delay predictions, real-time data\n"
            "- Use Duffel for: Modern search features, complex itineraries, detailed filtering\n"
            "- Use SQL/DuckDB for: Historical trends, weather correlations, price spike analysis, trend patterns\n"
            "- Combine all sources for comprehensive market intelligence\n\n"
            
            "UNITED AIRLINES FOCUS:\n"
            "- Primary hubs: ORD (Chicago), DEN (Denver), IAH (Houston), EWR (Newark), "
            "SFO (San Francisco), IAD (Washington), LAX (Los Angeles)\n"
            "- Key competitors: Delta (DL), American (AA), Southwest (WN)\n"
            "- Premium focus: Analyze Business and First class separately from Economy\n"
            "- Revenue optimization: Focus on yield, not just load factor\n\n"
            
            "ANALYSIS FRAMEWORK:\n"
            "1. Price Elasticity:\n"
            "   - How demand responds to price changes\n"
            "   - Optimal pricing points for revenue maximization\n"
            "   - Competitive price positioning\n\n"
            
            "2. Route Performance:\n"
            "   - High-yield vs high-volume routes\n"
            "   - Seasonal patterns and trends\n"
            "   - Hub connection opportunities\n\n"
            
            "3. Competitive Intelligence:\n"
            "   - Price comparison with DL, AA on same routes\n"
            "   - Market share opportunities\n"
            "   - Service differentiation insights\n\n"
            
            "4. Demand Indicators:\n"
            "   - Price trends indicating demand strength\n"
            "   - Capacity utilization patterns\n"
            "   - Premium cabin performance\n\n"
            
            "RESPONSE FORMAT:\n"
            "- Lead with key insights and recommendations\n"
            "- Support with specific data points\n"
            "- Include competitive context\n"
            "- Suggest actionable strategies\n\n"
            
            "QUANTITATIVE OUTPUT REQUIREMENTS:\n"
            "- Always lead with specific numbers: prices in USD, counts, percentages\n"
            "- Show trends: 'Up 15% vs last month', 'Down $50 from yesterday'\n"
            "- Include ranges: 'Prices vary from $234-$1,890 with median $567'\n"
            "- Specify sample sizes: 'Based on 147 flights analyzed'\n"
            "- Add time context: 'Data from last 24 hours', 'Historical trend over 90 days'\n"
            "- Calculate key metrics: load factors, yield per mile, market share %\n"
            "- Provide confidence levels: 'High confidence (>90%)', 'Moderate confidence (70-90%)'\n"
            "- Include statistical measures: averages, medians, standard deviations\n"
            "- Show year-over-year and month-over-month comparisons\n"
            "- Quantify competitive gaps: 'United $125 premium over Delta average'\n\n"
            
            "IMPORTANT NOTES:\n"
            "- Always specify the cabin class being analyzed\n"
            "- Convert all prices to USD for consistency\n"
            "- Highlight United's advantages and vulnerabilities\n"
            "- Consider both leisure and business traveler perspectives\n\n"
            
            "WHEN USERS ASK ABOUT FLIGHTS:\n"
            "- For 'Chicago to London' → Use ORD as origin, LHR as destination\n"
            "- For 'New York' → Use NYC (covers all airports) or specify JFK/LGA/EWR\n"
            "- For 'San Francisco to Tokyo' → Use SFO as origin, NRT or HND as destination\n"
            "- Always add a reasonable departure date if not specified (e.g., 30 days from today)\n\n"
            
            "Remember: You're helping United maximize revenue, not just fill seats. "
            "Every analysis should consider yield management and competitive positioning."
        )
    
    async def invoke(self, query: str, session_id: str) -> str:
        """
        Process a query about flight pricing and route intelligence.
        
        Args:
            query: The user's question about flights/pricing
            session_id: Unique session identifier
            
        Returns:
            Analysis and insights based on Amadeus data
        """
        try:
            # Get or create session
            session = await self._runner.session_service.get_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                session_id=session_id
            )

            if session is None:
                session = await self._runner.session_service.create_session(
                    app_name=self._agent.name,
                    user_id=self._user_id,
                    session_id=session_id,
                    state={}
                )

            # Create content with proper format
            content = types.Content(
                role="user",
                parts=[types.Part.from_text(text=query)]
            )

            # Use the runner to process the message
            last_event = None
            async for event in self._runner.run_async(
                user_id=self._user_id,
                session_id=session.id,
                new_message=content
            ):
                last_event = event

            # Extract response
            if not last_event or not last_event.content or not last_event.content.parts:
                return ""

            return "\n".join([p.text for p in last_event.content.parts if p.text])
                
        except Exception as e:
            logger.error(f"Error processing flight query: {e}")
            return f"I encountered an error analyzing flight data: {str(e)}"