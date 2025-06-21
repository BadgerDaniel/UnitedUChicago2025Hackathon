import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List, Literal
from enum import Enum
import aiohttp
import feedparser
from urllib.parse import quote_plus
from dateutil import parser as date_parser
from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


mcp = FastMCP("united-airlines-demand-explorer")


class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"


class DemandImpactType(Enum):
    """Types of demand impact events"""
    POSITIVE = "positive"  # Increases demand
    NEGATIVE = "negative"  # Decreases demand
    NEUTRAL = "neutral"  # No significant impact
    MIXED = "mixed"  # Mixed impact


class LLMClient:
    """Modular LLM client supporting multiple providers"""

    def __init__(self, provider: LLMProvider, api_key: Optional[str] = None,
                 endpoint: Optional[str] = None, model: Optional[str] = None):
        self.provider = provider
        self.api_key = api_key
        self.endpoint = endpoint
        self.model = model or self._get_default_model()

    def _get_default_model(self) -> str:
        """Get default model for each provider"""
        defaults = {
            LLMProvider.OPENAI: "gpt-4o-mini",
            LLMProvider.OLLAMA: "llama3.2",
            LLMProvider.ANTHROPIC: "claude-3-sonnet-20240229",
            LLMProvider.AZURE_OPENAI: "gpt-4o-mini"
        }
        return defaults.get(self.provider, "gpt-4o-mini")

    def _get_default_endpoint(self) -> str:
        """Get default endpoint for each provider"""
        endpoints = {
            LLMProvider.OPENAI: "https://api.openai.com/v1/chat/completions",
            LLMProvider.OLLAMA: "http://localhost:11434/api/generate",
            LLMProvider.ANTHROPIC: "https://api.anthropic.com/v1/messages",
            LLMProvider.AZURE_OPENAI: None  # Requires custom endpoint
        }
        return self.endpoint or endpoints.get(self.provider)

    async def generate_analysis(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate analysis using the configured LLM provider"""
        try:
            if self.provider == LLMProvider.OPENAI:
                return await self._call_openai(prompt, system_prompt)
            elif self.provider == LLMProvider.OLLAMA:
                return await self._call_ollama(prompt)
            elif self.provider == LLMProvider.ANTHROPIC:
                return await self._call_anthropic(prompt, system_prompt)
            elif self.provider == LLMProvider.AZURE_OPENAI:
                return await self._call_azure_openai(prompt, system_prompt)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
        except Exception as e:
            logger.error(f"Error calling {self.provider.value}: {str(e)}")
            return f"Error during analysis: {str(e)}"

    async def _call_openai(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Call OpenAI API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 4000
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self._get_default_endpoint(), headers=headers, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    error_text = await response.text()
                    return f"OpenAI API error {response.status}: {error_text}"

    async def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_ctx": 4096
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self._get_default_endpoint(), json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('response', 'No analysis available')
                else:
                    return f"Ollama API error: {response.status}"

    async def _call_anthropic(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Call Anthropic API"""
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }

        payload = {
            "model": self.model,
            "max_tokens": 4000,
            "temperature": 0.1,
            "messages": [{"role": "user", "content": prompt}]
        }

        if system_prompt:
            payload["system"] = system_prompt

        async with aiohttp.ClientSession() as session:
            async with session.post(self._get_default_endpoint(), headers=headers, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["content"][0]["text"]
                else:
                    error_text = await response.text()
                    return f"Anthropic API error {response.status}: {error_text}"

    async def _call_azure_openai(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Call Azure OpenAI API"""
        if not self.endpoint:
            return "Azure OpenAI endpoint not configured"

        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 4000
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.endpoint, headers=headers, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    error_text = await response.text()
                    return f"Azure OpenAI API error {response.status}: {error_text}"


class DemandExplorer:
    """Enhanced demand analysis for United Airlines routes"""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def parse_article_date(self, date_string: str) -> Optional[datetime]:
        """Parse article date string into datetime object"""
        if not date_string:
            return None
        try:
            return date_parser.parse(date_string)
        except Exception as e:
            logger.warning(f"Could not parse date '{date_string}': {e}")
            return None

    async def scrape_news_flexible_timeframe(self,
                                             search_terms: List[str],
                                             start_date: Optional[datetime] = None,
                                             end_date: Optional[datetime] = None,
                                             days_back: Optional[int] = None,
                                             max_articles: int = 100) -> List[Dict]:
        """
        Flexible news scraping with multiple timeframe options
        """
        # Determine date range
        if days_back:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
        elif not start_date or not end_date:
            # Default to last 7 days if no dates specified
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)

        all_articles = []

        for term in search_terms:
            try:
                encoded_term = quote_plus(term)
                url = f"https://news.google.com/rss/search?q={encoded_term}&hl=en-US&gl=US&ceid=US:en"

                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            content = await response.text()
                            feed = feedparser.parse(content)

                            for entry in feed.entries[:max_articles]:
                                article_date = self.parse_article_date(entry.get('published', ''))

                                # Filter by date range
                                if article_date and start_date <= article_date <= end_date:
                                    all_articles.append({
                                        'title': entry.title,
                                        'link': entry.link,
                                        'published': entry.get('published', ''),
                                        'published_datetime': article_date,
                                        'summary': entry.get('summary', ''),
                                        'source': entry.get('source', {}).get('title', 'Unknown'),
                                        'search_term': term
                                    })

            except Exception as e:
                logger.error(f"Error scraping news for '{term}': {str(e)}")

        # Remove duplicates and sort by date
        seen_titles = set()
        unique_articles = []
        for article in all_articles:
            if article['title'] not in seen_titles:
                seen_titles.add(article['title'])
                unique_articles.append(article)

        unique_articles.sort(key=lambda x: x['published_datetime'], reverse=True)

        logger.info(
            f"Found {len(unique_articles)} unique articles from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        return unique_articles

    def generate_route_search_terms(self, origin: str, destination: str, route_context: str = "") -> List[str]:
        """Generate comprehensive search terms for a specific route"""
        base_terms = [
            f"{origin} {destination}",
            f"{origin} to {destination}",
            f"flights {origin} {destination}",
        ]

        # Add context-specific terms
        context_terms = []
        if route_context:
            context_terms.extend([
                f"{route_context} {origin}",
                f"{route_context} {destination}",
                f"events {origin}",
                f"events {destination}",
            ])

        # Add demand-affecting event categories
        event_terms = [
            f"concerts {origin}",
            f"concerts {destination}",
            f"sports {origin}",
            f"sports {destination}",
            f"conference {origin}",
            f"conference {destination}",
            f"festival {origin}",
            f"festival {destination}",
            f"protest {origin}",
            f"protest {destination}",
            f"weather {origin}",
            f"weather {destination}",
            f"strike {origin}",
            f"strike {destination}",
        ]

        return base_terms + context_terms + event_terms

    async def analyze_route_demand_impact(self,
                                          origin: str,
                                          destination: str,
                                          start_date: Optional[datetime] = None,
                                          end_date: Optional[datetime] = None,
                                          days_back: Optional[int] = None,
                                          context: str = "") -> str:
        """Analyze demand impact for a specific airline route"""

        search_terms = self.generate_route_search_terms(origin, destination, context)
        articles = await self.scrape_news_flexible_timeframe(
            search_terms, start_date, end_date, days_back
        )

        if not articles:
            date_range = f"last {days_back} days" if days_back else f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
            return f"No relevant articles found for {origin} to {destination} route in the {date_range}"

        # Group articles by category and date
        articles_by_category = self._categorize_articles(articles)
        articles_by_date = self._group_by_date(articles)

        # Generate comprehensive analysis prompt
        system_prompt = """You are an airline demand analyst specializing in route-specific demand forecasting. 
        Analyze news articles to identify events, trends, and factors that could impact passenger demand for specific airline routes.
        Focus on: concerts, sports events, conferences, festivals, weather disruptions, strikes, protests, economic factors, and seasonal patterns.
        Categorize impact as: POSITIVE (increases demand), NEGATIVE (decreases demand), NEUTRAL, or MIXED."""

        analysis_prompt = self._build_route_analysis_prompt(
            origin, destination, articles, articles_by_category, articles_by_date,
            start_date, end_date, days_back
        )

        return await self.llm_client.generate_analysis(analysis_prompt, system_prompt)

    def _categorize_articles(self, articles: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize articles by likely demand impact type"""
        categories = {
            'events_positive': [],  # Concerts, festivals, conferences
            'events_negative': [],  # Protests, strikes, disasters
            'weather': [],
            'sports': [],
            'economic': [],
            'transport': [],  # Flight delays, airport issues
            'other': []
        }

        for article in articles:
            title_lower = article['title'].lower()
            summary_lower = article.get('summary', '').lower()
            text = f"{title_lower} {summary_lower}"

            if any(term in text for term in ['concert', 'festival', 'conference', 'convention', 'expo']):
                categories['events_positive'].append(article)
            elif any(term in text for term in ['protest', 'strike', 'riot', 'violence', 'disaster']):
                categories['events_negative'].append(article)
            elif any(term in text for term in ['weather', 'storm', 'hurricane', 'snow', 'rain']):
                categories['weather'].append(article)
            elif any(term in text for term in ['game', 'match', 'championship', 'tournament', 'sports']):
                categories['sports'].append(article)
            elif any(term in text for term in ['price', 'cost', 'economic', 'inflation', 'recession']):
                categories['economic'].append(article)
            elif any(term in text for term in ['flight', 'airport', 'airline', 'delay', 'cancellation']):
                categories['transport'].append(article)
            else:
                categories['other'].append(article)

        return categories

    def _group_by_date(self, articles: List[Dict]) -> Dict[str, List[Dict]]:
        """Group articles by date"""
        by_date = {}
        for article in articles:
            if article.get('published_datetime'):
                date_key = article['published_datetime'].strftime('%Y-%m-%d')
                if date_key not in by_date:
                    by_date[date_key] = []
                by_date[date_key].append(article)
        return by_date

    def _build_route_analysis_prompt(self, origin: str, destination: str,
                                     articles: List[Dict], categories: Dict,
                                     by_date: Dict, start_date: Optional[datetime],
                                     end_date: Optional[datetime], days_back: Optional[int]) -> str:
        """Build comprehensive analysis prompt for route demand"""

        date_range = f"last {days_back} days" if days_back else f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"

        # Build category summary
        category_summary = []
        for category, cat_articles in categories.items():
            if cat_articles:
                category_summary.append(f"- {category.replace('_', ' ').title()}: {len(cat_articles)} articles")

        # Build date distribution
        date_distribution = []
        for date_key in sorted(by_date.keys(), reverse=True):
            date_distribution.append(f"- {date_key}: {len(by_date[date_key])} articles")

        # Build article details
        article_details = []
        for article in articles[:50]:  # Limit for token management
            article_details.append(
                f"Title: {article['title']}\n"
                f"Source: {article['source']}\n"
                f"Date: {article['published']}\n"
                f"Summary: {article['summary']}\n"
                f"Search Term: {article['search_term']}\n"
            )

        prompt = f"""
UNITED AIRLINES ROUTE DEMAND ANALYSIS
=====================================

ROUTE: {origin} ↔ {destination}
TIME PERIOD: {date_range}
TOTAL ARTICLES: {len(articles)}

ARTICLE CATEGORIES:
{chr(10).join(category_summary)}

DATE DISTRIBUTION:
{chr(10).join(date_distribution)}

DETAILED ARTICLES:
{'=' * 50}
{chr(10).join(article_details)}

ANALYSIS REQUIREMENTS:
======================

1. DEMAND IMPACT ASSESSMENT:
   - Identify specific events/factors that could INCREASE demand (concerts, sports, conferences, positive economic news)
   - Identify specific events/factors that could DECREASE demand (strikes, protests, weather disruptions, negative economic factors)
   - Assess the magnitude and timing of these impacts

2. TEMPORAL ANALYSIS:
   - Timeline of events and their likely impact periods
   - Seasonal or recurring patterns
   - Future demand implications based on scheduled events

3. ROUTE-SPECIFIC INSIGHTS:
   - How events in {origin} affect outbound demand
   - How events in {destination} affect inbound demand
   - Connecting traffic implications

4. DEMAND FORECASTING INSIGHTS:
   - Short-term demand predictions (next 1-4 weeks)
   - Medium-term considerations (1-6 months)
   - Risk factors and opportunities

5. ACTIONABLE RECOMMENDATIONS:
   - Pricing strategy implications
   - Capacity planning considerations
   - Marketing opportunities
   - Risk mitigation strategies

Please provide a structured analysis with specific examples from the articles and quantify confidence levels where possible.
"""

        return prompt


# Initialize components - declare globals first
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