import json
from datetime import datetime
from typing import Optional, List
from mcp.server.fastmcp import FastMCP
from servers.news_demand_explorer.config import SERVER_NAME, DEFAULT_LLM_PROVIDER, DEFAULT_MODEL, VERSION
from servers.news_demand_explorer.llm_client import LLMClient, LLMProvider
from servers.news_demand_explorer.explorer import DemandExplorer

news_mcp = FastMCP(SERVER_NAME)

llm_client = LLMClient(
    provider=LLMProvider(DEFAULT_LLM_PROVIDER),
    api_key=None,
    model=DEFAULT_MODEL
)
explorer = DemandExplorer(llm_client)

@mcp.tool()
async def analyze_route_demand(
    origin: str,
    destination: str,
    days_back: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    context: Optional[str] = ""
) -> str:
    sd = datetime.fromisoformat(start_date) if start_date else None
    ed = datetime.fromisoformat(end_date) if end_date else None
    return await explorer.analyze_route(origin, destination, days_back, sd, ed, context)

@mcp.tool()
async def configure_llm(
    provider: str,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    endpoint: Optional[str] = None
) -> str:
    p = LLMProvider(provider)
    global llm_client, explorer
    llm_client = LLMClient(p, api_key, endpoint, model)
    explorer = DemandExplorer(llm_client)
    return f"LLM set to {provider} ({llm_client.model})"

@mcp.resource("config://server.json")
async def get_server_config() -> str:
    return json.dumps({
        "name": SERVER_NAME,
        "version": VERSION,
        "llm": llm_client.provider.value,
        "model": llm_client.model
    }, indent=2)