# =============================================================================
# agents/host_agent/orchestrator.py
# =============================================================================
# 🎯 Purpose:
# Defines the OrchestratorAgent, which:
#   1) Discovers and calls other A2A agents (via DiscoveryClient & AgentConnector)
#   2) Discovers and loads MCP tools (via MCPConnector)
#   3) Exposes each A2A action and each MCP tool as its own callable tool
# Also defines OrchestratorTaskManager to serve this agent over JSON-RPC.
# =============================================================================

import uuid                            # For generating unique session identifiers
import logging                         # For writing log messages to console or file
import asyncio                         # For running asynchronous tasks from synchronous code
from dotenv import load_dotenv         # To load environment variables from a .env file
import time                            # For tracking last discovery time
from typing import Optional            # For optional type hints
import threading                       # For background discovery task

# Load environment variables from .env (e.g., GOOGLE_API_KEY)
load_dotenv()

# -----------------------------------------------------------------------------
# Google ADK / Gemini imports: classes and functions to build and run LLM agents
# -----------------------------------------------------------------------------
from google.adk.agents.llm_agent import LlmAgent                # Main LLM agent class
from google.adk.sessions import InMemorySessionService          # Simple in-memory session storage
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService  # In-memory memory storage
from google.adk.artifacts import InMemoryArtifactService        # In-memory artifact storage (files, binaries)
from google.adk.runners import Runner                           # Coordinates LLM, sessions, memory, and tools
from google.adk.agents.readonly_context import ReadonlyContext  # Provides read-only context to system prompts
from google.adk.tools.tool_context import ToolContext           # Carries state between tool invocations
from google.adk.tools.function_tool import FunctionTool         # Wraps a Python function as a callable LLM tool
from google.genai import types                                 # For wrapping user messages into LLM-friendly format

# For date awareness
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# A2A infrastructure imports: task manager and message models for JSON-RPC
# -----------------------------------------------------------------------------
from server.task_manager import InMemoryTaskManager               # Base class for task storage and locking
from models.request import SendTaskRequest, SendTaskResponse      # JSON-RPC request/response models
from models.task import Message, TaskStatus, TaskState, TextPart   # Task, message, and status data models

# -----------------------------------------------------------------------------
# A2A discovery & connector imports: to find and call remote A2A agents
# -----------------------------------------------------------------------------
from utilities.a2a.agent_discovery import DiscoveryClient        # Finds agent URLs from registry file
from utilities.a2a.agent_connect import AgentConnector          # Sends tasks to remote A2A agents

# -----------------------------------------------------------------------------
# MCP connector import removed - agents handle their own MCP connections
# -----------------------------------------------------------------------------

# Import AgentCard model for typing
from models.agent import AgentCard                              # Metadata structure describing an agent

# -----------------------------------------------------------------------------
# Logging setup: configure root logger to show INFO and above
# -----------------------------------------------------------------------------
logger = logging.getLogger(__name__)                           # Create a logger for this module
logging.basicConfig(level=logging.INFO)                        # Show INFO-level logs in the console


