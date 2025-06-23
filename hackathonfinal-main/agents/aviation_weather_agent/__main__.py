# =============================================================================
# agents/aviation_weather_agent/__main__.py
# =============================================================================
# Purpose:
# This is the main script that starts the AviationWeatherAgent server.
# =============================================================================

from server.server import A2AServer
from models.agent import AgentCard, AgentCapabilities, AgentSkill
from agents.aviation_weather_agent.task_manager import AviationWeatherTaskManager
from agents.aviation_weather_agent.agent import AviationWeatherAgent

import click
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command()
@click.option("--host", default="localhost", help="Host to bind the server to")
@click.option("--port", default=10005, help="Port number for the server")
def main(host, port):
    """
    Start the Aviation Weather Agent server.
    
    DISCLAIMER: This agent provides weather data for informational purposes only.
    Do not use for actual flight planning or operational decisions.
    """
    
    logger.info("=" * 60)
    logger.info("AVIATION WEATHER AGENT - DISCLAIMER")
    logger.info("This agent provides weather data for INFORMATIONAL purposes only.")
    logger.info("DO NOT use for actual flight planning or in-flight decisions!")
    logger.info("Always consult official sources for operational use.")
    logger.info("=" * 60)

    # Define capabilities
    capabilities = AgentCapabilities(streaming=False)

    # Define the skill this agent offers
    skill = AgentSkill(
        id="aviation_weather",
        name="Aviation Weather Information",
        description="Provides METARs, TAFs, PIREPs, and route weather briefings (informational only)",
        tags=["weather", "aviation", "metar", "taf", "pirep", "flight"],
        examples=[
            "Get METAR for JFK",
            "What's the TAF for LAX?",
            "Show me PIREPs near ORD",
            "Get weather briefing from KJFK to KLAX with KPHX as alternate",
            "What's the current weather at Denver airport?"
        ]
    )

    # Create agent card
    agent_card = AgentCard(
        name="AviationWeatherAgent",
        description="Provides aviation weather information including METARs, TAFs, and PIREPs. FOR INFORMATIONAL USE ONLY - not for operational flight planning.",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=AviationWeatherAgent.SUPPORTED_CONTENT_TYPES,
        defaultOutputModes=AviationWeatherAgent.SUPPORTED_CONTENT_TYPES,
        capabilities=capabilities,
        skills=[skill]
    )

    # Start the server
    server = A2AServer(
        host=host,
        port=port,
        agent_card=agent_card,
        task_manager=AviationWeatherTaskManager(agent=AviationWeatherAgent())
    )

    logger.info(f"Starting Aviation Weather Agent on {host}:{port}")
    logger.info("Available capabilities:")
    logger.info("  - get_metar: Current weather observations")
    logger.info("  - get_taf: Terminal aerodrome forecasts")
    logger.info("  - get_pireps: Pilot reports")
    logger.info("  - get_route_weather: Complete route briefing")
    
    server.start()


if __name__ == "__main__":
    main()