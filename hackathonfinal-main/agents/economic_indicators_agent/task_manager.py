# =============================================================================
# agents/economic_indicators_agent/task_manager.py
# =============================================================================
# 🎯 Purpose:
# Connects the Economic Indicators Agent to the task-handling system.
# =============================================================================

import logging

from server.task_manager import InMemoryTaskManager
from agents.economic_indicators_agent.agent import EconomicIndicatorsAgent
from models.request import SendTaskRequest, SendTaskResponse
from models.task import Message, Task, TextPart, TaskStatus, TaskState

logger = logging.getLogger(__name__)


class EconomicIndicatorsTaskManager(InMemoryTaskManager):
    """
    Task manager that connects the Economic Indicators Agent to the A2A system.
    """

    def __init__(self, agent: EconomicIndicatorsAgent):
        super().__init__()
        self.agent = agent

    def _get_user_query(self, request: SendTaskRequest) -> str:
        """Extract the user's text from the request."""
        return request.params.message.parts[0].text

    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        """
        Handle incoming economic analysis tasks.
        """
        logger.info(f"Processing economic indicators task: {request.params.id}")

        # Save the task
        task = await self.upsert_task(request.params)

        # Get the user's query
        query = self._get_user_query(request)

        # Ask the agent for economic analysis
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