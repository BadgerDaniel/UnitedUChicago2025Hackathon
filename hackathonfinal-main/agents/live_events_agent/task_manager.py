# =============================================================================
# agents/live_events_agent/task_manager.py
# =============================================================================
# 🎯 Purpose:
#   Task manager for the Live Events Agent, handling A2A protocol communication
# =============================================================================

import logging

# A2A infrastructure imports
from server.task_manager import InMemoryTaskManager
from models.request import SendTaskRequest, SendTaskResponse
from models.task import Message, TaskStatus, TaskState, TextPart

# Import our agent
from agents.live_events_agent.agent import LiveEventsAgent

# Create logger
logger = logging.getLogger(__name__)


class LiveEventsTaskManager(InMemoryTaskManager):
    """
    📋 Task Manager for Live Events Agent
    
    Handles incoming A2A requests and delegates them to the LiveEventsAgent
    for processing event queries and flight demand analysis.
    """
    
    def __init__(self, agent: LiveEventsAgent):
        """
        Initialize the task manager with a LiveEventsAgent instance.
        
        Args:
            agent (LiveEventsAgent): The agent that will handle queries
        """
        super().__init__()
        self.agent = agent
        
    def _get_user_text(self, request: SendTaskRequest) -> str:
        """
        Extract the user's text from the A2A request.
        
        Args:
            request (SendTaskRequest): The incoming request
            
        Returns:
            str: The extracted text content
        """
        return request.params.message.parts[0].text
    
    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        """
        Handle incoming task requests.
        
        Process:
        1. Store the task in memory
        2. Extract the user query
        3. Invoke the agent to analyze events
        4. Return the analysis as a response
        
        Args:
            request (SendTaskRequest): The A2A request
            
        Returns:
            SendTaskResponse: The agent's analysis
        """
        logger.info(f"LiveEventsTaskManager received task {request.params.id}")
        
        # Store the task
        task = await self.upsert_task(request.params)
        
        # Extract user text and get agent response
        user_text = self._get_user_text(request)
        
        try:
            # Invoke the agent
            reply_text = await self.agent.invoke(user_text, request.params.sessionId)
            
            # Wrap the reply in a Message
            msg = Message(
                role="agent",
                parts=[TextPart(text=reply_text)]
            )
            
            # Update task status
            async with self.lock:
                task.status = TaskStatus(state=TaskState.COMPLETED)
                task.history.append(msg)
                
        except Exception as e:
            logger.error(f"Error processing live events request: {e}")
            # Create error message
            error_text = f"I encountered an error while searching for events: {str(e)}"
            msg = Message(
                role="agent",
                parts=[TextPart(text=error_text)]
            )
            
            async with self.lock:
                task.status = TaskStatus(state=TaskState.FAILED)
                task.history.append(msg)
        
        # Return the response
        return SendTaskResponse(
            id=request.id,
            result=task
        )