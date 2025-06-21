from typing import Dict, List, Optional
import aiohttp
import praw
import openai
import logging
from datetime import UTC, datetime, timedelta
from dateutil import parser as date_parser
from mcp.server.fastmcp import FastMCP
import os

from llm import LLMClient, LLMProvider
from reddit_explorer import RedditExplorer

openai.api_key = os.getenv("OPENAI_API_KEY")

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = "reddit-event-detector"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# City to Subreddit group
CITY_SUBREDDITS = {
    "new york": "nyc",
    "los angeles": "LosAngeles",
    "chicago": "chicago",
    "houston": "houston",
    "phoenix": "phoenix",
    "philadelphia": "philadelphia",
    "san antonio": "sanantonio",
    "san diego": "sandiego",
    "dallas": "dallas",
    "san jose": "SanJose",
    "austin": "Austin",
    "jacksonville": "jacksonville",
    "fort worth": "fortworth",
    "columbus": "Columbus",
    "charlotte": "Charlotte"
}

# Reddit API
print(REDDIT_CLIENT_ID)
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT
)

# Reddit MCP
mcp = FastMCP("reddit-posts-finder")

# Initialize components - declare globals first
llm_client = None
demand_explorer = None

def initialize_components():
    """Initialize the LLM client and demand explorer"""
    global llm_client, demand_explorer
    llm_client = LLMClient(
        provider=LLMProvider.OPENAI,
        api_key=OPENAI_API_KEY,
        model="gpt-4o-mini"
    )
    demand_explorer = RedditExplorer(llm_client)


# Initialize on startup
initialize_components()

# Fetch posts from given subreddit for time range
def get_relevant_posts(subreddit_name, days_back=7):
    subreddit = reddit.subreddit(subreddit_name)

    posts = []
    # Limit should be changed here based on 
    for post in subreddit.new(limit=100):
        timestamp = post.created_utc
        post_date = datetime.fromtimestamp(timestamp, UTC)

        # Check if the post is recent (within the last 'days_back' days)
        if post_date > datetime.now(UTC) - timedelta(days=days_back):
            posts.append({
                "title": post.title,
                "selftext": post.selftext or "",
                "created_utc": post_date
            })
    return posts

# Call LLM client to extract events from posts
async def extract_events_from_posts(city, posts):
    prompt = f"""
You are an AI agent. Analyze Reddit posts from r/{CITY_SUBREDDITS[city]} and extract public events.
Return results in JSON format as a list with:
- event (str)
- date (str)
- type (festival, concert, sports, etc.)
- description (short summary)

Posts:
"""
    for p in posts:
        prompt += f"\nTitle: {p['title']}\nDate: {p['created_utc']}\nText: {p['selftext']}\n"

    print(prompt)

    system_prompt = f""""
    You are an events analyst that extracts public event data."
    """

    return await llm_client.generate_analysis(prompt, system_prompt)

@mcp.tool
async def analyze_city(city: str, days_back: Optional[int]) -> str:
    """
    Analyze demand factors for a specific city

    Args:
        city: The city of interest to analyze data for
        days_back: The specific number of days back that data should be analyzed for
    """
    if city not in CITY_SUBREDDITS:
        return f"Error: City {city} not supported"

    print(f"Processing {city}...")
    posts = get_relevant_posts(CITY_SUBREDDITS[city]) # TODO specify timeframe / days back
    results = await extract_events_from_posts(city, posts)
    return results