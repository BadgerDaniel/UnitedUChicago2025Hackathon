from servers.news_demand_explorer.tools import news_mcp
from servers.news_demand_explorer.llm_client import LLMClient, LLMProvider
from servers.news_demand_explorer.explorer import DemandExplorer
import json
from datetime import datetime
from typing import Optional, List
from mcp.server.fastmcp import FastMCP

# Initialize the MCP server

mcp = FastMCP("united-airlines-demand-explorer")
llm_client = None
demand_explorer = None

def initialize_components():
    """Initialize the LLM client and demand explorer"""
    global llm_client, demand_explorer
    llm_client = LLMClient(
        provider=LLMProvider.OPENAI,
        api_key="OPENAI_API_KEY",
        model="gpt-4o-mini"
    )
    demand_explorer = DemandExplorer(llm_client)


# Initialize on startup
initialize_components()


@mcp.tool()
async def analyze_route_demand(
        origin: str,
        destination: str,
        days_back: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        context: Optional[str] = ""
) -> str:
    """
    Analyze demand factors for a specific United Airlines route using flexible timeframes.

    Args:
        origin: Origin city/airport (e.g., 'Chicago', 'ORD', 'San Francisco')
        destination: Destination city/airport (e.g., 'New York', 'JFK', 'Los Angeles')
        days_back: Number of days to look back (alternative to date range)
        start_date: Start date for analysis (YYYY-MM-DD format)
        end_date: End date for analysis (YYYY-MM-DD format)
        context: Additional context for search (e.g., 'business travel', 'leisure', 'holiday season')
    """
    global demand_explorer

    if not origin or not destination:
        return "Error: Both origin and destination are required"

    # Parse dates if provided
    start_date_obj = None
    end_date_obj = None
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            return "Error: Invalid start_date format. Use YYYY-MM-DD"

    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            return "Error: Invalid end_date format. Use YYYY-MM-DD"

    analysis = await demand_explorer.analyze_route_demand_impact(
        origin, destination, start_date_obj, end_date_obj, days_back, context
    )

    return analysis


@mcp.tool()
async def explore_demand_events(
        location: str,
        event_types: List[str],
        timeframe: Optional[str] = "past_week"
) -> str:
    """
    Explore specific types of demand-affecting events in a location.

    Args:
        location: City or region to analyze
        event_types: Types of events to focus on (concerts, sports, conferences, festivals, protests, weather, economic)
        timeframe: Timeframe for event exploration (past_week, past_month, past_quarter, next_month, next_quarter)
    """
    global demand_explorer

    # Map timeframe to days
    timeframe_map = {
        "past_week": 7,
        "past_month": 30,
        "past_quarter": 90,
        "next_month": -30,  # Future events (would need different implementation)
        "next_quarter": -90
    }

    days_back = timeframe_map.get(timeframe, 7)

    if days_back < 0:
        return f"Future event exploration ({timeframe}) not yet implemented"

    # Generate search terms based on event types
    search_terms = []
    for event_type in event_types:
        search_terms.append(f"{event_type} {location}")

    articles = await demand_explorer.scrape_news_flexible_timeframe(
        search_terms, days_back=days_back
    )

    if not articles:
        return f"No {', '.join(event_types)} events found in {location} for {timeframe}"

    # Simple categorization and summary
    event_summary = f"Found {len(articles)} articles about {', '.join(event_types)} in {location} ({timeframe}):\n\n"

    for article in articles[:20]:  # Limit to first 20
        event_summary += f"• {article['title']} ({article['source']}, {article['published']})\n"

    return event_summary


@mcp.tool()
async def configure_llm(
        provider: str,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None
) -> str:
    """
    Configure the LLM provider and settings.

    Args:
        provider: LLM provider to use (openai, ollama, anthropic, azure_openai)
        model: Model name (e.g., 'gpt-4o-mini', 'llama3.2', 'claude-3-sonnet-20240229')
        api_key: API key for the provider
        endpoint: Custom endpoint URL (optional)
    """
    global llm_client, demand_explorer

    try:
        provider_enum = LLMProvider(provider)

        # Update global components
        llm_client = LLMClient(
            provider=provider_enum,
            api_key=api_key,
            endpoint=endpoint,
            model=model
        )
        demand_explorer = DemandExplorer(llm_client)

        return f"LLM configuration updated: {provider} with model {llm_client.model}"

    except ValueError as e:
        return f"Error: Invalid provider '{provider}'. Supported: openai, ollama, anthropic, azure_openai"


@mcp.resource("config://server.json")
async def get_server_config() -> str:
    """Get current server configuration"""
    return json.dumps({
        "server_name": "united-airlines-demand-explorer",
        "version": "1.0.0",
        "llm_provider": llm_client.provider.value if llm_client else "not_configured",
        "llm_model": llm_client.model if llm_client else "not_configured",
        "max_articles_per_request": 100,
        "supported_sources": ["Google News RSS"],
        "analysis_capabilities": [
            "Route-specific demand analysis",
            "Event impact assessment",
            "Flexible timeframe analysis",
            "Multi-LLM provider support"
        ]
    }, indent=2)


@mcp.resource("help://usage.md")
async def get_usage_guide() -> str:
    """Get usage guide for the demand explorer"""
    return """# United Airlines Demand Explorer Usage Guide

## Available Tools

### 1. analyze_route_demand
Analyzes demand factors for specific airline routes.

**Example usage:**
```python
# Analyze Chicago to NYC demand over past 2 weeks
analyze_route_demand(
    origin="Chicago", 
    destination="New York",
    days_back=14,
    context="business travel"
)

# Analyze specific date range
analyze_route_demand(
    origin="LAX",
    destination="SFO", 
    start_date="2024-12-01",
    end_date="2024-12-15"
)
```

### 2. explore_demand_events
Explores specific types of demand-affecting events.

**Example usage:**
```python
explore_demand_events(
    location="Chicago",
    event_types=["concerts", "sports"],
    timeframe="past_month"
)
```

### 3. configure_llm
Configure the LLM provider and settings.

**Example usage:**
```python
configure_llm(
    provider="openai",
    model="gpt-4o-mini",
    api_key="your-api-key"
)
```

## Tips for Better Results

1. Be specific with city names and airport codes
2. Use relevant context terms for better search results
3. Consider both origin and destination events
4. The system automatically categorizes events by demand impact

## Supported Event Types

- **Positive Impact**: Concerts, festivals, conferences, sports events
- **Negative Impact**: Protests, strikes, weather disruptions
- **Mixed Impact**: Economic events, transport disruptions

## Configuration

Default: OpenAI GPT-4o-mini
Supported: OpenAI, Ollama, Anthropic, Azure OpenAI
"""


if __name__ == "__main__":
    mcp.run()