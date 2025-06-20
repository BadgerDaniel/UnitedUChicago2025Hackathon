import feedparser
import aiohttp
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from typing import List, Dict, Optional

class DemandExplorer:
    def __init__(self, llm_client):
        self.llm = llm_client

    def parse_date(self, ds: str) -> Optional[datetime]:
        if not ds:
            return None
        try:
            return date_parser.parse(ds)
        except Exception:
            return None

    async def scrape(self, terms: List[str], days_back: int = 7) -> List[Dict]:
        end = datetime.utcnow()
        start = end - timedelta(days=days_back)
        results: List[Dict] = []
        for term in terms:
            url = f"https://news.google.com/rss/search?q={term}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    text = await resp.text()
            feed = feedparser.parse(text)
            for entry in feed.entries:
                dt = self.parse_date(entry.get('published', ''))
                if dt and start <= dt <= end:
                    results.append({
                        'title': entry.title,
                        'link': entry.link,
                        'published': entry.get('published', ''),
                        'datetime': dt,
                        'summary': entry.get('summary', ''),
                    })
        unique = {a['title']: a for a in results}.values()
        return sorted(unique, key=lambda x: x['datetime'], reverse=True)

    async def analyze_route(
        self,
        origin: str,
        dest: str,
        days_back: Optional[int] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        context: str = ""
    ) -> str:
        if days_back:
            back = days_back
        elif start and end:
            back = (end - start).days
        else:
            back = 7

        terms = [f"{origin} to {dest}", f"flights {origin} {dest}"]
        if context:
            terms.append(f"{context} {origin} {dest}")

        articles = await self.scrape(terms, back)
        if not articles:
            return f"No articles for {origin}-{dest} in past {back} days"

        prompt_lines = [f"Found {len(articles)} articles:"]
        for art in articles[:20]:
            prompt_lines.append(f"- {art['title']} ({art['published']})")
        prompt = "\n".join(prompt_lines)

        system = "You are an airline demand analyst..."
        return await self.llm.generate(prompt, system)