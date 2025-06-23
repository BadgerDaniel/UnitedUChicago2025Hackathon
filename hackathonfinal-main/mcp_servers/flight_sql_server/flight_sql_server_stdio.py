#!/usr/bin/env python3
"""
MCP Flight SQL Server - stdio version
A Model Context Protocol server that provides historical flight pricing and weather analysis via DuckDB.

This server provides access to:
- Historical flight pricing data with quartile analysis
- Route information between cities
- Weather correlation with flight prices
- Price trend analysis and spike detection
"""

import asyncio
import json
import sys
import logging
from typing import Any, Optional, List, Dict
from datetime import datetime
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from mcp.server.models import InitializationOptions
    import mcp.types as types
    from mcp.server import NotificationOptions, Server
    import mcp.server.stdio
except ImportError as e:
    print(f"MCP imports failed: {e}", file=sys.stderr)
    print("Please install MCP: pip install mcp", file=sys.stderr)
    sys.exit(1)

try:
    from langchain_community.utilities import SQLDatabase
    from langchain_community.agent_toolkits import SQLDatabaseToolkit
    from langchain.chat_models import init_chat_model
    from langchain_core.messages import AIMessage, ToolMessage
    from langgraph.graph import StateGraph, END, START, MessagesState
    from langgraph.prebuilt import ToolNode
except ImportError as e:
    print(f"LangChain imports failed: {e}", file=sys.stderr)
    print("Please install dependencies: pip install langchain langchain-community langgraph duckdb", file=sys.stderr)
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize the MCP server
server = Server("flight-sql-server")

# Database path - adjust this to point to your DuckDB file
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "static.duckdb")

