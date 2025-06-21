"""
Alternative Google Trends implementation using realistic mock data.
This approach provides reliable trending insights without scraping limitations.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import random

logger = logging.getLogger(__name__)

class MockGoogleTrendsAnalyzer:
    """Provides realistic trending data based on seasonal patterns and current events."""
    
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
    
    # Seasonal trending patterns by month
    SEASONAL_TRENDS = {
        1: ["new year travel deals", "winter vacation", "ski resorts", "warm weather destinations", "hotel booking"],
        2: ["valentine's day getaway", "winter escape", "spring break planning", "cruise deals", "warm destinations"],
        3: ["spring break", "march madness travel", "easter vacation", "flight deals", "hotel reservations"],
        4: ["spring vacation", "easter travel", "cherry blossoms", "national parks", "camping reservations"],
        5: ["summer planning", "memorial day weekend", "graduation trips", "family vacation", "beach destinations"],
        6: ["summer vacation", "father's day weekend", "music festivals", "camping", "road trips"],
        7: ["summer travel peak", "july 4th weekend", "beach vacation", "amusement parks", "family trips"],
        8: ["back to school travel", "summer finale", "labor day planning", "last minute deals", "festival season"],
        9: ["fall travel", "labor day weekend", "oktoberfest", "leaf peeping", "harvest festivals"],
        10: ["halloween events", "fall foliage", "october festivals", "conference season", "business travel"],
        11: ["thanksgiving travel", "black friday deals", "winter planning", "holiday booking", "family visits"],
        12: ["holiday travel", "christmas vacation", "new year planning", "winter destinations", "year end trips"]
    }
    
    # City-specific trending topics
    CITY_SPECIFIC_TRENDS = {
        "las vegas": {
            "base": ["casino shows", "buffet deals", "pool parties", "convention events", "entertainment"],
            "high_impact": ["major concert", "championship fight", "tech conference", "new year's eve", "march madness"],
            "travel": ["vegas flights", "hotel deals", "show tickets", "weekend packages", "group bookings"]
        },
        "miami": {
            "base": ["beach weather", "nightlife", "art basel", "cruise deals", "south beach"],
            "high_impact": ["ultra music festival", "art basel miami", "super bowl", "spring break", "hurricane season"],
            "travel": ["miami flights", "beach resorts", "cruise departures", "art basel hotels", "nightlife packages"]
        },
        "new york": {
            "base": ["broadway shows", "restaurant week", "museums", "central park", "shopping"],
            "high_impact": ["fashion week", "marathon", "new year's eve", "9/11 memorial", "thanksgiving parade"],
            "travel": ["nyc hotels", "broadway tickets", "flight deals", "weekend packages", "city tours"]
        },
        "chicago": {
            "base": ["deep dish pizza", "architecture", "millennium park", "blues music", "lakefront"],
            "high_impact": ["lollapalooza", "marathon", "cubs playoffs", "winter weather", "food festivals"],
            "travel": ["chicago flights", "hotel deals", "cubs tickets", "food tours", "architecture tours"]
        },
        "orlando": {
            "base": ["disney world", "universal studios", "theme parks", "family vacation", "attractions"],
            "high_impact": ["disney special events", "halloween horror nights", "spring break", "christmas events", "new attractions"],
            "travel": ["disney packages", "theme park tickets", "family deals", "resort booking", "vacation packages"]
        },
        "seattle": {
            "base": ["coffee culture", "pike place market", "music scene", "tech companies", "outdoor activities"],
            "high_impact": ["seahawks games", "music festivals", "tech conferences", "cherry blossoms", "salmon season"],
            "travel": ["seattle flights", "coffee tours", "tech events", "outdoor packages", "music venue tickets"]
        }
    }
    
    # Travel and event keywords for analysis
    TRAVEL_KEYWORDS = [
        "flight", "flights", "travel", "vacation", "hotel", "airline", "airport",
        "trip", "booking", "tickets", "holiday", "cruise", "resort", "airfare",
        "deals", "packages", "weekend getaway", "destination"
    ]
    
    EVENT_KEYWORDS = [
        "concert", "festival", "conference", "convention", "game", "sports",
        "championship", "playoffs", "marathon", "show", "exhibition", "fair"
    ]
    
    def __init__(self):
        self.current_month = datetime.now().month
        self.current_day = datetime.now().day
    
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
    
    def _generate_seasonal_trends(self) -> List[str]:
        """Generate trending topics based on current season."""
        base_trends = self.SEASONAL_TRENDS.get(self.current_month, ["travel", "vacation", "booking"])
        
        # Add some randomization
        selected_trends = random.sample(base_trends, min(3, len(base_trends)))
        
        return selected_trends
    
    def _generate_city_specific_trends(self, city: str) -> List[str]:
        """Generate city-specific trending topics."""
        city_key = city.lower()
        city_trends = self.CITY_SPECIFIC_TRENDS.get(city_key, {})
        
        if not city_trends:
            return ["local events", "weather", "restaurants", "attractions"]
        
        # Mix base trends with occasional high-impact trends
        trends = []
        
        # Always include some base trends
        base_trends = city_trends.get("base", [])
        trends.extend(random.sample(base_trends, min(3, len(base_trends))))
        
        # Occasionally include high-impact trends (20% chance)
        if random.random() < 0.2:
            high_impact = city_trends.get("high_impact", [])
            if high_impact:
                trends.append(random.choice(high_impact))
        
        # Sometimes include travel-specific trends (30% chance)
        if random.random() < 0.3:
            travel_trends = city_trends.get("travel", [])
            if travel_trends:
                trends.extend(random.sample(travel_trends, min(2, len(travel_trends))))
        
        return trends
    
    def _generate_realistic_trends(self, city: str) -> List[Dict]:
        """Generate realistic trending topics for a city."""
        dma_info = self.get_city_dma_code(city)
        if not dma_info:
            dma_info = {"dma_code": 0, "city": city.title(), "airport": "Unknown"}
        
        # Combine seasonal and city-specific trends
        trends = []
        
        # Add seasonal trends
        seasonal = self._generate_seasonal_trends()
        for trend in seasonal:
            trends.append({
                "trend": trend,
                "city": dma_info["city"],
                "dma_code": dma_info["dma_code"],
                "scraped_at": datetime.now().isoformat(),
                "method": "seasonal_mock",
                "category": "seasonal"
            })
        
        # Add city-specific trends
        city_specific = self._generate_city_specific_trends(city)
        for trend in city_specific:
            trends.append({
                "trend": trend,
                "city": dma_info["city"],
                "dma_code": dma_info["dma_code"],
                "scraped_at": datetime.now().isoformat(),
                "method": "city_mock",
                "category": "city_specific"
            })
        
        # Add some general trending topics
        general_topics = [
            "weekend plans", "restaurant reservations", "weather forecast", 
            "traffic updates", "local news", "sports scores", "movie showtimes"
        ]
        
        for topic in random.sample(general_topics, 3):
            trends.append({
                "trend": topic,
                "city": dma_info["city"],
                "dma_code": dma_info["dma_code"],
                "scraped_at": datetime.now().isoformat(),
                "method": "general_mock",
                "category": "general"
            })
        
        logger.info(f"Generated {len(trends)} mock trending topics for {city}")
        return trends
    
    async def scrape_trending_topics(self, city: str) -> List[Dict]:
        """Generate realistic trending topics (mock implementation)."""
        # Add a small delay to simulate API call
        await asyncio.sleep(0.5)
        
        return self._generate_realistic_trends(city)
    
    def analyze_travel_relevance(self, trends: List[Dict]) -> Dict:
        """Analyze how trending topics relate to travel demand."""
        if not trends:
            return {
                "travel_impact_score": 3.0,
                "event_impact_score": 3.0,
                "relevant_trends": [],
                "analysis": "No trending data available - using conservative estimates"
            }
        
        travel_related = []
        event_related = []
        high_impact_trends = []
        
        for trend in trends:
            trend_text = trend["trend"].lower()
            
            # Check for travel keywords
            if any(keyword in trend_text for keyword in self.TRAVEL_KEYWORDS):
                travel_related.append(trend)
            
            # Check for event keywords
            if any(keyword in trend_text for keyword in self.EVENT_KEYWORDS):
                event_related.append(trend)
            
            # Check for high-impact indicators
            if trend.get("category") == "city_specific" and any(word in trend_text for word in 
                ["concert", "festival", "championship", "super bowl", "new year", "spring break"]):
                high_impact_trends.append(trend)
        
        # Calculate impact scores based on trending patterns
        base_travel_impact = 3.0  # Start with moderate baseline
        base_event_impact = 3.0
        
        # Adjust based on travel-related trends
        travel_impact = base_travel_impact + (len(travel_related) * 0.8)
        
        # Adjust based on event-related trends
        event_impact = base_event_impact + (len(event_related) * 1.0)
        
        # Boost for high-impact trends
        if high_impact_trends:
            travel_impact += len(high_impact_trends) * 1.5
            event_impact += len(high_impact_trends) * 1.2
        
        # Add seasonal adjustments
        current_month = datetime.now().month
        if current_month in [6, 7, 8]:  # Summer peak
            travel_impact += 1.0
        elif current_month in [11, 12]:  # Holiday season
            travel_impact += 1.5
            event_impact += 1.0
        elif current_month in [3, 4]:  # Spring break season
            travel_impact += 1.2
        
        # Cap at 10.0
        travel_impact = min(travel_impact, 10.0)
        event_impact = min(event_impact, 10.0)
        
        # Generate analysis text
        analysis_parts = []
        analysis_parts.append(f"Mock trending data analysis for realistic travel insights")
        
        if travel_related:
            analysis_parts.append(f"Travel interest: {len(travel_related)} travel-related trends detected")
        
        if event_related:
            analysis_parts.append(f"Event activity: {len(event_related)} event-related trends detected")
        
        if high_impact_trends:
            analysis_parts.append(f"High-impact activity: {len(high_impact_trends)} major trends detected")
        
        # Seasonal insights
        season_insights = {
            12: "Holiday season driving increased travel demand",
            1: "Post-holiday travel deals and winter vacation planning",
            3: "Spring break season increasing travel interest",
            6: "Summer vacation season peak demand",
            7: "Peak summer travel period with high demand",
            11: "Thanksgiving and holiday travel planning surge"
        }
        
        if current_month in season_insights:
            analysis_parts.append(season_insights[current_month])
        
        return {
            "travel_impact_score": round(travel_impact, 1),
            "event_impact_score": round(event_impact, 1),
            "travel_related_trends": travel_related,
            "event_related_trends": event_related,
            "high_impact_trends": high_impact_trends,
            "total_trends_analyzed": len(trends),
            "is_mock_data": True,
            "analysis": "; ".join(analysis_parts),
            "top_trends": [t["trend"] for t in trends[:5]]
        }
    
    async def get_travel_insights_for_city(self, city: str) -> str:
        """Get comprehensive travel insights based on realistic trending patterns."""
        trends = await self.scrape_trending_topics(city)
        analysis = self.analyze_travel_relevance(trends)
        
        # Format the response
        city_name = city.title()
        travel_score = analysis["travel_impact_score"]
        event_score = analysis["event_impact_score"]
        
        response = f"Google Trends Analysis for {city_name}:\n"
        response += "📊 Note: Using realistic mock trending data for reliable insights\n"
        response += f"Travel Impact Score: {travel_score}/10\n"
        response += f"Event Impact Score: {event_score}/10\n"
        response += f"Analysis: {analysis['analysis']}\n"
        
        if analysis["top_trends"]:
            response += f"Trending Topics: {', '.join(analysis['top_trends'][:3])}\n"
        
        if analysis["travel_related_trends"]:
            response += f"Travel-Related Trends: {len(analysis['travel_related_trends'])} detected\n"
        
        if analysis["event_related_trends"]:
            response += f"Event-Related Trends: {len(analysis['event_related_trends'])} detected\n"
        
        if analysis.get("high_impact_trends"):
            response += f"High-Impact Events: {len(analysis['high_impact_trends'])} major trends detected\n"
        
        # Add interpretation
        if travel_score >= 8 or event_score >= 8:
            response += "🚨 HIGH IMPACT: Strong trending indicators suggest significant travel demand"
        elif travel_score >= 6 or event_score >= 6:
            response += "⚠️ ELEVATED IMPACT: Trending patterns indicate increased travel interest"
        elif travel_score >= 4 or event_score >= 4:
            response += "📈 MODERATE IMPACT: Some trending factors may affect travel demand"
        else:
            response += "✅ NORMAL ACTIVITY: Typical trending patterns with standard travel impact"
        
        return response

# Global instance - can be swapped with real scraper when Google access is available
mock_trends_analyzer = MockGoogleTrendsAnalyzer()
