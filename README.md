# UnitedUChicago2025Hackathon

## MCP server on static database

1. Create static database
- Create a folder in repo `data`
- Store API keys for: Mistral, Langsmith (optional), Amadeus, Open Weather Map
- Run `data_processing.py` to generate data, and run `write_db.py` to store to `data/static.db`

1. Run MCP server
- Run `static/server.py`
- Test the server with *mcp inspector* extension