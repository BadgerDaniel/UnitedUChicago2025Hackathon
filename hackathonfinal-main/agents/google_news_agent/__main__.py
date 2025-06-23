# =============================================================================
# agents/google_news_agent/__main__.py
# =============================================================================
# Purpose:
# Main script that starts the Google News Agent server.
# =============================================================================

from server.server import A2AServer
from models.agent import AgentCard, AgentCapabilities, AgentSkill
from agents.google_news_agent.task_manager import GoogleNewsTaskManager
from agents.google_news_agent.agent import GoogleNewsAgent

import click
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command()
@click.option("--host", default="localhost", help="Host to bind the server to")
@click.option("--port", default=10007, help="Port number for the server")
def main(host, port):
    """
    Start the Google News Agent server.
    
    This agent searches and analyzes Google News for flight demand insights.
    """
    
    logger.info("=" * 60)
    logger.info("GOOGLE NEWS AGENT")
    logger.info("Analyzes news events for flight demand forecasting")
    logger.info("=" * 60)

    # Define capabilities
    capabilities = AgentCapabilities(streaming=False)

    # Define the skill this agent offers
    skill = AgentSkill(
        id="news_analysis",
        name="Google News Analysis",
        description="Searches and analyzes Google News for events impacting flight demand",
        tags=["news", "events", "analysis", "demand", "forecasting", "google"],
        examples=[
            "What major events are happening in Europe next month?",
            "Find news about business conferences in Asia",
            "Search for sports events affecting travel to Brazil",
            "What political developments might impact US-China flights?",
            "Find tourism-related news for Caribbean destinations",
            "Search for weather events affecting major airports"
        ]
    )

    # Create agent card
    agent_card = AgentCard(
        name="GoogleNewsAgent",
        description="Searches and analyzes Google News to identify events, trends, and developments that impact flight demand patterns and travel forecasting.",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=GoogleNewsAgent.SUPPORTED_CONTENT_TYPES,
        defaultOutputModes=GoogleNewsAgent.SUPPORTED_CONTENT_TYPES,
        capabilities=capabilities,
        skills=[skill]
    )

    # Start the server
    server = A2AServer(
        host=host,
        port=port,
        agent_card=agent_card,
        task_manager=GoogleNewsTaskManager(agent=GoogleNewsAgent())
    )

    logger.info(f"Starting Google News Agent on {host}:{port}")
    logger.info("Using SerpAPI for Google News searches")
    logger.info("")
    logger.info("Key analysis areas:")
    logger.info("  - Major events and conferences")
    logger.info("  - Economic and political developments")
    logger.info("  - Natural disasters and weather events")
    logger.info("  - Tourism trends and travel advisories")
    logger.info("  - Cultural festivals and sports events")
    
    server.start()


if __name__ == "__main__":
    main()