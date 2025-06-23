"""Duffel API configuration."""

import os
from typing import Final

# API Constants
DUFFEL_API_URL: Final = "https://api.duffel.com"
DUFFEL_API_VERSION: Final = "v2"

def get_api_token() -> str:
    """Get Duffel API token from environment."""
    # First check for test key
    token = os.getenv("DUFFEL_API_KEY")
    if not token:
        # Fallback to live key for backwards compatibility
        token = os.getenv("DUFFEL_API_KEY_LIVE")
    
    if not token:
        raise ValueError("DUFFEL_API_KEY environment variable not set")
    
    # Log if using test key
    if token.startswith("duffel_test"):
        import logging
        logging.info("Using Duffel test API key - will return simulated flight data")
    
    return token 