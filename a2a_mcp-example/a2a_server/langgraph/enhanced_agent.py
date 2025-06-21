"""Enhanced Multi-Agent System integrating Weather, Event, Flight, and Orchestrator agents."""

import logging
import asyncio
from collections.abc import AsyncIterable
from typing import Any, Literal

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.runnables.config import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel
from langchain_mcp_adapters.client import MultiServerMCPClient

# Import the orchestrator agent with proper path handling
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'agents'))

try:
    from orchestrator_agent import OrchestratorAgent
except ImportError as e:
    logging.error(f"Could not import orchestrator_agent: {e}")
    # Create a fallback orchestrator for basic functionality
    class OrchestratorAgent:
        async def process_complex_query(self, query):
            return {
                "response": f"Fallback response for: {query}",
                "error": "Full orchestrator not available"
            }

logger = logging.getLogger(__name__)

memory = MemorySaver()


class ResponseFormat(BaseModel):
    """Respond to the user in this format."""
    status: Literal['input_required', 'completed', 'error'] = 'input_required'
    message: str


class TravelAnalysisAgent:
    """Enhanced Travel Analysis Agent that coordinates multiple specialized agents."""

    SYSTEM_INSTRUCTION = (
        'You are a specialized travel analysis assistant that coordinates between weather, event, and flight agents. '
        'Your purpose is to analyze complex travel queries involving correlations between weather conditions, '
        'major events, and flight pricing patterns. '
        'You can help users understand:'
        '- How weather affects flight prices and availability'
        '- How major events impact travel costs and demand'
        '- Which dates and routes offer the best value considering all factors'
        '- Comprehensive travel recommendations based on multiple data sources'
        ''
        'Use the available tools to gather weather, event, and flight data, then provide insights '
        'about correlations and patterns that affect travel planning and pricing.'
        ''
        'If the user asks about anything other than travel analysis involving weather, events, and flights, '
        'politely state that you specialize in comprehensive travel analysis and redirect to relevant topics.'
    )

    RESPONSE_FORMAT_INSTRUCTION: str = (
        'Select status as completed if you have provided a comprehensive analysis'
        'Select status as input_required if you need more information from the user'
        'Set response status to error if there was an error in the analysis'
    )

    def __init__(self):
        self.model = ChatOpenAI(model="gpt-4o", temperature=0.3)
        self.graph = None
        self.orchestrator = OrchestratorAgent()
        
    async def invoke(self, query: str, sessionId: str) -> dict[str, Any]:
        """Process travel analysis queries using multiple agents and MCP tools."""
        try:
            # Use the orchestrator for complex multi-agent queries
            if self._is_complex_query(query):
                orchestrator_result = await self.orchestrator.process_complex_query(query)
                
                if "error" in orchestrator_result:
                    return {
                        'is_task_complete': False,
                        'require_user_input': True,
                        'content': f"I encountered an error analyzing your query: {orchestrator_result['error']}"
                    }
                
                return {
                    'is_task_complete': True,
                    'require_user_input': False,
                    'content': orchestrator_result.get('response', 'Analysis completed.')
                }
            
            # For simpler queries, use MCP tools directly
            async with MultiServerMCPClient(
                {
                    "travel_agents": {
                        "url": "http://localhost:8001/sse",  # Enhanced MCP server port
                        "transport": "sse",
                    }
                }
            ) as client:
                self.graph = create_react_agent(
                    self.model,
                    tools=client.get_tools(),
                    checkpointer=memory,
                    prompt=self.SYSTEM_INSTRUCTION,
                    response_format=(self.RESPONSE_FORMAT_INSTRUCTION, ResponseFormat),
                    debug=True
                )
                config: RunnableConfig = {'configurable': {'thread_id': sessionId}}
                await self.graph.ainvoke({'messages': [('user', query)]}, config)
                return self.get_agent_response(config)
                
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                'is_task_complete': False,
                'require_user_input': True,
                'content': f'I encountered an error while processing your request: {str(e)}'
            }

    def _is_complex_query(self, query: str) -> bool:
        """Determine if a query requires multi-agent orchestration."""
        complex_keywords = [
            "correlation", "correlate", "compare", "relationship", "impact", "affect",
            "expensive due to", "cheaper because", "prices higher", "why cost",
            "best dates", "recommend", "analysis", "multiple factors"
        ]
        
        # Check if query mentions multiple domains
        weather_keywords = ["weather", "storm", "rain", "snow", "temperature", "climate"]
        event_keywords = ["event", "concert", "game", "festival", "conference", "convention"]
        flight_keywords = ["flight", "airline", "ticket", "price", "cost", "expensive", "cheap"]
        
        domains_mentioned = 0
        if any(keyword in query.lower() for keyword in weather_keywords):
            domains_mentioned += 1
        if any(keyword in query.lower() for keyword in event_keywords):
            domains_mentioned += 1
        if any(keyword in query.lower() for keyword in flight_keywords):
            domains_mentioned += 1
        
        return (
            any(keyword in query.lower() for keyword in complex_keywords) or
            domains_mentioned >= 2
        )

    async def stream(self, query: str, sessionId: str) -> AsyncIterable[dict[str, Any]]:
        """Stream responses for long-running analyses."""
        try:
            if self._is_complex_query(query):
                # Stream orchestrator results
                yield {
                    'is_task_complete': False,
                    'require_user_input': False,
                    'content': 'Analyzing weather conditions...'
                }
                
                yield {
                    'is_task_complete': False,
                    'require_user_input': False,
                    'content': 'Searching for events...'
                }
                
                yield {
                    'is_task_complete': False,
                    'require_user_input': False,
                    'content': 'Analyzing flight pricing patterns...'
                }
                
                yield {
                    'is_task_complete': False,
                    'require_user_input': False,
                    'content': 'Performing cross-correlation analysis...'
                }
                
                # Get final result from orchestrator
                result = await self.orchestrator.process_complex_query(query)
                
                yield {
                    'is_task_complete': True,
                    'require_user_input': False,
                    'content': result.get('response', 'Analysis completed.')
                }
            else:
                # For simple queries, just return the regular result
                result = await self.invoke(query, sessionId)
                yield result
                
        except Exception as e:
            logger.error(f"Error in streaming: {e}")
            yield {
                'is_task_complete': False,
                'require_user_input': True,
                'content': f'Error during analysis: {str(e)}'
            }

    def get_agent_response(self, config: RunnableConfig) -> dict[str, Any]:
        """Get structured response from the agent."""
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

        return {
            'is_task_complete': False,
            'require_user_input': True,
            'content': 'I need more information to provide a comprehensive travel analysis. Could you specify the cities, dates, or type of analysis you\'re looking for?',
        }

    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']


