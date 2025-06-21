"""Enhanced main.py for the Travel Analysis Multi-Agent System."""

import logging
import os
import asyncio

import click

from enhanced_agent import TravelAnalysisAgent
from task_manager import AgentTaskManager
from google_a2a.common.server import A2AServer
from google_a2a.common.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from google_a2a.common.utils.push_notification_auth import PushNotificationSenderAuth

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main(host="localhost", port=10001):
    """Starts the Enhanced Travel Analysis Agent server."""
    try:
        # Define capabilities for the enhanced agent
        capabilities = AgentCapabilities(streaming=True, pushNotifications=True)
        
        # Define multiple skills for the travel analysis agent
        skills = [
            AgentSkill(
                id='weather_flight_correlation',
                name='Weather-Flight Price Correlation Analysis',
                description='Analyzes how weather conditions affect flight pricing and availability',
                tags=['weather', 'flights', 'correlation', 'pricing'],
                examples=[
                    'Why are flights to Miami more expensive during hurricane season?',
                    'How does severe weather in Chicago affect flight prices?'
                ],
            ),
            AgentSkill(
                id='event_impact_analysis',
                name='Event Impact on Travel Analysis',
                description='Analyzes how major events affect travel demand and pricing',
                tags=['events', 'travel', 'impact', 'pricing'],
                examples=[
                    'How do music festivals affect hotel and flight prices?',
                    'What events are causing high flight prices to Las Vegas next month?'
                ],
            ),
            AgentSkill(
                id='comprehensive_travel_analysis',
                name='Comprehensive Travel Factor Analysis',
                description='Performs multi-factor analysis considering weather, events, and market conditions',
                tags=['comprehensive', 'multi-factor', 'analysis', 'recommendations'],
                examples=[
                    'What are the best dates to fly from NYC to LA considering all factors?',
                    'Why were flights expensive on certain dates? Was it weather or events?'
                ],
            ),
            AgentSkill(
                id='agent_communication',
                name='Multi-Agent Coordination',
                description='Coordinates between weather, event, and flight agents for complex queries',
                tags=['coordination', 'multi-agent', 'collaboration'],
                examples=[
                    'Get weather impact on flights and correlate with event data',
                    'Coordinate analysis between all travel factors'
                ],
            )
        ]
        
        # Create agent card with enhanced capabilities
        agent_card = AgentCard(
            name='Travel Analysis Agent',
            description=(
                'Advanced travel analysis agent that coordinates between weather, event, and flight data '
                'to provide comprehensive insights into travel pricing patterns and recommendations. '
                'Specializes in multi-factor correlation analysis and cross-domain travel intelligence.'
            ),
            url=f'http://{host}:{port}/',
            version='2.0.0',
            defaultInputModes=TravelAnalysisAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=TravelAnalysisAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=skills,
        )

        # Initialize notification system
        notification_sender_auth = PushNotificationSenderAuth()
        notification_sender_auth.generate_jwk()
        
        # Create the enhanced travel analysis agent
        agent = TravelAnalysisAgent()
        
        # Create A2A server with enhanced task manager
        server = A2AServer(
            agent_card=agent_card,
            task_manager=AgentTaskManager(
                agent=agent,
                notification_sender_auth=notification_sender_auth,
            ),
            host=host,
            port=port,
        )

        # Add JWKS endpoint for push notifications
        server.app.add_route(
            '/.well-known/jwks.json',
            notification_sender_auth.handle_jwks_endpoint,
            methods=['GET'],
        )

        logger.info(f'Starting Enhanced Travel Analysis Agent server on {host}:{port}')
        logger.info('Agent capabilities:')
        logger.info('- Weather-Flight correlation analysis')
        logger.info('- Event impact assessment')
        logger.info('- Multi-factor travel analysis')
        logger.info('- Agent-to-agent communication')
        logger.info('- Streaming analysis support')
        
        server.start()
        
    except Exception as e:
        logger.error(f'An error occurred during server startup: {e}')
        exit(1)


@click.command()
@click.option('--host', default='localhost', help='Host to bind the server to')
@click.option('--port', default=10001, help='Port to bind the server to')
@click.option('--mcp-port', default=8001, help='Port for the enhanced MCP server')
def cli_main(host, port, mcp_port):
    """CLI entry point for the Enhanced Travel Analysis Agent."""
    logger.info(f'Starting with MCP server expected on port {mcp_port}')
    logger.info('Make sure to start the enhanced MCP server first:')
    logger.info(f'python a2a_mcp-example/mcp_server/enhanced_mcp_server.py')
    
    main(host, port)


if __name__ == "__main__":
    # For direct execution, use default parameters
    main()
