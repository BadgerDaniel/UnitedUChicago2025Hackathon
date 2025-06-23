#!/usr/bin/env python3
"""MCP Fetch Server - Web content fetching with HTML to Markdown conversion."""

import argparse
import asyncio
import html2text
import httpx
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

from pydantic import BaseModel
from mcp.server.fastmcp import FastMCP


class Fetch(BaseModel):
    """Parameters for the fetch tool."""
    url: str
    max_length: Optional[int] = None
    start_index: Optional[int] = None
    raw: Optional[bool] = False


def extract_content_from_html(html_content: str, start_index: int = 0, max_length: Optional[int] = None) -> str:
    """Extract and convert HTML content to markdown."""
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = False
    h.ignore_emphasis = False
    h.body_width = 0
    
    markdown_content = h.handle(html_content)
    
    if start_index > 0:
        markdown_content = markdown_content[start_index:]
    
    if max_length is not None:
        markdown_content = markdown_content[:max_length]
    
    return markdown_content


def get_robots_txt_url(url: str) -> str:
    """Generate robots.txt URL for a given website."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/robots.txt"


async def check_may_autonomously_fetch_url(
    url: str, 
    user_agent: str = "mcp-fetch/*", 
    http_client: Optional[httpx.AsyncClient] = None
) -> bool:
    """Check if URL can be fetched according to robots.txt."""
    robots_txt_url = get_robots_txt_url(url)
    
    try:
        if http_client:
            response = await http_client.get(robots_txt_url, timeout=10.0)
            robots_content = response.text if response.status_code == 200 else ""
        else:
            async with httpx.AsyncClient() as client:
                response = await client.get(robots_txt_url, timeout=10.0)
                robots_content = response.text if response.status_code == 200 else ""
        
        if robots_content:
            rp = RobotFileParser()
            rp.set_url(robots_txt_url)
            rp.read_from_string(robots_content)
            return rp.can_fetch(user_agent, url)
        else:
            return True
    except Exception:
        return True


async def fetch_url(
    url: str,
    max_length: Optional[int] = None,
    start_index: int = 0,
    raw: bool = False,
    user_agent: str = "mcp-fetch/*",
    ignore_robots_txt: bool = False,
    http_client: Optional[httpx.AsyncClient] = None
) -> str:
    """Fetch content from a URL."""
    if not ignore_robots_txt:
        may_fetch = await check_may_autonomously_fetch_url(url, user_agent, http_client)
        if not may_fetch:
            raise ValueError(f"Robots.txt disallows fetching {url}")
    
    headers = {"User-Agent": user_agent}
    
    try:
        if http_client:
            response = await http_client.get(url, headers=headers, timeout=30.0, follow_redirects=True)
        else:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=30.0, follow_redirects=True)
        
        response.raise_for_status()
        content = response.text
        
        if raw:
            if max_length is not None:
                content = content[:max_length]
            return content
        else:
            return extract_content_from_html(content, start_index, max_length)
            
    except httpx.HTTPError as e:
        raise ValueError(f"HTTP error fetching {url}: {e}")
    except Exception as e:
        raise ValueError(f"Error fetching {url}: {e}")


# Global variables for server configuration
user_agent_global = "mcp-fetch/*"
ignore_robots_txt_global = False
proxy_url_global = None
http_client_global = None

# Create the FastMCP app
app = FastMCP(
    name="fetch",
    description="Web content fetching with HTML to Markdown conversion"
)

# Configure the server port
import os
PORT = int(os.getenv('MCP_SERVER_PORT', '8008'))

@app.tool()
async def fetch(
    url: str,
    max_length: Optional[int] = None,
    start_index: Optional[int] = 0,
    raw: Optional[bool] = False
) -> str:
    """Fetch a web page and convert it to markdown.
    
    Args:
        url: URL to fetch
        max_length: Maximum number of characters to return (default: no limit)
        start_index: Starting index for content extraction (default: 0)
        raw: Return raw HTML instead of markdown (default: false)
    
    Returns:
        The fetched content as markdown or raw HTML
    """
    try:
        content = await fetch_url(
            url=url,
            max_length=max_length,
            start_index=start_index or 0,
            raw=raw or False,
            user_agent=user_agent_global,
            ignore_robots_txt=ignore_robots_txt_global,
            http_client=http_client_global
        )
        
        return content
        
    except Exception as e:
        return f"Error: {str(e)}"


def setup_server_config():
    """Setup server configuration from command line args."""
    global user_agent_global, ignore_robots_txt_global, proxy_url_global, http_client_global
    
    parser = argparse.ArgumentParser(description="MCP Fetch Server")
    parser.add_argument(
        "--user-agent",
        default="mcp-fetch/*",
        help="User agent string for requests"
    )
    parser.add_argument(
        "--ignore-robots-txt",
        action="store_true",
        help="Ignore robots.txt restrictions"
    )
    parser.add_argument(
        "--proxy-url",
        help="Proxy URL for requests"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="Port to run server on (default: 8001)"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to run server on (default: 127.0.0.1)"
    )
    
    args = parser.parse_args()
    
    user_agent_global = args.user_agent
    ignore_robots_txt_global = args.ignore_robots_txt
    proxy_url_global = args.proxy_url
    
    if proxy_url_global:
        http_client_global = httpx.AsyncClient(proxy=proxy_url_global)
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    return args


if __name__ == "__main__":
    print("Starting MCP fetch server with SSE transport...")
    args = setup_server_config()
    
    print(f"Server configured for {args.host}:{args.port}")
    
    # Run the server with SSE transport
    # Note: FastMCP runs on its own port, we'll use environment variable to configure
    os.environ['FASTMCP_PORT'] = str(args.port)
    os.environ['FASTMCP_HOST'] = args.host
    app.run(transport="sse")