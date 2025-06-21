"""
Streamlined A2A server for Travel Analysis Agent.
Clean, production-ready implementation without duplicated code.
"""

import logging
from travel_analysis_agent import TravelAnalysisAgent
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
    """Start the Travel Analysis A2A server."""
    try:
        # Define agent capabilities
        capabilities = AgentCapabilities(streaming=True, pushNotifications=True)
        
        # Define travel analysis skills
        skills = [
            AgentSkill(
                id='weather_analysis',
                name='Weather Impact Analysis',
                description='Analyzes how weather conditions affect travel and flight operations',
                tags=['weather', 'travel', 'flights', 'impact'],
                examples=[
                    'How does weather in Miami affect flight delays?',
                    'Analyze weather impact on Chicago flights this weekend'
                ],
            ),
            AgentSkill(
                id='event_analysis', 
                name='Event Impact Analysis',
                description='Analyzes how major events affect travel demand and pricing',
                tags=['events', 'travel', 'pricing', 'demand'],
                examples=[
                    'How do events in Las Vegas affect flight prices?',
                    'Analyze event impact on Boston travel costs'
                ],
            ),
            AgentSkill(
                id='flight_pricing',
                name='Flight Pricing Analysis', 
                description='Analyzes flight pricing patterns and trends',
                tags=['flights', 'pricing', 'trends', 'analysis'],
                examples=[
                    'Why are flights to Denver expensive this month?',
                    'Analyze pricing trends for NYC to LA route'
                ],
            ),
            AgentSkill(
                id='correlation_analysis',
                name='Multi-Factor Correlation Analysis',
                description='Analyzes correlations between weather, events, and flight pricing',
                tags=['correlation', 'multi-factor', 'comprehensive', 'insights'],
                examples=[
                    'Why are flights from NYC to Chicago expensive on July 15th?',
                    'How do weather and events combine to affect Miami travel costs?',
                    'Analyze all factors affecting Boston to Denver travel'
                ],
            )
        ]
        
        # Create agent card
        agent_card = AgentCard(
            name='Travel Analysis Agent',
            description='Analyzes correlations between weather, events, and flight pricing to provide comprehensive travel insights',
            url=f'http://{host}:{port}/',
            version='2.0.0',
            defaultInputModes=TravelAnalysisAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=TravelAnalysisAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=skills,
        )

        # Setup authentication and agent
        notification_sender_auth = PushNotificationSenderAuth()
        notification_sender_auth.generate_jwk()
        agent = TravelAnalysisAgent()
        
        # Create A2A server
        server = A2AServer(
            agent_card=agent_card,
            task_manager=AgentTaskManager(
                agent=agent,
                notification_sender_auth=notification_sender_auth,
            ),
            host=host,
            port=port,
        )

        # Add authentication endpoint
        server.app.add_route(
            '/.well-known/jwks.json',
            notification_sender_auth.handle_jwks_endpoint,
            methods=['GET'],
        )

        logger.info(f'🚀 Starting Travel Analysis Agent on {host}:{port}')
        logger.info(f'📊 Capabilities: Weather, Events, Flight Pricing, Multi-Factor Correlation')
        logger.info(f'🔗 MCP Server: Expected on localhost:8000')
        
        server.start()
        
    except Exception as e:
        logger.error(f'❌ Error starting Travel Analysis Agent: {e}')
        exit(1)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Travel Analysis A2A Agent')
    parser.add_argument('--host', default='localhost', help='Host to bind to')
    parser.add_argument('--port', type=int, default=10001, help='Port to bind to')
    
    args = parser.parse_args()
    main(args.host, args.port)
