# =============================================================================
# agents/host_agent/entry_sse.py - Enhanced entry with SSE support
# =============================================================================

import asyncio
import logging
import click

from utilities.a2a.agent_discovery import DiscoveryClient
from server.sse_server import SSEServer  # Use our enhanced SSE server
from models.agent import AgentCard, AgentCapabilities, AgentSkill
from agents.host_agent.orchestrator import (
    OrchestratorAgent,
    OrchestratorTaskManager
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--host", default="localhost",
    help="Bind address for host agent"
)
@click.option(
    "--port", default=10000,
    help="Port for host agent"
)
@click.option(
    "--registry", default=None,
    help=(
        "Path to A2A registry JSON. "        
        "Defaults to utilities/a2a/agent_registry.json"
    )
)
def main(host: str, port: int, registry: str):
    """
    Starts the OrchestratorAgent A2A server with SSE support.
    """
    # 1) Discover child A2A agents
    discovery = DiscoveryClient(registry_file=registry)
    agent_cards = asyncio.run(discovery.list_agent_cards())

    if not agent_cards:
        logger.warning(
            "No A2A agents found – the orchestrator will have nothing to call"
        )

    # 2) Define this host agent's metadata with streaming enabled
    capabilities = AgentCapabilities(streaming=True)  # Enable streaming!
    skill = AgentSkill(
        id="orchestrate",
        name="Orchestrate Tasks",
        description=(
            "Routes user requests to child A2A agents or MCP tools based on intent."
        ),
        tags=["routing", "orchestration", "streaming"],
        examples=[
            "What is the time?",
            "Greet me",
            "Search the latest funding news for Acme Corp",
        ]
    )
    
    orchestrator_card = AgentCard(
        name="OrchestratorAgent",
        description="Delegates to child agents with SSE streaming support",
        url=f"http://{host}:{port}/",
        version="1.1.0",  # Bumped version for SSE
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=capabilities,
        skills=[skill]
    )

    # 3) Instantiate the orchestrator logic and task manager
    orchestrator = OrchestratorAgent(agent_cards=agent_cards, registry_file=registry)
    task_manager = OrchestratorTaskManager(agent=orchestrator)

    # 4) Use SSE server instead of regular server
    server = SSEServer(
        host=host,
        port=port,
        agent_card=orchestrator_card,
        task_manager=task_manager
    )
    server.start()


if __name__ == "__main__":
    main()