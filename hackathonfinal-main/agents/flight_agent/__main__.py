# =============================================================================
# agents/flight_agent/__main__.py
# =============================================================================
# Purpose:
# This is the main script that starts the FlightIntelligenceAgent server.
# =============================================================================

from server.server import A2AServer
from models.agent import AgentCard, AgentCapabilities, AgentSkill
from agents.flight_agent.task_manager import FlightTaskManager
from agents.flight_agent.agent import FlightIntelligenceAgent

import click
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command()
@click.option("--host", default="localhost", help="Host to bind the server to")
@click.option("--port", default=10008, help="Port number for the server")
def main(host, port):
    """
    Start the Flight Intelligence Agent server.
    
    Provides comprehensive flight search and pricing intelligence for United Airlines
    demand forecasting using both Amadeus and Duffel APIs.
    """
    
    logger.info("=" * 60)
    logger.info("FLIGHT INTELLIGENCE AGENT")
    logger.info("Comprehensive flight search and pricing analysis for United Airlines")
    logger.info("Powered by both Amadeus GDS and Duffel modern flight APIs")
    logger.info("=" * 60)

    # Define capabilities
    capabilities = AgentCapabilities(streaming=False)

    # Define the skill this agent offers
    skill = AgentSkill(
        id="flight_intelligence",
        name="Flight Pricing and Route Intelligence",
        description="Comprehensive flight search, pricing analysis, and competitive intelligence",
        tags=["amadeus", "duffel", "flights", "pricing", "routes", "united", "airlines", "demand", "search"],
        examples=[
            "Search for round-trip flights from Chicago to London",
            "Find the cheapest business class flights from SFO to Tokyo",
            "Compare United vs Delta pricing on transatlantic routes",
            "Plan a multi-city trip: NYC to London to Paris to NYC",
            "How many routes does Denver airport serve?",
            "What are the pricing trends for premium cabins?",
            "Find delay predictions for Newark flights",
            "Get detailed information about United Airlines"
        ]
    )

    # Create agent card
    agent_card = AgentCard(
        name="FlightIntelligenceAgent",
        description="Comprehensive flight search and pricing intelligence using Amadeus and Duffel APIs for United Airlines optimization",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=FlightIntelligenceAgent.SUPPORTED_CONTENT_TYPES,
        defaultOutputModes=FlightIntelligenceAgent.SUPPORTED_CONTENT_TYPES,
        capabilities=capabilities,
        skills=[skill]
    )

    # Start the server
    server = A2AServer(
        host=host,
        port=port,
        agent_card=agent_card,
        task_manager=FlightTaskManager()
    )

    logger.info(f"Starting Flight Intelligence Agent on {host}:{port}")
    logger.info("Available capabilities:")
    logger.info("AMADEUS TOOLS:")
    logger.info("  - flight-price-analysis: Historical pricing trends")
    logger.info("  - flight-offers-search: Real-time GDS availability and pricing")
    logger.info("  - flight-inspiration-search: Find destinations by price")
    logger.info("  - airport-routes: Route network analysis")
    logger.info("  - airline-routes: Competitor route analysis")
    logger.info("  - flight-delay-prediction: ML-based delay predictions")
    logger.info("  - airport-on-time-performance: Punctuality statistics")
    logger.info("DUFFEL TOOLS:")
    logger.info("  - search_flights: Advanced one-way flight search")
    logger.info("  - search_round_trip: Round-trip optimization")
    logger.info("  - search_multi_city: Complex itinerary planning")
    logger.info("  - get_airline_info: Detailed carrier information")
    
    server.start()


if __name__ == "__main__":
    main()