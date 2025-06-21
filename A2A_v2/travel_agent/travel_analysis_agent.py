"""
Streamlined Travel Analysis Agent - Core A2A agent for travel analysis.
Integrates with MCP tools to provide weather, event, and flight correlation analysis.
"""

import logging
from collections.abc import AsyncIterable
from typing import Any, Literal

from langchain_core.runnables.config import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel
from langchain_mcp_adapters.client import MultiServerMCPClient

logger = logging.getLogger(__name__)
memory = MemorySaver()

class ResponseFormat(BaseModel):
    """Response format for A2A compatibility."""
    status: Literal['input_required', 'completed', 'error'] = 'input_required'
    message: str

class TravelAnalysisAgent:
    """
    Main travel analysis agent that provides multi-factor correlation analysis.
    
    Core Features:
    - Weather impact analysis
    - Event impact analysis  
    - Flight pricing analysis
    - Cross-correlation between all factors
    """
    
    SYSTEM_INSTRUCTION = (
        'You are a specialized travel analysis assistant that analyzes correlations between '
        'weather conditions, major events, and flight pricing patterns. '
        'Your core capabilities include:'
        '\n'
        '• Weather Impact Analysis: How weather affects travel and flight operations'
        '• Event Impact Analysis: How major events drive demand and pricing'
        '• Flight Pricing Analysis: Current pricing trends and factors'
        '• Cross-Correlation Analysis: How multiple factors combine to affect travel costs'
        '\n'
        'Use the available MCP tools to gather comprehensive data, then provide insights about '
        'how different factors correlate and affect travel planning and pricing. '
        'Always use the analyze_travel_correlation tool for complex multi-factor queries.'
        '\n'
        'Focus on providing actionable insights and clear explanations of correlation patterns.'
    )

    RESPONSE_FORMAT_INSTRUCTION: str = (
        'Select status as completed if you have provided a comprehensive analysis with clear insights. '
        'Select status as input_required if you need more specific information from the user. '
        'Set response status to error if there was an error in the analysis.'
    )

    def __init__(self):
        self.model = ChatOpenAI(model="gpt-4o", temperature=0.3)
        self.graph = None
        
    async def invoke(self, query: str, sessionId: str) -> dict[str, Any]:
        """Process travel analysis queries using MCP tools and AI reasoning."""
        try:
            async with MultiServerMCPClient({
                "travel": {
                    "url": "http://localhost:8000/sse",
                    "transport": "sse",
                }
            }) as client:
                # Get tools and create the agent - get_tools() is not async
                tools = client.get_tools()
                self.graph = create_react_agent(
                    self.model,
                    tools,
                    checkpointer=memory,
                    system_prompt=self.SYSTEM_INSTRUCTION,
                    response_format=(self.RESPONSE_FORMAT_INSTRUCTION, ResponseFormat),
                    debug=True
                )
                config: RunnableConfig = {'configurable': {'thread_id': sessionId}}
                await self.graph.ainvoke({'messages': [('user', query)]}, config)
                return self.get_agent_response(config)
                
        except Exception as e:
            logger.error(f"Error processing travel query: {e}")
            return {
                'is_task_complete': False,
                'require_user_input': True,
                'content': f'I encountered an error analyzing your travel query: {str(e)}. Please try rephrasing your question or provide more specific details about cities and dates.'
            }

    async def stream(self, query: str, sessionId: str) -> AsyncIterable[dict[str, Any]]:
        """Stream responses for long-running analyses."""
        # For now, just return the complete result
        # In the future, this could stream incremental analysis steps
        result = await self.invoke(query, sessionId)
        yield result

    def get_agent_response(self, config: RunnableConfig) -> dict[str, Any]:
        """Extract and format the agent's response for A2A compatibility."""
        current_state = self.graph.get_state(config)
        structured_response = current_state.values.get('structured_response')
        
        if structured_response and isinstance(structured_response, ResponseFormat):
            if structured_response.status in {'input_required', 'error'}:
                return {
                    'is_task_complete': False,
                    'require_user_input': True,
                    'content': structured_response.message,
                }
            if structured_response.status == 'completed':
                return {
                    'is_task_complete': True,
                    'require_user_input': False,
                    'content': structured_response.message,
                }

        # Default response if structured response is not available
        return {
            'is_task_complete': False,
            'require_user_input': True,
            'content': (
                'I can help you analyze travel factors including weather, events, and flight pricing correlations. '
                'Please provide specific cities, dates, and what type of analysis you need. '
                'For example: "Why are flights from NYC to Chicago expensive on July 15th?" or '
                '"How do weather and events affect Miami travel costs?"'
            ),
        }

    # A2A compatibility
    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']
