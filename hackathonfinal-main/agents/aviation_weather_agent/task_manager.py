# =============================================================================
# agents/aviation_weather_agent/task_manager.py
# =============================================================================
# 🎯 Purpose:
# This file connects the AviationWeatherAgent to the task-handling system.
# =============================================================================

import logging

from server.task_manager import InMemoryTaskManager
from agents.aviation_weather_agent.agent import AviationWeatherAgent
from models.request import SendTaskRequest, SendTaskResponse
from models.task import Message, Task, TextPart, TaskStatus, TaskState

logger = logging.getLogger(__name__)


class AviationWeatherTaskManager(InMemoryTaskManager):
    """
    Task manager that connects the Aviation Weather Agent to the A2A system.
    """

    def __init__(self, agent: AviationWeatherAgent):
        super().__init__()
        self.agent = agent

    def _get_user_query(self, request: SendTaskRequest) -> str:
        """Extract the user's text from the request."""
        return request.params.message.parts[0].text

    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        """
        Handle incoming weather query tasks.
        """
        logger.info(f"Processing aviation weather task: {request.params.id}")

        # Save the task
        task = await self.upsert_task(request.params)

        # Get the user's query
        query = self._get_user_query(request)

        # Ask the agent for weather information
        result_text = await self.agent.invoke(query, request.params.sessionId)

        # Create agent's response message
        agent_message = Message(
            role="agent",
            parts=[TextPart(text=result_text)]
        )

        # Update task with response
        async with self.lock:
            task.status = TaskStatus(state=TaskState.COMPLETED)
            task.history.append(agent_message)

        return SendTaskResponse(id=request.id, result=task)