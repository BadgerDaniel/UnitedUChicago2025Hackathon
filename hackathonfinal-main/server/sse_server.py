# =============================================================================
# sse_server.py - Enhanced A2A Server with SSE Support
# =============================================================================

from starlette.applications import Starlette
from starlette.responses import JSONResponse, StreamingResponse
from starlette.requests import Request
from starlette.middleware.cors import CORSMiddleware
import asyncio
import json
import logging
from datetime import datetime
from typing import AsyncGenerator
import uuid

from models.agent import AgentCard
from models.request import A2ARequest, SendTaskRequest
from models.json_rpc import JSONRPCResponse, InternalError
from server import task_manager
from fastapi.encoders import jsonable_encoder

logger = logging.getLogger(__name__)

def json_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

class SSEServer:
    def __init__(self, host="0.0.0.0", port=5000, agent_card: AgentCard = None, task_manager: task_manager = None):
        self.host = host
        self.port = port
        self.agent_card = agent_card
        self.task_manager = task_manager
        self.app = Starlette()
        
        # Add CORS middleware for SSE
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Regular routes
        self.app.add_route("/", self._handle_request, methods=["POST"])
        self.app.add_route("/.well-known/agent.json", self._get_agent_card, methods=["GET"])
        
        # SSE streaming route
        self.app.add_route("/stream", self._handle_stream_request, methods=["POST"])
        
        # Store active streams
        self.active_streams = {}

    def start(self):
        if not self.agent_card or not self.task_manager:
            raise ValueError("Agent card and task manager are required")
        import uvicorn
        uvicorn.run(self.app, host=self.host, port=self.port)

    def _get_agent_card(self, request: Request) -> JSONResponse:
        response_data = jsonable_encoder(self.agent_card.model_dump())
        return JSONResponse(response_data)

    async def _handle_request(self, request: Request):
        """Standard JSON-RPC handler (non-streaming)"""
        try:
            data = await request.json()
            a2a_request = A2ARequest(**data)
            send_task_request = SendTaskRequest(**a2a_request.params)
            
            response = await self.task_manager.handle_send_task(send_task_request)
            json_response = JSONRPCResponse(
                id=a2a_request.id,
                result=jsonable_encoder(response.model_dump())
            )
            
            return JSONResponse(
                jsonable_encoder(json_response.model_dump()),
                headers={"Access-Control-Allow-Origin": "*"}
            )
        except Exception as e:
            logger.error(f"Task handling error: {e}")
            error_response = JSONRPCResponse(
                id=a2a_request.id if 'a2a_request' in locals() else None,
                error=InternalError(message=str(e))
            )
            return JSONResponse(
                jsonable_encoder(error_response.model_dump()),
                status_code=500,
                headers={"Access-Control-Allow-Origin": "*"}
            )

    async def _handle_stream_request(self, request: Request):
        """SSE streaming handler"""
        try:
            data = await request.json()
            a2a_request = A2ARequest(**data)
            send_task_request = SendTaskRequest(**a2a_request.params)
            
            # Create a unique stream ID
            stream_id = str(uuid.uuid4())
            
            async def event_generator() -> AsyncGenerator[str, None]:
                try:
                    # Send initial thinking message
                    yield self._format_sse({
                        "type": "thinking",
                        "agent": "orchestrator",
                        "content": "Processing your request..."
                    })
                    
                    # Check if task_manager has streaming support
                    if hasattr(self.task_manager, 'handle_send_task_streaming'):
                        # Stream responses from task manager
                        async for event in self.task_manager.handle_send_task_streaming(send_task_request):
                            yield self._format_sse(event)
                    else:
                        # Fallback: simulate streaming with status updates
                        yield self._format_sse({
                            "type": "status",
                            "agent": "orchestrator",
                            "content": "Routing to appropriate agent..."
                        })
                        
                        # Get the actual response
                        response = await self.task_manager.handle_send_task(send_task_request)
                        
                        # Send final response
                        yield self._format_sse({
                            "type": "complete",
                            "agent": response.history[-1].agent if response.history else "orchestrator",
                            "content": response.history[-1].parts[0].text if response.history else "No response",
                            "result": jsonable_encoder(response.model_dump())
                        })
                    
                    # Send done signal
                    yield self._format_sse({"type": "done"})
                    
                except Exception as e:
                    logger.error(f"Streaming error: {e}")
                    yield self._format_sse({
                        "type": "error",
                        "content": str(e)
                    })
            
            return StreamingResponse(
                event_generator(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                }
            )
            
        except Exception as e:
            logger.error(f"Stream request error: {e}")
            return JSONResponse(
                {"error": str(e)},
                status_code=500,
                headers={"Access-Control-Allow-Origin": "*"}
            )
    
    def _format_sse(self, data: dict) -> str:
        """Format data as SSE message"""
        return f"data: {json.dumps(data)}\n\n"