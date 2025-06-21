"""
Streamlined Travel Analysis Multi-Agent System

This package contains specialized agents for comprehensive travel analysis:
- Weather Agent: Weather impact analysis
- Event Agent: Event impact on travel
- Flight Agent: Flight pricing analysis  
- Orchestrator Agent: Multi-agent coordination

All agents work together to provide insights into travel pricing correlations.
"""

__version__ = "2.0.0"
__author__ = "Streamlined A2A Travel Analysis System"

from .weather_agent import WeatherAgent
from .event_agent import EventAgent
from .flight_agent import FlightAgent
from .orchestrator_agent import OrchestratorAgent

__all__ = [
    "WeatherAgent",
    "EventAgent", 
    "FlightAgent",
    "OrchestratorAgent"
]