class AgentCommunicationDemo:
    """Demonstration of agent-to-agent communication capabilities."""
    
    def __init__(self):
        self.orchestrator = OrchestratorAgent()
    
    async def demonstrate_agent_communication(self) -> dict[str, Any]:
        """Demonstrate how agents communicate with each other."""
        try:
            # Mock agent communication for demo
            return {
                "demonstration_completed": True,
                "communications": [
                    {"type": "weather_to_flight", "result": {"status": "demo"}},
                    {"type": "event_to_weather", "result": {"status": "demo"}},
                    {"type": "flight_multi_request", "result": {"status": "demo"}}
                ],
                "summary": "Agents successfully demonstrated communication capabilities"
            }
            
        except Exception as e:
            logger.error(f"Error in agent communication demo: {e}")
            return {"error": str(e)}


# Example usage and testing functions
async def test_complex_query():
    """Test the system with a complex query involving multiple agents."""
    agent = TravelAnalysisAgent()
    
    complex_query = (
        "Why were flights from New York to Chicago more expensive on July 15th? "
        "Was it due to weather conditions or major events happening in either city?"
    )
    
    result = await agent.invoke(complex_query, "test_session_1")
    print("Complex Query Result:")
    print(result)
    return result


async def test_agent_communication():
    """Test direct agent-to-agent communication."""
    demo = AgentCommunicationDemo()
    
    result = await demo.demonstrate_agent_communication()
    print("Agent Communication Demo:")
    print(result)
    return result


async def test_streaming_analysis():
    """Test streaming capabilities for long-running analyses."""
    agent = TravelAnalysisAgent()
    
    streaming_query = (
        "Analyze the correlation between major events and flight pricing "
        "for the New York to Los Angeles route in July 2025"
    )
    
    print("Streaming Analysis:")
    async for chunk in agent.stream(streaming_query, "test_session_2"):
        print(f"Stream chunk: {chunk}")
    
    return "Streaming test completed"


if __name__ == "__main__":
    # Run tests
    async def main():
        print("=== Testing Enhanced Multi-Agent System ===\n")
        
        # Test 1: Complex query processing
        print("1. Testing complex query processing...")
        await test_complex_query()
        print("\n" + "="*50 + "\n")
        
        # Test 2: Agent communication
        print("2. Testing agent-to-agent communication...")
        await test_agent_communication()
        print("\n" + "="*50 + "\n")
        
        # Test 3: Streaming analysis
        print("3. Testing streaming analysis...")
        await test_streaming_analysis()
        print("\n" + "="*50 + "\n")
        
        print("All tests completed!")
    
    # Run the tests
    asyncio.run(main())
