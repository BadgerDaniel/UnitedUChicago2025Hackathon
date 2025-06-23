# =============================================================================
# agents/live_events_agent/agent.py
# =============================================================================
# 🎯 Purpose:
#   A specialized agent for querying live events data from Ticketmaster.
#   This agent can search for concerts, shows, and other events by city,
#   date range, and keywords. Part of the flight demand forecasting system.
# =============================================================================

import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()  # Load environment variables

# Gemini LLM agent and supporting services from Google's ADK:
from google.adk.agents.llm_agent import LlmAgent
from google.adk.sessions import InMemorySessionService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.artifacts import InMemoryArtifactService
from google.adk.runners import Runner

# Gemini types for wrapping messages
from google.genai import types

# Helper to wrap our Python functions as "tools" for the LLM to call
from google.adk.tools.function_tool import FunctionTool
from google.adk.agents.readonly_context import ReadonlyContext

# MCP connector for live events
from utilities.mcp.mcp_connect import MCPConnector

# Create a module-level logger
logger = logging.getLogger(__name__)


class LiveEventsAgent:
    """
    🎭 Live Events Agent that provides event information using Ticketmaster data.
    
    This agent specializes in finding concerts, shows, and events that might
    impact flight demand to various cities. It can search by location, date
    range, and event type.
    """

    # Declare which content types this agent accepts
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        """
        🏗️ Constructor: build the internal LLM agent with MCP tools.
        """
        # Load MCP tools for live events
        self.mcp = MCPConnector()
        mcp_tools = self.mcp.get_tools()
        
        # Find the live events tool specifically
        self.live_events_tools = []
        for tool in mcp_tools:
            if tool.name == "get_upcoming_events":
                self.live_events_tools.append(tool)
                logger.info(f"Loaded MCP tool: {tool.name}")
        
        self.agent = self._build_agent()
        self.user_id = "live_events_user"
        
        # Runner wires together: agent logic, sessions, memory, artifacts
        self.runner = Runner(
            app_name=self.agent.name,
            agent=self.agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

    def _build_agent(self) -> LlmAgent:
        """
        🔧 Internal: define the LLM and its system instruction with MCP tools.
        """
        
        # Create tool wrappers for MCP tools
        tools = []
        for mcp_tool in self.live_events_tools:
            # Create a wrapper factory to avoid closure issues
            def create_tool_wrapper(tool):
                async def wrapper(**kwargs) -> str:
                    """Search for upcoming events."""
                    return await tool.run(kwargs)
                return wrapper
            
            # Create the wrapper for this specific tool
            tool_wrapper = create_tool_wrapper(mcp_tool)
            tool_wrapper.__name__ = mcp_tool.name
            tool_wrapper.__doc__ = mcp_tool.description or f"MCP tool: {mcp_tool.name}"
            
            # Wrap as FunctionTool
            tools.append(FunctionTool(tool_wrapper))
        
        # System instruction callback that includes current date
        def system_instruction(context: ReadonlyContext) -> str:
            today = datetime.now()
            return (
            "You are a Live Events Agent specializing in finding concerts, shows, and events "
            "that might impact travel demand.\n\n"
            
            "CORE CAPABILITY:\n"
            "You have direct access to the get_upcoming_events tool that searches Ticketmaster data. "
            "You can search for events by city, date range, and keywords.\n"
            "IMPORTANT: The tool requires these exact parameter names:\n"
            "- city: The city name (e.g., 'Chicago', 'New York')\n"
            "- start_dttm_str: Start date/time in ISO format (e.g., '2025-07-21T00:00:00Z')\n"
            "- end_dttm_str: End date/time in ISO format (e.g., '2025-07-31T23:59:59Z')\n"
            "- keyword: Optional search term (e.g., 'concert', 'festival')\n\n"
            
            "INTELLIGENT BEHAVIOR:\n"
            "- When asked about events, consider the context of flight demand forecasting\n"
            "- Identify major events that could drive significant travel (festivals, tours, sports)\n"
            "- Provide relevant details: event size, venue capacity, expected attendance\n"
            "- Consider event timing relative to flight booking patterns\n"
            "- Group similar events (e.g., multi-day festivals, concert series)\n\n"
            
            f"DATE HANDLING:\n"
            f"- Today is {today.strftime('%A, %B %d, %Y')} ({today.strftime('%Y-%m-%d')})\n"
            f"- When users ask about 'next month' or 'this weekend', calculate from today's date\n"
            f"- Always use ISO 8601 format for the MCP tool: YYYY-MM-DDTHH:MM:SSZ\n"
            f"- For 'next month', use the 1st day of next month at 00:00:00Z to last day at 23:59:59Z\n"
            f"- For 'this weekend', use upcoming Saturday 00:00:00Z to Sunday 23:59:59Z\n"
            f"- For 'tomorrow', use tomorrow's date at 00:00:00Z to 23:59:59Z\n"
            f"- Default to searching 30 days ahead if no specific dates given\n\n"
            
            "QUANTITATIVE OUTPUT REQUIREMENTS:\n"
            "- Always lead with specific numbers: 'Found 47 events', '12 major festivals'\n"
            "- Show attendance figures: '75,000 expected attendees', 'Venue capacity: 20,000'\n"
            "- Include event metrics: '3-day festival', '8 concert series', '15 performances'\n"
            "- Specify flight impacts: 'Drives ~5,000 inbound passengers to ORD'\n"
            "- Add time context: 'Event in 21 days', 'Tickets 65% sold', 'On sale for 30 days'\n"
            "- Calculate demand multipliers: 'Similar events drive 3.5x normal weekend traffic'\n"
            "- Provide price ranges: 'Tickets $45-$350', 'Average spend $127'\n"
            "- Include competitive data: 'United has 42% market share to this city'\n"
            "- Show historical data: 'Last year's event: 68,000 attended, 85% from out of town'\n"
            "- Quantify revenue opportunity: 'Potential $1.8M incremental revenue'\n\n"
            
            "RESPONSE FORMAT:\n"
            "- Summarize key events that could impact flight demand\n"
            "- Highlight major festivals, tours by popular artists, sporting events\n"
            "- Note if multiple events coincide (could amplify demand)\n"
            "- Provide ticket links for reference\n"
            "- Mention venue capacity when available\n\n"
            
            "FLIGHT DEMAND INSIGHTS:\n"
            "- Large music festivals → significant inbound travel 2-3 days before\n"
            "- Major sporting events → concentrated travel on game day\n"
            "- Multi-day conferences → business travel patterns\n"
            "- Holiday events → family travel patterns\n\n"
            
            "Remember: You're United Airlines' event intelligence specialist. Focus on events that "
            "specifically impact United's routes, hubs, and competitive position."
            )
        
        # Create and return the LlmAgent
        return LlmAgent(
            model="gemini-2.5-flash",
            name="live_events_agent",
            description="Analyzes live events that could impact flight demand using Ticketmaster data",
            instruction=system_instruction,
            tools=tools,  # MCP tools for searching events
        )

    async def invoke(self, query: str, session_id: str) -> str:
        """
        📥 Handle a user query about live events.
        
        Args:
            query (str): User's question about events
            session_id (str): Session identifier
            
        Returns:
            str: Analysis of events and potential flight demand impact
        """
        # Try to reuse an existing session or create one
        session = await self.runner.session_service.get_session(
            app_name=self.agent.name,
            user_id=self.user_id,
            session_id=session_id
        )
        
        if session is None:
            session = await self.runner.session_service.create_session(
                app_name=self.agent.name,
                user_id=self.user_id,
                session_id=session_id,
                state={}
            )
        
        # Format the user message
        content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=query)]
        )
        
        # Run the agent and collect response
        last_event = None
        async for event in self.runner.run_async(
            user_id=self.user_id,
            session_id=session.id,
            new_message=content
        ):
            last_event = event
        
        # Extract and return the response
        if not last_event or not last_event.content or not last_event.content.parts:
            return ""
        
        return "\n".join([p.text for p in last_event.content.parts if p.text])