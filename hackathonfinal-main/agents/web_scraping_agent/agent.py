# =============================================================================
# agents/google_adk/agent.py
# =============================================================================
# 🎯 Purpose:
# This file defines a WebScrapingAgent that provides powerful web scraping capabilities.
# It uses Google's ADK with Gemini model and integrates fetch and playwright MCP tools.
# =============================================================================


# -----------------------------------------------------------------------------
# 📦 Built-in & External Library Imports
# -----------------------------------------------------------------------------

from datetime import datetime, timedelta  # Used to get the current system time and date calculations

# 🧠 Gemini-based AI agent provided by Google's ADK
from google.adk.agents.llm_agent import LlmAgent

# 📚 ADK services for session, memory, and file-like "artifacts"
from google.adk.sessions import InMemorySessionService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.artifacts import InMemoryArtifactService

# 🏃 The "Runner" connects the agent, session, memory, and files into a complete system
from google.adk.runners import Runner

# 🧾 Gemini-compatible types for formatting input/output messages
from google.genai import types

# 🛠️ FunctionTool to wrap Python functions as LLM tools
from google.adk.tools.function_tool import FunctionTool
from google.adk.agents.readonly_context import ReadonlyContext

# MCP connector for fetch tool
from utilities.mcp.mcp_connect import MCPConnector

# 🔐 Load environment variables (like API keys) from a `.env` file
from dotenv import load_dotenv
load_dotenv()  # Load variables like GOOGLE_API_KEY into the system
# This allows you to keep sensitive data out of your code.

import logging
logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# 🌐 WebScrapingAgent: Your AI agent for web scraping and automation
# -----------------------------------------------------------------------------

