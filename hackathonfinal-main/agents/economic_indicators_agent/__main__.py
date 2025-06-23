# =============================================================================
# agents/economic_indicators_agent/__main__.py
# =============================================================================
# Purpose:
# Main script that starts the Economic Indicators Agent server.
# =============================================================================

from server.server import A2AServer
from models.agent import AgentCard, AgentCapabilities, AgentSkill
from agents.economic_indicators_agent.task_manager import EconomicIndicatorsTaskManager
from agents.economic_indicators_agent.agent import EconomicIndicatorsAgent

import click
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command()
@click.option("--host", default="localhost", help="Host to bind the server to")
@click.option("--port", default=10006, help="Port number for the server")
def main(host, port):
    """
    Start the Economic Indicators Agent server.
    
    This agent analyzes IMF economic data to predict flight demand patterns.
    """
    
    logger.info("=" * 60)
    logger.info("ECONOMIC INDICATORS AGENT")
    logger.info("Analyzes IMF data for flight demand forecasting")
    logger.info("=" * 60)

    # Define capabilities
    capabilities = AgentCapabilities(streaming=False)

    # Define the skill this agent offers
    skill = AgentSkill(
        id="economic_analysis",
        name="Economic Indicators Analysis",
        description="Analyzes GDP, exchange rates, inflation, and investment flows for demand forecasting",
        tags=["economics", "imf", "gdp", "exchange", "inflation", "demand", "forecasting"],
        examples=[
            "Analyze economic conditions for flights between USA and UK",
            "How is GDP growth affecting travel demand in Asia?",
            "What's the exchange rate impact on US-Europe routes?",
            "Show me economic indicators for Brazil",
            "Analyze investment flows between China and USA",
            "How will inflation affect travel demand next quarter?"
        ]
    )

    # Create agent card
    agent_card = AgentCard(
        name="EconomicIndicatorsAgent",
        description="Analyzes IMF economic data including GDP growth, exchange rates, inflation, and investment flows to predict flight demand patterns and provide route optimization insights.",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=EconomicIndicatorsAgent.SUPPORTED_CONTENT_TYPES,
        defaultOutputModes=EconomicIndicatorsAgent.SUPPORTED_CONTENT_TYPES,
        capabilities=capabilities,
        skills=[skill]
    )

    # Start the server
    server = A2AServer(
        host=host,
        port=port,
        agent_card=agent_card,
        task_manager=EconomicIndicatorsTaskManager(agent=EconomicIndicatorsAgent())
    )

    logger.info(f"Starting Economic Indicators Agent on {host}:{port}")
    logger.info("Available IMF data sources:")
    logger.info("  - IFS: International Financial Statistics")
    logger.info("  - CDIS: Coordinated Direct Investment Survey")
    logger.info("  - CPIS: Portfolio Investment Survey")
    logger.info("  - BOP: Balance of Payments")
    logger.info("")
    logger.info("Key indicators tracked:")
    logger.info("  - GDP growth rates")
    logger.info("  - Exchange rates")
    logger.info("  - Inflation rates")
    logger.info("  - Foreign direct investment")
    logger.info("  - Trade balances")
    
    server.start()


if __name__ == "__main__":
    main()