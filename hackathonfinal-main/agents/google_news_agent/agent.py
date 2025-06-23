# =============================================================================
# agents/google_news_agent/agent.py
# =============================================================================
# Purpose:
# Defines the GoogleNewsAgent that uses the Google News MCP server
# to fetch and analyze news for flight demand forecasting.
# =============================================================================

import logging
import asyncio
import uuid
from datetime import datetime
from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.sessions import InMemorySessionService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.artifacts import InMemoryArtifactService
from google.adk.runners import Runner
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.function_tool import FunctionTool
from google.genai import types

from utilities.mcp.mcp_connect import MCPConnector
from utilities.a2a.agent_discovery import DiscoveryClient
from utilities.a2a.agent_connect import AgentConnector
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class GoogleNewsAgent:
    """
    Google News Agent that searches and analyzes news for flight demand insights.
    Uses the Google News MCP server via SerpAPI.
    """
    
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]
    
    def __init__(self):
        """Initialize the Google News Agent with MCP tools and A2A capabilities."""
        # Load MCP tools
        self.mcp = MCPConnector()
        mcp_tools = self.mcp.get_tools()
        
        # Find Google News tools
        self.news_tools = []
        for tool in mcp_tools:
            # Google News server provides 'google_news_search' tool
            if tool.name == "google_news_search":
                self.news_tools.append(tool)
                logger.info(f"Loaded Google News tool: {tool.name}")
        
        # Initialize A2A discovery for agent collaboration
        self.discovery = DiscoveryClient()
        self.agent_connectors = {}
        self._discover_peer_agents()
        
        self._agent = self._build_agent()
        self._user_id = "google_news_user"
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )


    def _discover_peer_agents(self):
        """Discover other agents for collaboration."""
        try:
            agent_cards = asyncio.run(self.discovery.list_agent_cards())
            
            # Connect to specific agents we want to collaborate with
            for card in agent_cards:
                if card.name == "EconomicIndicatorsAgent":
                    self.agent_connectors[card.name] = AgentConnector(card.name, card.url)
                    logger.info(f"[A2A] Connected to {card.name} for collaboration")
        except Exception as e:
            logger.warning(f"[A2A] Failed to discover peer agents: {e}")
            # Continue without peer agents - we can still function independently
    
    async def _get_economic_context(self, context: str) -> str:
        """Get economic analysis from EconomicIndicatorsAgent."""
        if "EconomicIndicatorsAgent" not in self.agent_connectors:
            return "Economic analysis unavailable - agent not connected"
        
        try:
            # Ask economic agent for United-specific analysis
            task = await self.agent_connectors["EconomicIndicatorsAgent"].send_task(
                f"Analyze economic factors for United Airlines flight demand based on: {context}",
                session_id=str(uuid.uuid4())
            )
            
            if task.history and len(task.history) > 1:
                return task.history[-1].parts[0].text
            return "No economic data available"
        except Exception as e:
            logger.error(f"[A2A] Failed to get economic context: {e}")
            return f"Economic analysis error: {str(e)}"
    
    def _build_agent(self) -> LlmAgent:
        """Build the Gemini LLM agent with Google News tools."""
        tools = []
        
        # Add MCP Google News tools
        for mcp_tool in self.news_tools:
            # Create a wrapper factory to avoid closure issues
            def create_tool_wrapper(tool):
                async def wrapper(**kwargs) -> str:
                    """Execute Google News tool."""
                    # Ensure we have a query parameter for Google News
                    if tool.name == "google_news_search" and not kwargs.get('q'):
                        kwargs['q'] = "news today"  # Default query
                    
                    result = await tool.run(kwargs)
                    # Handle the MCP response format
                    if isinstance(result, list):
                        # If result is already a list of content items
                        return "\n".join([item.text if hasattr(item, 'text') else str(item) for item in result])
                    elif hasattr(result, 'content') and isinstance(result.content, list):
                        # If result has content attribute with list of items
                        return "\n".join([item.text if hasattr(item, 'text') else str(item) for item in result.content])
                    elif hasattr(result, 'text'):
                        # If result has text attribute directly
                        return result.text
                    else:
                        # Fallback to string representation
                        return str(result)
                return wrapper
            
            # Create the wrapper for this specific tool
            tool_wrapper = create_tool_wrapper(mcp_tool)
            tool_wrapper.__name__ = mcp_tool.name
            tool_wrapper.__doc__ = mcp_tool.description or f"Google News tool: {mcp_tool.name}"
            
            # Wrap as FunctionTool
            tools.append(FunctionTool(tool_wrapper))
        
        # Add economic context tool for agent collaboration
        async def get_economic_analysis(news_context: str) -> str:
            """Get economic analysis for news events from EconomicIndicatorsAgent."""
            return await self._get_economic_context(news_context)
        
        tools.append(FunctionTool(get_economic_analysis))
        
        return LlmAgent(
            model="gemini-2.5-flash",
            name="google_news_agent",
            description="Searches and analyzes Google News for United Airlines flight demand insights",
            instruction=self._system_instruction,
            tools=tools,
        )

    def _system_instruction(self, context: ReadonlyContext) -> str:
        """Generate system instructions for the Google News Agent."""
        today = datetime.now().strftime("%Y-%m-%d")
        
        return f"""You are a specialized Google News analyst for UNITED AIRLINES flight demand prediction.
Today's date is {today}. Your mission is to identify news events that specifically impact United's route network and demand.

UNITED AIRLINES FOCUS AREAS:
- Major hubs: Chicago (ORD), Denver (DEN), Houston (IAH), Newark (EWR), San Francisco (SFO), Washington (IAD), Los Angeles (LAX)
- Key international routes: Trans-Pacific (especially to Tokyo, Hong Kong, Singapore)
- Trans-Atlantic routes (London, Frankfurt, Munich)
- Latin America connections (Mexico City, São Paulo, Buenos Aires)

NEWS ANALYSIS FOR UNITED DEMAND:

1. HUB-SPECIFIC EVENTS:
   - Chicago conventions/trade shows → ORD business travel
   - Denver ski season/weather → DEN leisure patterns  
   - Houston energy conferences → IAH oil industry travel
   - San Francisco tech events → SFO business demand
   - Newark/DC political events → EWR/IAD government travel

2. COMPETITIVE LANDSCAPE:
   - Other airline issues (Southwest, American, Delta) → United opportunity
   - New route announcements by competitors → Market share impact
   - Alliance changes (Star Alliance news) → Network effects
   - Low-cost carrier expansions → Price pressure on United routes

3. UNITED-SPECIFIC NEWS:
   - Fleet changes (737 MAX, 787 Dreamliner deliveries)
   - Route announcements or cancellations
   - Labor negotiations or strikes
   - MileagePlus program changes
   - Partnerships (codeshares, joint ventures)

4. DEMAND DRIVERS FOR UNITED:
   - Business travel recovery in tech/finance sectors
   - International travel restrictions affecting United's Pacific routes
   - Fuel prices impacting United's long-haul profitability
   - Corporate travel policy changes at major United clients

5. ROUTE-SPECIFIC ANALYSIS:
   - Asia-Pacific: Tech conferences, trade tensions, COVID policies
   - Europe: EU regulations, business travel, tourism seasons
   - Latin America: Economic conditions, visa changes, festivals
   - Domestic: Weather patterns at hubs, regional events

ANALYSIS APPROACH:
1. Search for United-specific news first
2. Analyze competitor and industry news for indirect impacts
3. Check events at United hub cities
4. Monitor international developments on key United routes
5. Get economic context using get_economic_analysis() for major findings

AVAILABLE TOOLS:
- google_news_search: Search news (ALWAYS include 'q' parameter)
- get_economic_analysis: Get economic impact analysis from EconomicIndicatorsAgent

QUANTITATIVE OUTPUT REQUIREMENTS:
- Always lead with specific numbers: 'Found 23 relevant articles', '5 major events'
- Show impact percentages: 'Expected +12% demand increase', '-8% capacity impact'
- Include event sizes: '50,000 attendees', '3-day festival', '15 concurrent events'
- Specify affected flights: 'Impacts 47 daily United departures from ORD'
- Add time metrics: 'Published 3 hours ago', 'Event in 14 days', 'Trend over 30 days'
- Calculate demand scores: 'Demand impact score: 8.5/10', 'Urgency: High (9/10)'
- Provide coverage stats: 'Mentioned in 12 news sources', '85% positive sentiment'
- Include competitive metrics: 'United has 35% market share on affected routes'
- Show historical comparisons: 'Similar event last year drove +18% bookings'
- Quantify revenue impacts: 'Estimated $2.3M additional revenue opportunity'

OUTPUT FORMAT:
For each news item:
- Headline and date
- Impact on United specifically (not generic airline impact)
- Affected routes/hubs
- Demand impact: High/Medium/Low with percentage
- Timeframe: Immediate (0-7 days), Short-term (1-4 weeks), Long-term (1-6 months)
- Recommended United action with quantified benefit

Remember: Every analysis must tie back to UNITED AIRLINES demand, not generic airline industry trends."""


    async def invoke(self, query: str, session_id: str) -> str:
        """
        Process a query using the Google News Agent.
        
        Args:
            query: User query about news or events
            session_id: Session identifier
            
        Returns:
            Agent's response with news analysis
        """
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

        # Create user message
        content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=query)]
        )

        # Run the agent
        last_event = None
        async for event in self._runner.run_async(
            user_id=self._user_id,
            session_id=session.id,
            new_message=content
        ):
            last_event = event

        # Extract response
        if not last_event or not last_event.content or not last_event.content.parts:
            return "No news analysis available."

        return "\n".join([p.text for p in last_event.content.parts if p.text])