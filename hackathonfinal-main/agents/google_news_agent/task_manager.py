# =============================================================================
# agents/google_news_agent/task_manager.py
# =============================================================================
# Purpose:
# TaskManager for the Google News Agent that handles JSON-RPC requests.
# =============================================================================

import logging
from server.task_manager import InMemoryTaskManager
from models.request import SendTaskRequest, SendTaskResponse
from models.task import Message, TaskStatus, TaskState, TextPart
from agents.google_news_agent.agent import GoogleNewsAgent

logger = logging.getLogger(__name__)


class GoogleNewsTaskManager(InMemoryTaskManager):
    """
    Task manager for Google News Agent that processes news search requests.
    """
    
    def __init__(self, agent: GoogleNewsAgent):
        """
        Initialize the task manager with a Google News agent.
        
        Args:
            agent: GoogleNewsAgent instance
        """
        super().__init__()
        self.agent = agent
        
    def _get_user_text(self, request: SendTaskRequest) -> str:
        """
        Extract user text from the request.
        
        Args:
            request: Incoming task request
            
        Returns:
            User text message
        """
        return request.params.message.parts[0].text
    
    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        """
        Handle incoming task requests for news analysis.
        
        Args:
            request: Task request with news query
            
        Returns:
            Response with news analysis
        """
        logger.info(f"GoogleNewsTaskManager received task {request.params.id}")
        
        # Store the task
        task = await self.upsert_task(request.params)
        
        # Extract query and process with agent
        user_text = self._get_user_text(request)
        
        try:
            # Get news analysis from the agent
            analysis = await self.agent.invoke(user_text, request.params.sessionId)
            
            # Create response message
            msg = Message(
                role="agent",
                parts=[TextPart(text=analysis)]
            )
            
            # Update task status
            async with self.lock:
                task.status = TaskStatus(state=TaskState.COMPLETED)
                task.history.append(msg)
                
        except Exception as e:
            logger.error(f"Error processing news request: {str(e)}")
            error_msg = Message(
                role="agent",
                parts=[TextPart(text=f"Error analyzing news: {str(e)}")]
            )
            async with self.lock:
                task.status = TaskStatus(state=TaskState.FAILED)
                task.history.append(error_msg)
        
        # Return the response
        return SendTaskResponse(id=request.id, result=task)