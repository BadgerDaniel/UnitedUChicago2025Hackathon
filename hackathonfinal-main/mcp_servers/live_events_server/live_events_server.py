#!/usr/bin/env python3
"""MCP Live Events Server - Ticketmaster API integration for real-time event data."""

import argparse
import asyncio
import os
import logging
from typing import Optional
from dotenv import load_dotenv

import httpx
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP

# Load environment variables
load_dotenv()


class UpcomingEventsRequest(BaseModel):
    """Schema for the UpcomingEventsRequest tool, which searches Ticketmaster for upcoming music events."""
    
    city: str = Field(description="City in which search for events.")
    start_dttm_str: str = Field(
        description="Start date/time in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ). Example: 2025-02-08T00:00:00Z"
    )
    end_dttm_str: str = Field(
        description="End date/time in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ). Example: 2025-02-28T23:59:59Z"
    )
    keyword: Optional[str] = Field(
        default=None, description="Any optional keywords to help filter search results."
    )


class EventsApiClient:
    """Client for interacting with the Ticketmaster API."""
    
    def __init__(self, api_key: str):
        self.base_url = "https://app.ticketmaster.com/discovery/v2"
        self.api_key = api_key
        if not self.api_key:
            raise ValueError("Ticketmaster API key missing!")

    async def fetch_events(
        self,
        city: str,
        start_dttm_str: str,
        end_dttm_str: str,
        classification_name: str = "Music",
        keyword: Optional[str] = None,
    ) -> Optional[dict]:
        """Fetch events from Ticketmaster API."""
        async with httpx.AsyncClient() as client:
            try:
                params = {
                    "apikey": self.api_key,
                    "city": city,
                    "startDateTime": start_dttm_str,
                    "endDateTime": end_dttm_str,
                    "classificationName": classification_name,
                    "size": 100,
                }
                if keyword:
                    params["keyword"] = keyword
                    
                response = await client.get(
                    f"{self.base_url}/events.json",
                    params=params,
                    timeout=30.0,
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logging.error(f"Error fetching events: {e}")
                return None


def format_events(response_dict: Optional[dict]) -> str:
    """Format events data into a readable string."""
    if not response_dict:
        return "No events found!"

    if "_embedded" not in response_dict or "events" not in response_dict["_embedded"]:
        return "No events found!"

    events = response_dict["_embedded"]["events"]
    if not events:
        return "No events found!"

    formatted_events = []
    for event in events:
        try:
            # Extract event information safely
            name = event.get("name", "Unknown Event")
            url = event.get("url", "No URL available")
            
            # Handle datetime
            dates = event.get("dates", {})
            start_info = dates.get("start", {})
            datetime_str = start_info.get("dateTime", start_info.get("localDate", "Unknown Date"))
            
            # Handle genres
            classifications = event.get("classifications", [])
            genres = []
            for classification in classifications:
                if "genre" in classification and "name" in classification["genre"]:
                    genres.append(classification["genre"]["name"])
            genres_str = ", ".join(set(genres)) if genres else "Unknown Genre"
            
            # Handle info
            info = event.get("info", "No additional info")
            
            # Handle venue
            embedded = event.get("_embedded", {})
            venues = embedded.get("venues", [])
            venue_name = venues[0]["name"] if venues and "name" in venues[0] else "Unknown Venue"
            
            formatted_event = f"""
Name: {name}
Link: {url}
Event Datetime: {datetime_str}
Genres: {genres_str}
Info: {info}
Venue: {venue_name}
"""
            formatted_events.append(formatted_event)
            
        except Exception as e:
            logging.warning(f"Error formatting event: {e}")
            continue
    
    return "\n\n".join(formatted_events) if formatted_events else "No events could be formatted!"


# Global API client
api_client = None


def setup_api_client():
    """Setup the API client with the API key."""
    global api_client
    api_key = os.environ.get("TICKETMASTER_API_KEY")
    if not api_key:
        raise ValueError("TICKETMASTER_API_KEY environment variable is required!")
    api_client = EventsApiClient(api_key)


# Create the FastMCP app
app = FastMCP(
    name="mcp-live-events",
    description="MCP server that integrates with the Ticketmaster API to provide real-time event data"
)


@app.tool()
async def get_upcoming_events(
    city: str,
    start_dttm_str: str,
    end_dttm_str: str,
    keyword: Optional[str] = None
) -> str:
    """Fetch upcoming events based on city, time range, and keyword.
    
    Args:
        city: City in which search for events
        start_dttm_str: Start date/time in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ). Example: 2025-02-08T00:00:00Z
        end_dttm_str: End date/time in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ). Example: 2025-02-28T23:59:59Z
        keyword: Any optional keywords to help filter search results
    
    Returns:
        Formatted string of upcoming events
    """
    try:
        if not api_client:
            return "Error: API client not initialized. Please check your TICKETMASTER_API_KEY."
        
        response = await api_client.fetch_events(
            city=city,
            start_dttm_str=start_dttm_str,
            end_dttm_str=end_dttm_str,
            keyword=keyword
        )
        
        return format_events(response)
        
    except Exception as e:
        logging.error(f"Error in get_upcoming_events: {e}")
        return f"Error fetching events: {str(e)}"


def setup_server_config():
    """Setup server configuration from command line args."""
    parser = argparse.ArgumentParser(description="MCP Live Events Server")
    parser.add_argument(
        "--port",
        type=int,
        default=8002,
        help="Port to run server on (default: 8002)"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to run server on (default: 127.0.0.1)"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    return args


if __name__ == "__main__":
    print("MCP Live Events server is running!")
    
    try:
        # Setup API client
        setup_api_client()
        args = setup_server_config()
        
        print(f"Ticketmaster API integration ready")
        print(f"Server starting on {args.host}:{args.port}")
        
        # Run the server with SSE transport
        app.run(transport="sse")
        
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please set the TICKETMASTER_API_KEY environment variable")
        exit(1)
    except Exception as e:
        print(f"Server error: {e}")
        exit(1)