class OrchestratorAgent:
    """
    🤖 OrchestratorAgent:
      - Discovers A2A agents via DiscoveryClient → list of AgentCards
      - Connects to each A2A agent with AgentConnector
      - Discovers MCP servers via MCPConnector and loads MCP tools
      - Exposes each A2A action and each MCP tool as its own callable tool
      - Routes user queries by picking and invoking the correct tool
    """
    
    # Specify supported MIME types for input/output (we only handle plain text)
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self, agent_cards: list[AgentCard], registry_file: Optional[str] = None):
        """
        Initialize the orchestrator with discovered A2A agents and MCP tools.

        Args:
            agent_cards (list[AgentCard]): Metadata for each A2A child agent.
            registry_file (Optional[str]): Path to agent registry file for re-discovery.
        """
        # Store registry file path for re-discovery
        self.registry_file = registry_file
        self.discovery_client = DiscoveryClient(registry_file=registry_file)
        self.last_discovery_time = time.time()
        self.discovery_lock = asyncio.Lock()
        self.failed_agents = set()  # Track agents that failed recently
        
        # 1) Build connectors for each A2A agent
        self.connectors = {}                                  # Dict mapping agent name → AgentConnector
        self.agent_urls = {}                                  # Dict mapping agent name → URL
        self._update_connectors(agent_cards)

        # 2) Build the Gemini LLM agent and its Runner
        self._agent = self._build_agent()                      # Assemble LlmAgent with tools
        self._user_id = "orchestrator_user"                   # Fixed user ID for session tracking
        self._runner = Runner(
            app_name=self._agent.name,                         # Name of this agent
            agent=self._agent,                                 # LLM agent object
            artifact_service=InMemoryArtifactService(),        # In-memory artifact handler
            session_service=InMemorySessionService(),          # In-memory session storage
            memory_service=InMemoryMemoryService(),            # In-memory conversation memory
        )
        
        # 3) Start periodic discovery task (optional)
        self._start_periodic_discovery()

    def _build_agent(self) -> LlmAgent:
        """
        Construct the Gemini LLM agent with all available tools.

        Returns:
            LlmAgent: Configured ADK agent ready to run.
        """
        # Gather A2A tools
        tools = [
            self._list_agents,    # Function listing child A2A agents
            self._delegate_task,  # Async function for routing to A2A agents
        ]
        # Create and return the LlmAgent
        return LlmAgent(
            model="gemini-2.5-flash",                      # Gemini flash model for orchestration
            name="orchestrator_agent",                        # Unique name for this agent
            description="Routes requests to A2A agents or MCP tools.",
            instruction=self._root_instruction,                  # System prompt callback
            tools=tools,                                        # List of tool functions
        )

    def _root_instruction(self, context: ReadonlyContext) -> str:
        """
        System prompt generator: instructs the LLM how to use available tools.

        Args:
            context (ReadonlyContext): Read-only context (unused here).
        """
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        return (
            "You are UNITED AIRLINES' Chief Intelligence Orchestrator, coordinating all analysis agents\n"
            "to provide comprehensive flight demand predictions and insights for United's network.\n\n"
            
            "UNITED AIRLINES CONTEXT:\n"
            "- You coordinate specialized agents to analyze factors affecting United's flight demand\n"
            "- Focus on United's hubs: ORD, DEN, IAH, EWR, SFO, IAD, LAX\n"
            "- Consider United's competitive position vs Delta, American, Southwest\n"
            "- Optimize for United's revenue, not just passenger volume\n\n"
            
            "AVAILABLE CAPABILITIES:\n"
            "1) A2A Agents: _list_agents() to see available agents, _delegate_task(agent_name, message) to call them\n"
            "2) Each agent has specific capabilities - use _list_agents() to discover them\n\n"
            
            "UNITED-FOCUSED ROUTING:\n"
            "- United route/hub weather analysis → AviationWeatherAgent\n"
            "- Events at United hub cities or affecting United routes → LiveEventsAgent\n"
            "- Economic factors for United's markets → EconomicIndicatorsAgent\n"
            "- News about United, competitors, or aviation industry → GoogleNewsAgent\n"
            "- Flight booking sites, United.com analysis → WebScrapingAgent\n"
            "- Flight pricing, route analysis, competitor comparison → FlightIntelligenceAgent\n"
            "- General greetings → GreetingAgent\n\n"
            
            "INTEGRATED ANALYSIS PATTERNS:\n"
            "- 'United demand forecast for Chicago' → LiveEventsAgent + AviationWeatherAgent + EconomicIndicatorsAgent\n"
            "- 'Impact of fuel prices on United' → GoogleNewsAgent + EconomicIndicatorsAgent\n"
            "- 'United's Pacific route analysis' → EconomicIndicatorsAgent + GoogleNewsAgent + AviationWeatherAgent\n"
            "- 'Competitor analysis for United' → GoogleNewsAgent + WebScrapingAgent\n\n"
            
            "COMPOUND REQUEST HANDLING:\n"
            "- When users ask for multiple things (e.g., 'give me a greeting AND fetch content'):\n"
            "  1. Identify ALL requested tasks\n"
            "  2. Execute each task by calling appropriate agents\n"
            "  3. Combine and present ALL results to the user\n"
            "- NEVER forget to complete any part of a multi-part request\n"
            "- Execute tasks in logical order (e.g., greeting before content fetch)\n\n"
            
            f"DATE/TIME AWARENESS:\n"
            f"- Today is {today.strftime('%A, %B %d, %Y')} ({today.strftime('%Y-%m-%d')})\n"
            f"- Tomorrow is {tomorrow.strftime('%A, %B %d, %Y')} ({tomorrow.strftime('%Y-%m-%d')})\n"
            f"- When users say 'tomorrow', 'next month', etc., calculate from today's date\n"
            f"- For LiveEventsAgent, provide specific date ranges (start_date and end_date)\n"
            f"- Example: 'tomorrow' = {tomorrow.strftime('%Y-%m-%d')} to {tomorrow.strftime('%Y-%m-%d')}\n\n"
            
            "ERROR HANDLING:\n"
            "- If an agent returns an error, explain it clearly to the user\n"
            "- For LiveEventsAgent errors: mention it might be an API issue and suggest trying again\n"
            "- Always provide context about what went wrong\n"
            "- Suggest alternatives when appropriate\n\n"
            
            "RESPONSE SYNTHESIS:\n"
            "- ALWAYS clearly attribute which agent provided which information\n"
            "- Use format like: 'According to [AgentName]:' or '[AgentName] reports:'\n"
            "- For multiple agent calls, structure the response with clear sections\n"
            "- Label each section with the contributing agent(s)\n"
            "- Example: '### Economic Analysis (from EconomicIndicatorsAgent)'\n"
            "- Maintain the original agent's response quality\n"
            "- Add brief transitions between different agent responses\n"
            "- In summary sections, cite which agents contributed key insights\n\n"
            
            "QUANTITATIVE SYNTHESIS REQUIREMENTS:\n"
            "- Aggregate numerical data from multiple agents into unified insights\n"
            "- Calculate combined impact: 'Total demand impact: +23% (Events: +15%, Weather: -5%, Economics: +13%)'\n"
            "- Show cross-agent correlations: 'High fuel prices ($3.45/gal) + 3 major Chicago events = Est. $2.3M revenue opportunity'\n"
            "- Provide confidence ranges when combining uncertain data: 'Demand forecast: 85-92% load factor'\n"
            "- Summarize with key metrics dashboard:\n"
            "  • Total flights analyzed: X across Y routes\n"
            "  • Price range: $XXX-$YYYY (median: $ZZZ)\n"
            "  • Weather impact: -X% capacity at Z hubs\n"
            "  • Event-driven demand: +X% for Y cities\n"
            "  • Competitive position: United X% vs Delta Y% market share\n"
            "- Always conclude with specific, quantified recommendations\n\n"
            
            "BEST PRACTICES:\n"
            "- Always validate and sanitize inputs before passing to agents\n"
            "- Think step-by-step about user intent\n"
            "- Be thorough - complete ALL requested tasks\n"
            "- Preserve the unique character of each agent's response\n"
            "- If unsure about routing, explain your reasoning\n\n"
            
            "UNITED DEMAND PREDICTION FOCUS:\n"
            "When analyzing for United, always consider:\n"
            "1. Revenue impact (not just passenger numbers)\n"
            "2. Premium cabin demand (business/first class)\n"
            "3. Cargo opportunities on routes\n"
            "4. MileagePlus member engagement\n"
            "5. Competitive advantages/threats\n\n"
            
            "Remember: You're United's orchestrator. Every analysis should ultimately help United\n"
            "optimize its network, pricing, and competitive position. Coordinate agents to provide\n"
            "integrated insights, not isolated data points."
        )

    def _list_agents(self) -> list[str]:
        """
        A2A tool: returns the list of names of registered child agents.

        Returns:
            list[str]: Agent names for delegation.
        """
        return list(self.connectors.keys())
    
    def _update_connectors(self, agent_cards: list[AgentCard]):
        """Update connectors based on new agent cards."""
        # Track which agents we've seen
        seen_agents = set()
        
        for card in agent_cards:
            seen_agents.add(card.name)
            if card.name not in self.connectors:
                # New agent discovered
                self.connectors[card.name] = AgentConnector(card.name, card.url)
                self.agent_urls[card.name] = card.url
                logger.info(f"[Discovery] New agent discovered: {card.name} at {card.url}")
            elif self.agent_urls.get(card.name) != card.url:
                # Agent URL changed
                self.connectors[card.name] = AgentConnector(card.name, card.url)
                self.agent_urls[card.name] = card.url
                logger.info(f"[Discovery] Agent URL updated: {card.name} -> {card.url}")
        
        # Remove agents that are no longer in registry
        removed_agents = set(self.connectors.keys()) - seen_agents
        for agent_name in removed_agents:
            del self.connectors[agent_name]
            if agent_name in self.agent_urls:
                del self.agent_urls[agent_name]
            logger.info(f"[Discovery] Agent removed: {agent_name}")
    
    async def _rediscover_agents(self):
        """Re-discover agents from registry."""
        async with self.discovery_lock:
            try:
                logger.info("[Discovery] Re-discovering agents...")
                agent_cards = await self.discovery_client.list_agent_cards()
                self._update_connectors(agent_cards)
                self.last_discovery_time = time.time()
                # Clear failed agents set on successful discovery
                self.failed_agents.clear()
                logger.info(f"[Discovery] Found {len(agent_cards)} agents")
            except Exception as e:
                logger.error(f"[Discovery] Failed to re-discover agents: {e}")
    
    def _start_periodic_discovery(self, interval_minutes: int = 5):
        """Start background task for periodic agent discovery."""
        def periodic_task():
            while True:
                time.sleep(interval_minutes * 60)
                try:
                    asyncio.run(self._rediscover_agents())
                except Exception as e:
                    logger.error(f"[Discovery] Periodic discovery failed: {e}")
        
        # Start background thread
        discovery_thread = threading.Thread(target=periodic_task, daemon=True)
        discovery_thread.start()
        logger.info(f"[Discovery] Started periodic discovery (every {interval_minutes} minutes)")

    async def _delegate_task(
        self,
        agent_name: str,
        message: str,
        tool_context: ToolContext
    ) -> str:
        """
        A2A tool: forwards a message to a child agent and returns its reply.

        Args:
            agent_name (str): Name of the target agent.
            message (str): The user message to send.
            tool_context (ToolContext): Holds state across invocations (e.g., session ID).

        Returns:
            str: The text of the agent's reply, or empty string on failure.
        """
        # Ensure the agent exists
        if agent_name not in self.connectors:
            # Try re-discovery if agent not found
            logger.warning(f"[Discovery] Agent '{agent_name}' not found, triggering re-discovery...")
            await self._rediscover_agents()
            
            # Check again after re-discovery
            if agent_name not in self.connectors:
                raise ValueError(f"Unknown agent: {agent_name} (even after re-discovery)")
        # Persist or create a session_id between calls
        state = tool_context.state
        if "session_id" not in state:
            state["session_id"] = str(uuid.uuid4())
        session_id = state["session_id"]
        # Send the task and await its completion
        try:
            task = await self.connectors[agent_name].send_task(message, session_id)
            # Remove from failed agents if successful
            self.failed_agents.discard(agent_name)
            # Extract the last history entry if present
            if task.history and len(task.history) > 1:
                return task.history[-1].parts[0].text
            return ""
        except Exception as e:
            # Track failed agent
            self.failed_agents.add(agent_name)
            logger.error(f"[Discovery] Agent '{agent_name}' failed: {e}")
            
            # Trigger re-discovery on failure
            if agent_name in self.failed_agents:
                logger.info(f"[Discovery] Triggering re-discovery due to failed agent: {agent_name}")
                await self._rediscover_agents()
                
                # Try one more time with potentially updated connector
                if agent_name in self.connectors:
                    try:
                        task = await self.connectors[agent_name].send_task(message, session_id)
                        self.failed_agents.discard(agent_name)
                        if task.history and len(task.history) > 1:
                            return task.history[-1].parts[0].text
                        return ""
                    except Exception as retry_error:
                        logger.error(f"[Discovery] Agent '{agent_name}' still failing after re-discovery: {retry_error}")
                        raise retry_error
            
            raise e

    async def invoke(self, query: str, session_id: str) -> str:
        """
        Primary entrypoint: handles a user query.

        Steps:
          1) Create or retrieve a session
          2) Wrap query into LLM Content format
          3) Run the Runner (may invoke tools)
          4) Return the final text output
        Note - function updated 28 May 2025
        Summary of changes:
        1. Agent's invoke method is made async
        2. All async calls (get_session, create_session, run_async) 
            are awaited inside invoke method
        3. task manager's on_send_task updated to await the invoke call

        Reason - get_session and create_session are async in the 
        "Current" Google ADK version and were synchronous earlier 
        when this lecture was recorded. This is due to a recent change 
        in the Google ADK code 
        https://github.com/google/adk-python/commit/1804ca39a678433293158ec066d44c30eeb8e23b

        """
        # 1) Get or create a session for this user and session_id
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
        # 2) Wrap user text into Content object for Gemini
        content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=query)]
        )
        # 🚀 Run the agent using the Runner and collect the last event
        last_event = None
        async for event in self._runner.run_async(
            user_id=self._user_id,
            session_id=session.id,
            new_message=content
        ):
            last_event = event

        # 🧹 Fallback: return empty string if something went wrong
        if not last_event or not last_event.content or not last_event.content.parts:
            return ""

        # 📤 Extract and join all text responses into one string
        return "\n".join([p.text for p in last_event.content.parts if p.text])


