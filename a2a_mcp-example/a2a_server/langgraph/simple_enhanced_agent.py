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
    status: Literal['input_required', 'completed', 'error'] = 'input_required'
    message: str

class SimpleTravelAnalysisAgent:
    SYSTEM_INSTRUCTION = (
        'You are a travel analysis assistant that uses weather, event, and flight data to help users. '
        'You can analyze how weather conditions and events affect flight pricing. '
        'Use the available tools to gather information and provide comprehensive travel insights.'
    )

    RESPONSE_FORMAT_INSTRUCTION: str = (
        'Select status as completed if you have provided a comprehensive analysis. '
        'Select status as input_required if you need more information from the user. '
        'Set response status to error if there was an error in the analysis.'
    )

    def __init__(self):
        self.model = ChatOpenAI(model="gpt-4o", temperature=0.3)
        self.graph = None
        
    async def invoke(self, query: str, sessionId: str) -> dict[str, Any]:
        try:
            async with MultiServerMCPClient({
                "travel": {
                    "url": "http://localhost:8000/sse",
                    "transport": "sse",
                }
            }) as client:
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
                'content': f'Error processing request: {str(e)}'
            }

    async def stream(self, query: str, sessionId: str) -> AsyncIterable[dict[str, Any]]:
        result = await self.invoke(query, sessionId)
        yield result

    def get_agent_response(self, config: RunnableConfig) -> dict[str, Any]:
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
            'content': 'Please specify cities, dates, or type of travel analysis you need.',
        }

    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']
