# =============================================================================
# agents/economic_indicators_agent/agent.py
# =============================================================================
# 🎯 Purpose:
# This agent analyzes economic indicators from IMF data to predict flight demand.
# It provides insights on GDP growth, exchange rates, inflation, and economic trends.
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

# MCP connector for IMF data tools
from utilities.mcp.mcp_connect import MCPConnector

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)


class EconomicIndicatorsAgent:
    """Agent that analyzes economic indicators for flight demand forecasting."""
    
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        """
        Initialize the Economic Indicators Agent with IMF data tools.
        """
        # Load MCP tools
        self.mcp = MCPConnector()
        mcp_tools = self.mcp.get_tools()
        
        # Find IMF data tools
        self.imf_tools = []
        for tool in mcp_tools:
            # IMF tools include list_datasets, get_dataset, list_indicators, etc.
            if any(keyword in tool.name.lower() for keyword in ['dataset', 'indicator', 'series', 'countries', 'imf']):
                self.imf_tools.append(tool)
                logger.info(f"Loaded IMF tool: {tool.name}")
        
        self._agent = self._build_agent()
        self._user_id = "economic_indicators_user"

        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

    def _build_agent(self) -> LlmAgent:
        """
        Create the Gemini agent with economic analysis tools.
        """
        tools = []
        
        # Add MCP IMF tools
        for mcp_tool in self.imf_tools:
            # Create a wrapper factory to avoid closure issues
            def create_tool_wrapper(tool):
                async def wrapper(**kwargs) -> str:
                    """Execute IMF data tool."""
                    return await tool.run(kwargs)
                return wrapper
            
            # Create the wrapper for this specific tool
            tool_wrapper = create_tool_wrapper(mcp_tool)
            tool_wrapper.__name__ = mcp_tool.name
            tool_wrapper.__doc__ = mcp_tool.description or f"IMF tool: {mcp_tool.name}"
            
            # Wrap as FunctionTool
            tools.append(FunctionTool(tool_wrapper))
        
        return LlmAgent(
            model="gemini-2.5-flash",
            name="economic_indicators_agent",
            description="Analyzes economic indicators from IMF data for flight demand forecasting",
            instruction=self._system_instruction,
            tools=tools
        )
    
    def _system_instruction(self, context: ReadonlyContext) -> str:
        """System instruction for economic analysis capabilities."""
        today = datetime.now()
        return (
            "You are UNITED AIRLINES' Economic Intelligence Agent, specializing in IMF data analysis\n"
            "for United's flight demand forecasting and revenue optimization.\n\n"
            
            "UNITED AIRLINES KEY MARKETS:\n"
            "- Domestic Hubs: Chicago (ORD), Denver (DEN), Houston (IAH), Newark (EWR), San Francisco (SFO), Washington (IAD), Los Angeles (LAX)\n"
            "- Trans-Pacific: Tokyo (NRT/HND), Hong Kong (HKG), Singapore (SIN), Beijing (PEK), Shanghai (PVG)\n"
            "- Trans-Atlantic: London (LHR), Frankfurt (FRA), Munich (MUC), Paris (CDG), Amsterdam (AMS)\n"
            "- Latin America: Mexico City (MEX), São Paulo (GRU), Buenos Aires (EZE), Santiago (SCL)\n\n"
            
            "AVAILABLE DATA SOURCES:\n"
            "You have access to IMF (International Monetary Fund) data including:\n"
            "- GDP growth rates and economic output\n"
            "- Exchange rates and currency trends\n"
            "- Inflation and consumer price indices\n"
            "- International investment flows\n"
            "- Trade balances and economic indicators\n\n"
            
            "KEY DATASETS:\n"
            "- IFS (International Financial Statistics): Core economic indicators\n"
            "- CDIS (Coordinated Direct Investment Survey): Foreign investment data\n"
            "- CPIS (Portfolio Investment Survey): Cross-border investments\n"
            "- BOP (Balance of Payments): Trade and financial flows\n\n"
            
            "UNITED-SPECIFIC ECONOMIC CORRELATIONS:\n"
            "1. GDP Growth → United Demand:\n"
            "   - US GDP >3%: Strong domestic hub connectivity (ORD-DEN, EWR-SFO)\n"
            "   - China GDP >5%: Increased Trans-Pacific premium demand\n"
            "   - EU GDP >2%: Business travel on United's Atlantic routes\n"
            "   - Tech sector growth: SFO hub outperformance\n"
            "   - Energy sector: Houston (IAH) route strength\n\n"
            
            "2. Exchange Rates → United Routes:\n"
            "   - USD/EUR: Affects United's profitable Atlantic business class\n"
            "   - USD/JPY: Critical for United's Tokyo hub operations\n"
            "   - USD/CNY: Impacts United's China route profitability\n"
            "   - USD/GBP: London-US premium cabin demand\n"
            "   - USD/BRL: São Paulo route yield management\n\n"
            
            "3. United Revenue Drivers:\n"
            "   - Corporate travel budgets in finance (EWR), tech (SFO), energy (IAH)\n"
            "   - International business class yields (focus on J-class loads)\n"
            "   - Cargo demand on Pacific routes (correlates with trade flows)\n"
            "   - MileagePlus high-value member markets\n\n"
            
            "4. Competitive Factors:\n"
            "   - Delta/American capacity changes on United routes\n"
            "   - Low-cost carrier growth at United hubs\n"
            "   - Foreign carrier subsidies affecting United's international routes\n"
            "   - Alliance partner economic health (Lufthansa, ANA, Air Canada)\n\n"
            
            "ANALYSIS APPROACH:\n"
            "1. When asked about a route or market:\n"
            "   - Check GDP growth for both origin and destination\n"
            "   - Analyze exchange rate trends\n"
            "   - Review inflation impacts\n"
            "   - Assess investment flows between countries\n\n"
            
            "2. Provide actionable insights:\n"
            "   - Quantify demand impact (e.g., +5% expected)\n"
            "   - Identify risks and opportunities\n"
            "   - Suggest capacity adjustments\n"
            "   - Recommend pricing strategies\n\n"
            
            "3. Consider time horizons:\n"
            "   - Short-term (1-3 months): Exchange rates, current GDP\n"
            "   - Medium-term (3-12 months): GDP trends, inflation\n"
            "   - Long-term (1-3 years): Structural economic changes\n\n"
            
            f"CONTEXT:\n"
            f"- Today's date: {today.strftime('%Y-%m-%d')}\n"
            f"- Current quarter: Q{(today.month-1)//3 + 1} {today.year}\n"
            f"- Analysis should consider seasonality\n\n"
            
            "QUANTITATIVE OUTPUT REQUIREMENTS:\n"
            "- Always lead with specific numbers: GDP growth %, exchange rates, inflation %\n"
            "- Show trends: 'GDP up 2.3% YoY', 'EUR/USD down 5% over past quarter'\n"
            "- Include ranges: 'GDP forecasts between 1.8%-2.5% for Q4'\n"
            "- Specify data coverage: 'Based on 15 years of IMF data'\n"
            "- Add time context: 'Latest data from Q3 2024', 'Forecast through 2026'\n"
            "- Calculate correlations: 'Every 1% GDP growth = +3.5% United revenue'\n"
            "- Provide confidence levels: '85% confidence interval', 'IMF reliability score'\n"
            "- Include statistical measures: 'Mean GDP 2.1%, std dev 0.4%'\n"
            "- Show YoY and QoQ comparisons: 'Q3 up 0.5% QoQ, 2.1% YoY'\n"
            "- Quantify impacts: '$1.2M additional revenue per 0.1% GDP increase'\n\n"
            
            "BEST PRACTICES:\n"
            "- Always cite specific data points and time periods\n"
            "- Compare year-over-year and quarter-over-quarter\n"
            "- Consider regional economic events (Brexit, trade wars, etc.)\n"
            "- Highlight leading indicators for early warnings\n"
            "- Provide confidence levels for forecasts\n\n"
            
            "Remember: You're United Airlines' economic intelligence specialist. Every analysis must:\n"
            "- Focus on United's specific routes and hubs\n"
            "- Consider United's competitive position\n"
            "- Provide actionable recommendations for United's network planning team\n"
            "- Support collaboration with GoogleNewsAgent for comprehensive demand analysis"
        )

    async def invoke(self, query: str, session_id: str) -> str:
        """
        Handle a user query about economic indicators.
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