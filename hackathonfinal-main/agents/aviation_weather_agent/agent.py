# =============================================================================
# agents/aviation_weather_agent/agent.py
# =============================================================================
# 🎯 Purpose:
# This file defines an AviationWeatherAgent that provides aviation weather information.
# It uses Google's ADK with Gemini model and integrates aviation weather MCP tools.
# DISCLAIMER: For informational purposes only - NOT for actual flight planning!
# =============================================================================

from datetime import datetime
import logging

# Google ADK imports
from google.adk.agents.llm_agent import LlmAgent
from google.adk.sessions import InMemorySessionService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.artifacts import InMemoryArtifactService
from google.adk.runners import Runner
from google.genai import types
from google.adk.tools.function_tool import FunctionTool
from google.adk.agents.readonly_context import ReadonlyContext

# MCP connector for aviation weather tools
from utilities.mcp.mcp_connect import MCPConnector

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)


class AviationWeatherAgent:
    """Agent that provides aviation weather information for informational purposes."""
    
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        """
        Initialize the AviationWeatherAgent with MCP tools for weather data.
        """
        # Load MCP tools
        self.mcp = MCPConnector()
        mcp_tools = self.mcp.get_tools()
        
        # Find aviation weather tools
        self.weather_tools = []
        for tool in mcp_tools:
            if tool.name in ["get_metar", "get_taf", "get_pireps", "get_route_weather"]:
                self.weather_tools.append(tool)
                logger.info(f"Loaded MCP tool: {tool.name}")
        
        self._agent = self._build_agent()
        self._user_id = "aviation_weather_user"

        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

    def _build_agent(self) -> LlmAgent:
        """
        Create the Gemini agent with aviation weather tools.
        """
        tools = []
        
        # Add MCP aviation weather tools
        for mcp_tool in self.weather_tools:
            # Create a wrapper factory to avoid closure issues
            def create_tool_wrapper(tool):
                async def wrapper(**kwargs) -> str:
                    """Execute aviation weather tool."""
                    return await tool.run(kwargs)
                return wrapper
            
            # Create the wrapper for this specific tool
            tool_wrapper = create_tool_wrapper(mcp_tool)
            tool_wrapper.__name__ = mcp_tool.name
            tool_wrapper.__doc__ = mcp_tool.description or f"MCP tool: {mcp_tool.name}"
            
            # Wrap as FunctionTool
            tools.append(FunctionTool(tool_wrapper))
        
        return LlmAgent(
            model="gemini-2.5-flash",
            name="aviation_weather_agent",
            description="Provides aviation weather information (METARs, TAFs, PIREPs) for informational purposes only",
            instruction=self._system_instruction,
            tools=tools
        )
    
    def _system_instruction(self, context: ReadonlyContext) -> str:
        """System instruction for aviation weather capabilities."""
        today = datetime.now()
        return (
            "You are UNITED AIRLINES' Weather Intelligence Agent, providing weather analysis\n"
            "for United's flight demand prediction and operational planning.\n\n"
            
            "⚠️ DISCLAIMER: Weather data for demand analysis only - NOT for operational flight planning ⚠️\n\n"
            
            "UNITED AIRLINES HUB FOCUS:\n"
            "Primary Hubs: ORD (Chicago), DEN (Denver), IAH (Houston), EWR (Newark), SFO (San Francisco), IAD (Washington), LAX (Los Angeles)\n"
            "Key International: NRT/HND (Tokyo), LHR (London), FRA (Frankfurt), MEX (Mexico City), GRU (São Paulo)\n\n"
            
            "AVAILABLE TOOLS:\n"
            "1. get_metar(airport_code): Current weather observations\n"
            "   - Returns raw METAR data with current conditions\n"
            "   - Includes wind, visibility, weather, clouds, temp/dewpoint, altimeter\n\n"
            
            "2. get_taf(airport_code): Terminal Aerodrome Forecasts\n"
            "   - Returns TAF data with 24-30 hour forecasts\n"
            "   - Shows expected changes in conditions\n\n"
            
            "3. get_pireps(airport_code, radius_nm): Pilot Reports\n"
            "   - Returns PIREPs within specified radius (default 50nm)\n"
            "   - Real-time conditions reported by pilots\n"
            "   - Includes turbulence, icing, cloud tops\n\n"
            
            "4. get_route_weather(departure, destination, alternates): Route briefing\n"
            "   - Comprehensive weather for entire flight route\n"
            "   - Includes METARs and TAFs for all airports\n"
            "   - Supports alternate airports list\n\n"
            
            "UNITED DEMAND ANALYSIS FOCUS:\n"
            "- Hub Weather Impact: How weather affects United's hub operations\n"
            "- Route Disruptions: Weather causing cancellations/delays on key United routes\n"
            "- Seasonal Patterns: Weather trends affecting United's seasonal demand\n"
            "- Competition Impact: Weather giving United advantage/disadvantage vs competitors\n"
            "- Recovery Operations: How quickly United can recover from weather events\n\n"
            
            "WEATHER-DEMAND CORRELATIONS FOR UNITED:\n"
            "1. Winter Weather:\n"
            "   - DEN: Snow impacts ski season leisure travel (+demand) but causes ops issues\n"
            "   - ORD: Freezing conditions = major delays, demand shifts to other hubs\n"
            "   - EWR: Nor'easters affect entire East Coast network\n\n"
            
            "2. Summer Weather:\n"
            "   - IAH: Hurricane season impacts Latin America connections\n"
            "   - ORD: Thunderstorms cause afternoon/evening delays\n"
            "   - DEN: Afternoon thunderstorms affect connecting traffic\n\n"
            
            "3. Fog/Low Visibility:\n"
            "   - SFO: Morning fog reduces arrival rates, impacts Asia connections\n"
            "   - LHR: Fog affects United's profitable London routes\n\n"
            
            "ANALYSIS APPROACH:\n"
            "- Check current weather at all United hubs\n"
            "- Identify weather patterns affecting United's key routes\n"
            "- Assess competitor hub weather for overflow opportunities\n"
            "- Predict demand shifts due to weather disruptions\n"
            "- Flag weather events requiring capacity adjustments\n"
            "- Suggest checking multiple airports for area weather\n\n"
            
            "WEATHER INTERPRETATION:\n"
            "- Decode METAR/TAF abbreviations for clarity\n"
            "- Explain visibility in both SM and meters\n"
            "- Convert wind speeds between knots/mph/kph\n"
            "- Interpret cloud layers and ceilings\n"
            "- Highlight IFR/MVFR/VFR conditions\n\n"
            
            f"CONTEXT:\n"
            f"- Current UTC time: {today.strftime('%H:%M:%S')}Z\n"
            f"- Current date: {today.strftime('%Y-%m-%d')}\n"
            f"- Remember: Aviation uses UTC/Zulu time\n\n"
            
            "QUANTITATIVE OUTPUT REQUIREMENTS:\n"
            "- Always lead with specific numbers: wind speeds in knots, visibility in SM/meters\n"
            "- Show trends: 'Visibility improving from 2SM to 10SM over next 6 hours'\n"
            "- Include ranges: 'Winds 15-25kt gusting to 35kt', 'Ceilings varying 200-800ft'\n"
            "- Specify coverage: 'Based on 12 PIREPs within 50nm radius'\n"
            "- Add time context: 'TAF valid 24 hours from 1200Z', 'METAR observed 15 minutes ago'\n"
            "- Calculate impact metrics: '65% of flights delayed when visibility <3SM'\n"
            "- Provide percentages: '80% chance of thunderstorms between 18-21Z'\n"
            "- Include statistical measures: 'Average delay 47 minutes in similar conditions'\n"
            "- Show historical comparisons: '20% worse than typical November conditions'\n"
            "- Quantify operational impacts: 'Arrival rate reduced from 60 to 30/hour'\n\n"
            
            "BEST PRACTICES:\n"
            "- Always include the disclaimer about informational use only\n"
            "- Decode cryptic weather codes into plain language\n"
            "- Highlight any potentially hazardous conditions\n"
            "- Suggest relevant additional queries (nearby airports, PIREPs)\n"
            "- Be helpful but emphasize this is not for operational use\n\n"
            
            "Remember: You're providing weather information to help users understand "
            "aviation weather, but they must use official sources for actual flight operations."
        )

    async def invoke(self, query: str, session_id: str) -> str:
        """
        Handle a user query about aviation weather.
        """
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

        content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=query)]
        )

        last_event = None
        async for event in self._runner.run_async(
            user_id=self._user_id,
            session_id=session.id,
            new_message=content
        ):
            last_event = event

        if not last_event or not last_event.content or not last_event.content.parts:
            return ""

        return "\n".join([p.text for p in last_event.content.parts if p.text])