class WebScrapingAgent:
    # This agent only supports plain text input/output
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        """
        👷 Initialize the WebScrapingAgent:
        - Creates the LLM agent (powered by Gemini)
        - Sets up session handling, memory, and a runner to execute tasks
        - Loads MCP tools for web fetching and browser automation
        """
        # Load MCP tools
        self.mcp = MCPConnector()
        mcp_tools = self.mcp.get_tools()
        
        # Find web scraping tools (fetch and playwright)
        self.web_tools = []
        for tool in mcp_tools:
            if tool.name in ["fetch", "navigate", "screenshot", "click", "fill", "get_text", "evaluate", "get_page_info"]:
                self.web_tools.append(tool)
                logger.info(f"Loaded MCP tool: {tool.name}")
        
        self._agent = self._build_agent()  # Set up the Gemini agent
        self._user_id = "web_scraping_user"  # Use a fixed user ID for simplicity

        # 🧠 The Runner is what actually manages the agent and its environment
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),  # For files (not used here)
            session_service=InMemorySessionService(),    # Keeps track of conversations
            memory_service=InMemoryMemoryService(),      # Optional: remembers past messages
        )

    def _build_agent(self) -> LlmAgent:
        """
        ⚙️ Creates and returns a Gemini agent with basic settings and a tool to get current time.

        Returns:
            LlmAgent: An agent object from Google's ADK
        """
        # Define a tool to get the current time
        def get_current_time() -> str:
            """Get the current system time in YYYY-MM-DD HH:MM:SS format."""
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Start with time tool
        tools = [FunctionTool(get_current_time)]
        
        # Add MCP web scraping tools
        for mcp_tool in self.web_tools:
            # Create a wrapper factory to avoid closure issues
            def create_tool_wrapper(tool):
                async def wrapper(**kwargs) -> str:
                    """Fetch web content and convert to markdown."""
                    # If URL doesn't have protocol, add https://
                    if 'url' in kwargs and not kwargs['url'].startswith(('http://', 'https://')):
                        kwargs['url'] = f"https://{kwargs['url']}"
                    return await tool.run(kwargs)
                return wrapper
            
            # Create the wrapper for this specific tool
            tool_wrapper = create_tool_wrapper(mcp_tool)
            tool_wrapper.__name__ = mcp_tool.name
            tool_wrapper.__doc__ = mcp_tool.description or f"MCP tool: {mcp_tool.name}"
            
            # Wrap as FunctionTool
            tools.append(FunctionTool(tool_wrapper))
        
        return LlmAgent(
            model="gemini-2.5-flash",           # Gemini model version
            name="web_scraping_agent",                  # Name of the agent
            description="Provides web scraping capabilities with fetch and playwright tools",    # Description for metadata
            instruction=self._system_instruction,  # System prompt callback
            tools=tools                              # Add the time tool
        )
    
    def _system_instruction(self, context: ReadonlyContext) -> str:
        """System instruction for web scraping capabilities."""
        today = datetime.now()
        return (
            "You are a powerful Web Scraping agent with browser automation and content fetching capabilities.\n\n"
            
            f"CURRENT CONTEXT:\n"
            f"- Today is {today.strftime('%A, %B %d, %Y')} ({today.strftime('%Y-%m-%d')})\n"
            f"- Current time is available via get_current_time() tool\n\n"
            
            "CORE CAPABILITIES:\n"
            "1. Simple Web Fetching (fetch tool):\n"
            "   - fetch(url): Quick HTTP GET requests to retrieve web content\n"
            "   - Automatically converts HTML to clean markdown format\n"
            "   - Best for: Static content, APIs, simple web pages\n\n"
            
            "2. Browser Automation (playwright tools):\n"
            "   - navigate(url): Open pages in a real browser\n"
            "   - screenshot(): Capture visual snapshots\n"
            "   - click(selector): Interact with buttons and links\n"
            "   - fill(selector, value): Complete forms\n"
            "   - get_text(selector): Extract specific text\n"
            "   - evaluate(script): Execute JavaScript\n"
            "   - get_page_info(): Get page metadata\n"
            "   - Best for: Dynamic content, interactions, visual capture\n\n"
            
            "3. Time Services:\n"
            "   - get_current_time(): System time for timestamps\n"
            "   - Useful for logging scraping activities\n\n"
            
            "INTELLIGENT SCRAPING STRATEGY:\n"
            "- Choose the right tool for the task:\n"
            "  * Use fetch() for simple, static content\n"
            "  * Use playwright for JavaScript-heavy sites\n"
            "  * Use playwright for form submissions or interactions\n"
            "- Handle errors gracefully and retry with different approaches\n"
            "- Extract structured data efficiently\n"
            "- Respect rate limits and robots.txt\n\n"
            
            "COMMON SCRAPING PATTERNS:\n"
            "- Login flows: navigate → fill → click → wait\n"
            "- Data extraction: navigate → get_text or evaluate\n"
            "- Visual capture: navigate → screenshot\n"
            "- API data: fetch with proper headers\n"
            "- Dynamic content: navigate → wait → get_text\n\n"
            
            "QUANTITATIVE OUTPUT REQUIREMENTS:\n"
            "- Always lead with specific numbers: 'Scraped 234 data points', 'Found 15 tables'\n"
            "- Show extraction rates: 'Successfully extracted 98% of targeted fields'\n"
            "- Include performance metrics: 'Page loaded in 2.3 seconds', 'Total scrape: 45 seconds'\n"
            "- Specify data volumes: 'Retrieved 1,247 rows across 8 columns'\n"
            "- Add accuracy context: 'Validated 100% of email formats', '3 missing values found'\n"
            "- Calculate success rates: 'Form submission success: 95% (19/20 attempts)'\n"
            "- Provide size metrics: 'HTML: 234KB', 'Extracted text: 12KB', 'Images: 15 files'\n"
            "- Include element counts: 'Found 47 links, 23 buttons, 15 input fields'\n"
            "- Show comparison data: 'Price changed by +$12 (5%) since last scrape'\n"
            "- Quantify completeness: 'Coverage: 87% of product catalog (1,043/1,200 items)'\n\n"
            
            f"CONTEXT:\n"
            f"- Current time: {today.strftime('%I:%M %p on %A, %B %d, %Y')}\n"
            f"- Use timestamps when logging scraping activities\n\n"
            
            "Remember: You're a sophisticated web scraping assistant with both simple fetch and advanced browser automation capabilities."
        )

    async def invoke(self, query: str, session_id: str) -> str:
        """
        📥 Handle a user query and return a response string.

        Args:
            query (str): What the user said (e.g., "what time is it?")
            session_id (str): Helps group messages into a session

        Returns:
            str: Agent's reply (usually the current time)
        """

        # 🔁 Try to reuse an existing session (or create one if needed)
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
                state={}  # Optional dictionary to hold session state
            )

        # 📨 Format the user message in a way the Gemini model expects
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

    async def stream(self, query: str, session_id: str):
        """
        🌀 Simulates a "streaming" agent that returns a single reply.
        This is here just to demonstrate that streaming is possible.

        Yields:
            dict: Response payload that says the task is complete and gives the time
        """
        yield {
            "is_task_complete": True,
            "content": f"The current time is: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        }
