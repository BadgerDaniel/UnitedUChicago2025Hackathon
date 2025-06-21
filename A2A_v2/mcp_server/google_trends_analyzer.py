"""
Improved Google Trends integration for travel analysis.
Uses multiple approaches to handle Google's anti-bot measures.
"""

import requests
import time
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, List, Optional
import logging
import random

logger = logging.getLogger(__name__)

class GoogleTrendsAnalyzer:
    """Analyzes Google Trends data for travel-related insights with improved scraping."""
    
    # Major airport DMAs mapping
    AIRPORT_DMA_MAP = {
        "atlanta": {"dma_code": 524, "airport": "ATL", "city": "Atlanta"},
        "los angeles": {"dma_code": 803, "airport": "LAX", "city": "Los Angeles"},
        "dallas": {"dma_code": 623, "airport": "DFW", "city": "Dallas"},
        "denver": {"dma_code": 751, "airport": "DEN", "city": "Denver"},
        "chicago": {"dma_code": 602, "airport": "ORD", "city": "Chicago"},
        "orlando": {"dma_code": 534, "airport": "MCO", "city": "Orlando"},
        "charlotte": {"dma_code": 517, "airport": "CLT", "city": "Charlotte"},
        "las vegas": {"dma_code": 839, "airport": "LAS", "city": "Las Vegas"},
        "seattle": {"dma_code": 819, "airport": "SEA", "city": "Seattle"},
        "miami": {"dma_code": 528, "airport": "MIA", "city": "Miami"},
        "phoenix": {"dma_code": 753, "airport": "PHX", "city": "Phoenix"},
        "san francisco": {"dma_code": 807, "airport": "SFO", "city": "San Francisco"},
        "new york": {"dma_code": 501, "airport": "JFK/LGA/EWR", "city": "New York"},
        "houston": {"dma_code": 618, "airport": "IAH", "city": "Houston"},
        "boston": {"dma_code": 506, "airport": "BOS", "city": "Boston"}
    }
    
    # Travel-related keywords that might indicate increased demand
    TRAVEL_KEYWORDS = [
        "flight", "flights", "travel", "vacation", "hotel", "airline", "airport",
        "trip", "booking", "tickets", "holiday", "cruise", "resort", "airfare",
        "cheap flights", "flight deals", "travel deals", "weekend getaway"
    ]
    
    # Event-related keywords that drive travel
    EVENT_KEYWORDS = [
        "concert", "festival", "conference", "convention", "game", "sports",
        "championship", "playoffs", "world series", "super bowl", "olympics",
        "comic con", "expo", "trade show", "marathon", "tournament"
    ]
    
    def __init__(self):
        self.base_urls = [
            "https://trends.google.com/trending?geo={dma}&hours=24&sort=search-volume",
            "https://trends.google.com/trending/trendingsearches/daily?geo={geo}&hl=en",
        ]
        self.session = requests.Session()
        
        # Rotate through different user agents to avoid detection
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
        
        self.update_session_headers()
    
    def update_session_headers(self):
        """Update session headers with random user agent and other headers."""
        self.session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
    
    def get_city_dma_code(self, city: str) -> Optional[Dict]:
        """Get DMA code for a city."""
        city_key = city.lower().strip()
        
        # Direct match
        if city_key in self.AIRPORT_DMA_MAP:
            return self.AIRPORT_DMA_MAP[city_key]
        
        # Partial match
        for key, data in self.AIRPORT_DMA_MAP.items():
            if city_key in key or key in city_key:
                return data
        
        return None
    
    async def scrape_trending_topics_multiple_approaches(self, city: str) -> List[Dict]:
        """Try multiple approaches to scrape trending topics."""
        dma_info = self.get_city_dma_code(city)
        if not dma_info:
            logger.warning(f"No DMA mapping found for city: {city}")
            return self._get_fallback_trends(city)
        
        # Try different approaches
        approaches = [
            self._approach_1_dma_trends,
            self._approach_2_geo_trends,
            self._approach_3_alternative_selectors
        ]
        
        for i, approach in enumerate(approaches):
            try:
                logger.info(f"Trying approach {i+1} for {city}")
                trends = await approach(dma_info, city)
                if trends:
                    logger.info(f"Approach {i+1} succeeded with {len(trends)} trends")
                    return trends
                else:
                    logger.info(f"Approach {i+1} returned no trends")
            except Exception as e:
                logger.warning(f"Approach {i+1} failed for {city}: {e}")
                continue
        
        # If all approaches fail, return fallback data
        logger.warning(f"All approaches failed for {city}, using fallback")
        return self._get_fallback_trends(city)
    
    async def _approach_1_dma_trends(self, dma_info: Dict, city: str) -> List[Dict]:
        """Approach 1: Use DMA-specific trends URL."""
        dma_code = dma_info["dma_code"]
        url = f"https://trends.google.com/trending?geo={dma_code}&hours=24&sort=search-volume"
        
        self.update_session_headers()
        
        # Add random delay
        # await asyncio.sleep(random.uniform(2, 5))
        await asyncio.sleep(13)
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: self.session.get(url, timeout=15)
        )
        
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}")
        
        return self._parse_trends_from_html(response.text, dma_info, city)
    
    async def _approach_2_geo_trends(self, dma_info: Dict, city: str) -> List[Dict]:
        """Approach 2: Use geographic code trends."""
        # Map DMA to country/state codes
        geo_code = "US"  # Default to US
        url = f"https://trends.google.com/trending/trendingsearches/daily?geo={geo_code}&hl=en"
        
        self.update_session_headers()
        await asyncio.sleep(random.uniform(3, 6))
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: self.session.get(url, timeout=15)
        )
        
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}")
        
        return self._parse_trends_from_html(response.text, dma_info, city)
    
    async def _approach_3_alternative_selectors(self, dma_info: Dict, city: str) -> List[Dict]:
        """Approach 3: Try alternative CSS selectors and parsing."""
        dma_code = dma_info["dma_code"]
        url = f"https://trends.google.com/trending?geo={dma_code}"
        
        self.update_session_headers()
        await asyncio.sleep(random.uniform(4, 7))
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: self.session.get(url, timeout=20)
        )
        
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}")
        
        # Try multiple parsing approaches
        return self._parse_with_alternative_methods(response.text, dma_info, city)
    
    def _parse_trends_from_html(self, html_content: str, dma_info: Dict, city: str) -> List[Dict]:
        """Parse trends from HTML using multiple selector strategies."""
        soup = BeautifulSoup(html_content, "html.parser")
        trends = []
        
        # Multiple selector strategies
        selector_strategies = [
            ("div", {"class": "title"}),
            ("div", {"class": "trending-title"}),
            ("span", {"class": "trending-search"}),
            ("div", {"class": "trending-search-title"}),
            ("h3", {}),  # Generic h3 tags
            ("a", {"class": "trending-search-link"}),
            ("[data-testid*='trend']", {}),  # Modern data-testid attributes
        ]
        
        for tag, attrs in selector_strategies:
            try:
                if tag.startswith("["):
                    # CSS selector for data attributes
                    elements = soup.select(tag)
                else:
                    elements = soup.find_all(tag, attrs) if attrs else soup.find_all(tag)
                
                for element in elements[:20]:  # Limit to 20
                    trend_text = element.get_text(strip=True)
                    if trend_text and len(trend_text) > 2 and len(trend_text) < 100:
                        trends.append({
                            "trend": trend_text,
                            "city": dma_info["city"],
                            "dma_code": dma_info["dma_code"],
                            "scraped_at": datetime.now().isoformat(),
                            "method": f"{tag}_{attrs.get('class', 'no_class')}"
                        })
                
                if trends:
                    logger.info(f"Found {len(trends)} trends using {tag} selector")
                    break
                    
            except Exception as e:
                logger.debug(f"Selector {tag} failed: {e}")
                continue
        
        return trends
    
    def _parse_with_alternative_methods(self, html_content: str, dma_info: Dict, city: str) -> List[Dict]:
        """Try alternative parsing methods including text search."""
        trends = []
        
        # First try standard parsing
        trends = self._parse_trends_from_html(html_content, dma_info, city)
        if trends:
            return trends
        
        # If that fails, try text-based extraction
        try:
            # Look for JSON data in script tags
            soup = BeautifulSoup(html_content, "html.parser")
            script_tags = soup.find_all("script")
            
            for script in script_tags:
                script_text = script.get_text()
                if "trending" in script_text.lower() and "{" in script_text:
                    # Try to extract trends from JavaScript data
                    # This is a simplified approach - in practice, you'd need more sophisticated JSON extraction
                    import re
                    trend_matches = re.findall(r'"title":\s*"([^"]+)"', script_text)
                    
                    for match in trend_matches[:10]:
                        trends.append({
                            "trend": match,
                            "city": dma_info["city"],
                            "dma_code": dma_info["dma_code"],
                            "scraped_at": datetime.now().isoformat(),
                            "method": "json_extraction"
                        })
                    
                    if trends:
                        logger.info(f"Extracted {len(trends)} trends from JSON data")
                        break
        
        except Exception as e:
            logger.debug(f"JSON extraction failed: {e}")
        
        return trends
    
    def _get_fallback_trends(self, city: str) -> List[Dict]:
        """Provide realistic fallback trending topics when scraping fails."""
        # City-specific fallback topics that might realistically be trending
        city_fallbacks = {
            "las vegas": [
                "weekend shows", "casino deals", "buffet specials", "convention center events", "pool parties"
            ],
            "miami": [
                "beach weather", "art basel", "nightlife", "cruise deals", "south beach events"
            ],
            "new york": [
                "broadway shows", "restaurant week", "museum exhibitions", "yankees", "fashion week"
            ],
            "chicago": [
                "winter weather", "bulls games", "deep dish pizza", "millennium park", "cubs tickets"
            ],
            "los angeles": [
                "hollywood events", "lakers games", "beach conditions", "traffic updates", "concert venues"
            ]
        }
        
        city_key = city.lower()
        fallback_topics = city_fallbacks.get(city_key, ["local events", "weather updates", "traffic", "restaurants", "entertainment"])
        
        trends = []
        for topic in fallback_topics:
            trends.append({
                "trend": topic,
                "city": city.title(),
                "dma_code": 0,  # Indicate this is fallback data
                "scraped_at": datetime.now().isoformat(),
                "method": "fallback"
            })
        
        logger.info(f"Using fallback trends for {city}: {len(trends)} topics")
        return trends
    
    async def scrape_trending_topics(self, city: str) -> List[Dict]:
        """Main method to scrape trending topics with fallback support."""
        return await self.scrape_trending_topics_multiple_approaches(city)
    
    def analyze_travel_relevance(self, trends: List[Dict]) -> Dict:
        """Analyze how trending topics relate to travel demand."""
        if not trends:
            return {
                "travel_impact_score": 3.0,  # Changed from 1.0 to 3.0 for unknown
                "event_impact_score": 3.0,   # Conservative estimate when no data
                "relevant_trends": [],
                "analysis": "No trending data available - using conservative estimates"
            }
        
        # Check if we're using fallback data
        is_fallback = all(trend.get("method") == "fallback" for trend in trends)
        
        travel_related = []
        event_related = []
        other_trends = []
        
        for trend in trends:
            trend_text = trend["trend"].lower()
            
            # Check for travel keywords
            if any(keyword in trend_text for keyword in self.TRAVEL_KEYWORDS):
                travel_related.append(trend)
            # Check for event keywords
            elif any(keyword in trend_text for keyword in self.EVENT_KEYWORDS):
                event_related.append(trend)
            else:
                other_trends.append(trend)
        
        # Calculate impact scores with fallback adjustment
        if is_fallback:
            # More conservative scoring for fallback data
            travel_impact = 3.0 + (len(travel_related) * 0.5)
            event_impact = 3.0 + (len(event_related) * 0.7)
        else:
            # Normal scoring for real data
            travel_impact = 1.0 + (len(travel_related) * 0.8)
            event_impact = 1.0 + (len(event_related) * 1.2)
        
        travel_impact = min(travel_impact, 10.0)
        event_impact = min(event_impact, 10.0)
        
        # Additional analysis for high-impact trends
        analysis_parts = []
        
        if is_fallback:
            analysis_parts.append("Using fallback trending topics due to scraping limitations")
        
        if travel_related:
            analysis_parts.append(f"Travel interest detected: {len(travel_related)} travel-related trends")
        
        if event_related:
            analysis_parts.append(f"Event activity detected: {len(event_related)} event-related trends")
        
        # Look for specific high-impact indicators
        all_trend_text = " ".join([t["trend"].lower() for t in trends])
        
        if "hurricane" in all_trend_text or "storm" in all_trend_text:
            travel_impact = min(travel_impact + 2.0, 10.0)
            analysis_parts.append("Weather emergency trending - potential flight disruptions")
        
        if "strike" in all_trend_text and "airline" in all_trend_text:
            travel_impact = min(travel_impact + 3.0, 10.0)
            analysis_parts.append("Airline strike trending - major travel disruption expected")
        
        if any(word in all_trend_text for word in ["championship", "finals", "playoffs", "super bowl"]):
            event_impact = min(event_impact + 2.0, 10.0)
            analysis_parts.append("Major sporting event trending - increased travel demand")
        
        return {
            "travel_impact_score": round(travel_impact, 1),
            "event_impact_score": round(event_impact, 1),
            "travel_related_trends": travel_related,
            "event_related_trends": event_related,
            "total_trends_analyzed": len(trends),
            "is_fallback_data": is_fallback,
            "analysis": "; ".join(analysis_parts) if analysis_parts else "Normal activity detected",
            "top_trends": [t["trend"] for t in trends[:5]]
        }
    
    async def get_travel_insights_for_city(self, city: str) -> str:
        """Get comprehensive travel insights based on trending topics."""
        trends = await self.scrape_trending_topics(city)
        analysis = self.analyze_travel_relevance(trends)
        
        # Format the response
        city_name = city.title()
        travel_score = analysis["travel_impact_score"]
        event_score = analysis["event_impact_score"]
        is_fallback = analysis.get("is_fallback_data", False)
        
        response = f"Google Trends Analysis for {city_name}:\n"
        
        if is_fallback:
            response += "⚠️  Note: Using fallback data due to Google Trends access limitations\n"
        
        response += f"Travel Impact Score: {travel_score}/10\n"
        response += f"Event Impact Score: {event_score}/10\n"
        response += f"Analysis: {analysis['analysis']}\n"
        
        if analysis["top_trends"]:
            response += f"Trending Topics: {', '.join(analysis['top_trends'][:3])}\n"
        
        if analysis["travel_related_trends"]:
            response += f"Travel-Related Trends: {len(analysis['travel_related_trends'])} detected\n"
        
        if analysis["event_related_trends"]:
            response += f"Event-Related Trends: {len(analysis['event_related_trends'])} detected\n"
        
        # Add interpretation
        if travel_score >= 7 or event_score >= 7:
            response += "🚨 HIGH IMPACT: Significant travel demand/disruption factors detected"
        elif travel_score >= 5 or event_score >= 5:
            response += "⚠️ MODERATE IMPACT: Some factors may affect travel demand"
        else:
            response += "✅ NORMAL ACTIVITY: Typical trending patterns with minimal travel impact"
        
        return response

# Global instance
trends_analyzer = GoogleTrendsAnalyzer()