class OrchestratorTaskManager(InMemoryTaskManager):
    """
    TaskManager wrapper: exposes OrchestratorAgent.invoke()
    over the `tasks/send` JSON-RPC endpoint.
    """
    def __init__(self, agent: OrchestratorAgent):
        super().__init__()             # Initialize in-memory store and lock
        self.agent = agent             # Store reference to orchestrator logic

    def _get_user_text(self, request: SendTaskRequest) -> str:
        """
        Helper: extract raw user text from JSON-RPC request.

        Args:
            request (SendTaskRequest): Incoming RPC request.

        Returns:
            str: The text from the request payload.
        """
        return request.params.message.parts[0].text

    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        """
        Handle `tasks/send` calls:
          1) Store incoming message in memory
          2) Invoke the orchestrator to get a reply
          3) Append the reply, mark task COMPLETED
          4) Return the full Task in the response
        """
        logger.info(f"OrchestratorTaskManager received task {request.params.id}")
        # Store or update the task record
        task = await self.upsert_task(request.params)
        # Extract the text and invoke orchestration logic
        user_text = self._get_user_text(request)
        reply_text = await self.agent.invoke(user_text, request.params.sessionId)
        # Wrap reply in a Message object
        msg = Message(role="agent", parts=[TextPart(text=reply_text)])
        # Safely append reply and update status under lock
        async with self.lock:
            task.status = TaskStatus(state=TaskState.COMPLETED)
            task.history.append(msg)
        # Return the RPC response including the updated task
        return SendTaskResponse(id=request.id, result=task)
