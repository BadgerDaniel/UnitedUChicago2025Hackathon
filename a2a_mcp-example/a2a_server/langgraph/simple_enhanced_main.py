import logging
from simple_enhanced_agent import SimpleTravelAnalysisAgent
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
    try:
        capabilities = AgentCapabilities(streaming=True, pushNotifications=True)
        
        skills = [
            AgentSkill(
                id='travel_analysis',
                name='Travel Analysis',
                description='Analyzes weather, events, and flight pricing correlations',
                tags=['travel', 'weather', 'events', 'flights'],
                examples=[
                    'Why are flights expensive from NYC to Chicago?',
                    'How does weather affect flight prices to Miami?',
                    'Analyze travel factors for Boston to Denver'
                ],
            )
        ]
        
        agent_card = AgentCard(
            name='Travel Analysis Agent',
            description='Analyzes correlations between weather, events, and flight pricing',
            url=f'http://{host}:{port}/',
            version='1.0.0',
            defaultInputModes=SimpleTravelAnalysisAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=SimpleTravelAnalysisAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=skills,
        )

        notification_sender_auth = PushNotificationSenderAuth()
        notification_sender_auth.generate_jwk()
        agent = SimpleTravelAnalysisAgent()
        
        server = A2AServer(
            agent_card=agent_card,
            task_manager=AgentTaskManager(
                agent=agent,
                notification_sender_auth=notification_sender_auth,
            ),
            host=host,
            port=port,
        )

        server.app.add_route(
            '/.well-known/jwks.json',
            notification_sender_auth.handle_jwks_endpoint,
            methods=['GET'],
        )

        logger.info(f'Starting Travel Analysis Agent on {host}:{port}')
        server.start()
        
    except Exception as e:
        logger.error(f'Error starting server: {e}')
        exit(1)

if __name__ == "__main__":
    main()