class FlightSQLAnalyzer:
    """Analyzes historical flight pricing and weather data using DuckDB."""
    
    def __init__(self):
        """Initialize the SQL analyzer with database connection."""
        self.db_path = f"duckdb:///{DB_PATH}"
        self.db = None
        self.toolkit = None
        self.tools = None
        self.langgraph_agent = None
        self._initialize_db()
    
    def _initialize_db(self):
        """Initialize database connection and tools."""
        try:
            # Connect to DuckDB
            self.db = SQLDatabase.from_uri(self.db_path)
            
            # Initialize LLM - using a lightweight model for SQL generation
            self.llm = init_chat_model("gemini-1.5-flash", model_provider="google_genai")
            
            # Create toolkit
            self.toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
            self.tools = self.toolkit.get_tools()
            
            # Build the LangGraph workflow
            self._build_workflow()
            
            logger.info(f"Connected to DuckDB at {DB_PATH}")
            logger.info(f"Available tools: {[tool.name for tool in self.tools]}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _build_workflow(self):
        """Build the LangGraph workflow for SQL query generation."""
        # Get specific tools
        get_schema_tool = next(tool for tool in self.tools if tool.name == "sql_db_schema")
        get_schema_node = ToolNode([get_schema_tool], name="get_schema")
        
        run_query_tool = next(tool for tool in self.tools if tool.name == "sql_db_query")
        run_query_node = ToolNode([run_query_tool], name="run_query")
        
        def list_tables(state: MessagesState):
            tool_call = {
                "name": "sql_db_list_tables",
                "args": {},
                "id": "abc123",
                "type": "tool_call",
            }
            tool_call_message = AIMessage(content="", tool_calls=[tool_call])
            
            list_tables_tool = next(tool for tool in self.tools if tool.name == "sql_db_list_tables")
            tool_message = list_tables_tool.invoke(tool_call)
            response = AIMessage(f"Available tables: {tool_message.content}")
            
            return {"messages": [tool_call_message, tool_message, response]}
        
        def call_get_schema(state: MessagesState):
            messages = state["messages"]
            while messages and isinstance(messages[-1], AIMessage):
                messages = messages[:-1]
            llm_with_tools = self.llm.bind_tools([get_schema_tool], tool_choice="any")
            response = llm_with_tools.invoke(messages)
            return {"messages": [response]}
        
        generate_query_system_prompt = f"""
You are a smart agent that interacts with a SQL database to analyze flight pricing and weather trends.

You have access to the following schema:

1. **city**:
   - `id`, `city_name`

2. **nearest_airport**:
   - `id`, `iata_code`, `city_id` (foreign key to city)

3. **route**:
   - `id`, `depar_airport_id`, `desti_airport_id` (foreign keys to nearest_airport)

4. **flight**:
   - `id`, `route_id`, `departure_date`, and prices:
     - `price_quartile_minimum`, `price_quartile_low`, `price_quartile_middle`, `price_quartile_high`, `price_quartile_maximum`

5. **weather**:
   - `id`, `date`, `city_id`, `weather_id`, `weather`, `alert`
   - Linked to city via `city_id`

---

### 💡 Key Query Patterns:

#### A. For Price Analysis:
1. Extract departure and destination cities from the question.
2. Lookup city IDs from the `city` table.
3. Use `nearest_airport` to find departure and destination airport IDs.
4. Query the `route` table to find matching routes.
5. Retrieve `flight` entries by joining `route → flight`.
6. Analyze pricing columns (typically `price_quartile_middle` for average prices).

#### B. For Weather Correlation:
1. Once you have flight dates, extract `departure_date` and city IDs.
2. Query the `weather` table for that `city_id` and `date`.
3. Check for weather conditions and alerts.

#### C. Common Queries:
- "What is the flight price from City A to City B?" - Find route and return prices
- "Show price trends" - Group by month/week and analyze price changes
- "Weather impact on prices" - Join flight and weather data

### ⚠️ Important:
- Always use JOINs to traverse relationships
- Filter by relevant dates (e.g., year 2025 for recent data)
- Return specific columns, not SELECT *
- Prices are in USD
- Limit results to keep responses concise
"""
        
        def generate_query(state: MessagesState):
            system_message = {"role": "system", "content": generate_query_system_prompt}
            llm_with_tools = self.llm.bind_tools([run_query_tool])
            response = llm_with_tools.invoke([system_message] + state["messages"])
            return {"messages": [response]}
        
        check_query_system_prompt = f"""
You are a SQL expert. Double-check the {self.db.dialect} query for errors.
Reproduce the correct query if needed.
"""
        
        def check_query(state: MessagesState):
            system_message = {"role": "system", "content": check_query_system_prompt}
            tool_call = state["messages"][-1].tool_calls[0]
            if "query" not in tool_call["args"]:
                return {"messages": []}
            
            user_message = {"role": "user", "content": tool_call["args"]["query"]}
            llm_with_tools = self.llm.bind_tools([run_query_tool], tool_choice="any")
            response = llm_with_tools.invoke([system_message, user_message])
            response.id = state["messages"][-1].id
            return {"messages": [response]}
        
        def should_continue(state: MessagesState):
            if not state["messages"][-1].tool_calls:
                return END
            return "check_query"
        
        # Build the graph
        graph = StateGraph(MessagesState)
        graph.add_node(list_tables)
        graph.add_node(call_get_schema)
        graph.add_node(get_schema_node, "get_schema")
        graph.add_node(generate_query)
        graph.add_node(check_query)
        graph.add_node(run_query_node, "run_query")
        
        graph.add_edge(START, "list_tables")
        graph.add_edge("list_tables", "call_get_schema")
        graph.add_edge("call_get_schema", "get_schema")
        graph.add_edge("get_schema", "generate_query")
        graph.add_conditional_edges("generate_query", should_continue)
        graph.add_edge("check_query", "run_query")
        graph.add_edge("run_query", "generate_query")
        
        self.langgraph_agent = graph.compile()
    
    async def analyze_sql_question(self, question: str) -> str:
        """
        Analyze a SQL question about flight pricing and weather.
        
        Args:
            question: Natural language question about flight data
            
        Returns:
            Analysis results as a string
        """
        try:
            final_response = None
            all_messages = []
            
            logger.info(f"Processing SQL question: {question}")
            
            # Run the LangGraph workflow
            async for step in self.langgraph_agent.astream(
                {"messages": [{"role": "user", "content": question}]},
                stream_mode="values",
            ):
                msg = step["messages"][-1]
                all_messages.append(msg)
                
                # Keep track of the final response
                if hasattr(msg, 'content') and msg.content and not hasattr(msg, 'tool_calls'):
                    final_response = msg
            
            if final_response is None:
                return "No results found for your query."
            
            # Format the response
            result = final_response.content
            
            # Add some context if it's raw data
            if result and (result.startswith('[') or result.startswith('(')):
                result = f"Query Results:\n{result}"
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing SQL question: {e}")
            return f"Error analyzing your question: {str(e)}"
    
    async def get_route_prices(self, origin_city: str, destination_city: str, 
                             start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        """
        Get flight prices for a specific route.
        
        Args:
            origin_city: Origin city name
            destination_city: Destination city name
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
            
        Returns:
            Price information as a string
        """
        question = f"What are the flight prices from {origin_city} to {destination_city}"
        if start_date:
            question += f" departing after {start_date}"
        if end_date:
            question += f" and before {end_date}"
        question += "? Show price quartiles."
        
        return await self.analyze_sql_question(question)
    
    async def analyze_price_trends(self, origin_city: str, destination_city: str, 
                                 time_period: str = "monthly") -> str:
        """
        Analyze price trends for a route.
        
        Args:
            origin_city: Origin city name
            destination_city: Destination city name
            time_period: Grouping period (monthly, weekly, daily)
            
        Returns:
            Trend analysis as a string
        """
        question = f"Show {time_period} price trends for flights from {origin_city} to {destination_city}. Group by {time_period} and show average prices."
        return await self.analyze_sql_question(question)
    
    async def check_weather_impact(self, city: str, date: str) -> str:
        """
        Check weather conditions and their impact on flight prices.
        
        Args:
            city: City name
            date: Date to check (YYYY-MM-DD)
            
        Returns:
            Weather and price impact analysis
        """
        question = f"What was the weather in {city} on {date} and how did it affect flight prices? Show both weather conditions and any price changes."
        return await self.analyze_sql_question(question)

# Create global analyzer instance
analyzer = FlightSQLAnalyzer()

@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available SQL analysis tools."""
    return [
        types.Tool(
            name="analyze-flight-sql",
            description="Analyze historical flight pricing and weather data using natural language queries",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Natural language question about flight prices, routes, or weather impacts"
                    }
                },
                "required": ["question"]
            }
        ),
        types.Tool(
            name="get-route-prices",
            description="Get historical flight prices for a specific route",
            inputSchema={
                "type": "object",
                "properties": {
                    "origin_city": {
                        "type": "string",
                        "description": "Origin city name (e.g., 'Chicago', 'New York')"
                    },
                    "destination_city": {
                        "type": "string",
                        "description": "Destination city name (e.g., 'London', 'Tokyo')"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Optional start date in YYYY-MM-DD format"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "Optional end date in YYYY-MM-DD format"
                    }
                },
                "required": ["origin_city", "destination_city"]
            }
        ),
        types.Tool(
            name="analyze-price-trends",
            description="Analyze price trends for a route over time",
            inputSchema={
                "type": "object",
                "properties": {
                    "origin_city": {
                        "type": "string",
                        "description": "Origin city name"
                    },
                    "destination_city": {
                        "type": "string",
                        "description": "Destination city name"
                    },
                    "time_period": {
                        "type": "string",
                        "enum": ["monthly", "weekly", "daily"],
                        "description": "Time period for grouping (default: monthly)"
                    }
                },
                "required": ["origin_city", "destination_city"]
            }
        ),
        types.Tool(
            name="check-weather-impact",
            description="Check weather conditions and their impact on flight prices",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name to check weather for"
                    },
                    "date": {
                        "type": "string",
                        "description": "Date to check in YYYY-MM-DD format"
                    }
                },
                "required": ["city", "date"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: Optional[Dict[str, Any]] = None
) -> List[types.TextContent]:
    """Handle tool execution."""
    if not arguments:
        arguments = {}
    
    try:
        if name == "analyze-flight-sql":
            result = await analyzer.analyze_sql_question(arguments.get("question", ""))
        elif name == "get-route-prices":
            result = await analyzer.get_route_prices(
                arguments.get("origin_city", ""),
                arguments.get("destination_city", ""),
                arguments.get("start_date"),
                arguments.get("end_date")
            )
        elif name == "analyze-price-trends":
            result = await analyzer.analyze_price_trends(
                arguments.get("origin_city", ""),
                arguments.get("destination_city", ""),
                arguments.get("time_period", "monthly")
            )
        elif name == "check-weather-impact":
            result = await analyzer.check_weather_impact(
                arguments.get("city", ""),
                arguments.get("date", "")
            )
        else:
            result = f"Unknown tool: {name}"
        
        return [types.TextContent(type="text", text=result)]
        
    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}")
        error_msg = f"Error: {str(e)}"
        return [types.TextContent(type="text", text=error_msg)]

async def main():
    """Run the MCP server."""
    logger.info("Starting Flight SQL MCP Server...")
    
    # Check if database exists
    if not os.path.exists(DB_PATH):
        logger.error(f"Database not found at {DB_PATH}")
        print(f"ERROR: Database file not found at {DB_PATH}", file=sys.stderr)
        sys.exit(1)
    
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="flight-sql-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())