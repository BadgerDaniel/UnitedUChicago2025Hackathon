# =============================================================================
# agents/live_events_agent/__main__.py
# =============================================================================
# 🎯 Purpose:
#   Entry point to run the Live Events Agent as a standalone A2A server
# =============================================================================

import asyncio
import argparse
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# A2A server infrastructure
from server.server import A2AServer

# Agent components
from agents.live_events_agent.agent import LiveEventsAgent
from agents.live_events_agent.task_manager import LiveEventsTaskManager

# Agent metadata
from models.agent import AgentCard, AgentCapabilities, AgentSkill

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_agent_card(host: str, port: int) -> AgentCard:
    """
    Create the agent card describing the Live Events Agent's capabilities.
    
    Args:
        host: The host the agent is running on
        port: The port the agent is running on
    
    Returns:
        AgentCard: Metadata about this agent
    """
    return AgentCard(
        name="LiveEventsAgent",
        description=(
            "Analyzes live events data from Ticketmaster to identify concerts, shows, "
            "and festivals that could impact flight demand. Specializes in understanding "
            "event-driven travel patterns for airline route planning."
        ),
        url=f"http://{host}:{port}",
        version="1.0.0",
        capabilities=AgentCapabilities(
            streaming=False,
            pushNotifications=False,
            stateTransitionHistory=True
        ),
        skills=[
            AgentSkill(
                id="event_search",
                name="Event Search",
                description="Search for upcoming events by city and date range",
                examples=[
                    "What concerts are happening in Chicago next month?",
                    "Find major events in New York this weekend",
                    "Show me festivals in Los Angeles in March"
                ]
            ),
            AgentSkill(
                id="demand_analysis",
                name="Demand Analysis",
                description="Analyze how events might impact flight demand",
                examples=[
                    "Which events in Miami could drive flight demand next month?",
                    "Find events that might increase travel to Denver",
                    "What major festivals could impact flights to Austin?"
                ]
            ),
            AgentSkill(
                id="event_details",
                name="Event Details",
                description="Provide detailed information about specific events",
                examples=[
                    "Tell me about Taylor Swift concerts in Seattle",
                    "What's the capacity of upcoming events at Madison Square Garden?",
                    "Find multi-day festivals in California"
                ]
            )
        ]
    )


def main():
    """
    Main entry point for running the Live Events Agent server.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Live Events Agent A2A Server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=10004, help="Port to bind to")
    args = parser.parse_args()
    
    logger.info("Starting Live Events Agent...")
    
    try:
        # Create the agent and task manager
        agent = LiveEventsAgent()
        task_manager = LiveEventsTaskManager(agent)
        
        # Create the agent card
        agent_card = create_agent_card(args.host, args.port)
        
        # Create and start the A2A server
        server = A2AServer(
            agent_card=agent_card,
            task_manager=task_manager,
            host=args.host,
            port=args.port
        )
        
        logger.info(f"Live Events Agent ready at http://{args.host}:{args.port}")
        logger.info("Capabilities:")
        for skill in agent_card.skills:
            logger.info(f"  - {skill.name}: {skill.description}")
        
        # Start the server
        server.start()
        
    except Exception as e:
        logger.error(f"Failed to start Live Events Agent: {e}")
        raise


if __name__ == "__main__":
    main()