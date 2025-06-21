# UnitedUChicago2025Hackathon

## MCP server on static database

1. Create static database
- Create a folder in repo `data`
- Store API keys for: Mistral, Langsmith (optional), Amadeus, Open Weather Map
- Run `data.ipynb` to retrive data and store to `data/static.db`

1. Run MCP server
- Run `static/mcp_static_tool.py`
- Test the server with *mcp inspector* extension