import logging
from datetime import datetime
from dateutil import parser as date_parser
from typing import Dict, List, Optional

from llm import LLMClient, LLMProvider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedditExplorer:
    """Demand analysis for City subreddits"""

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
    demand_explorer = RedditExplorer(llm_client)


# Initialize on startup
initialize_components()