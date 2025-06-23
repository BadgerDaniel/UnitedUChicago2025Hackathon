import os
import getpass
from dotenv import load_dotenv

from langchain.chat_models import init_chat_model
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_core.messages import AIMessage, ToolMessage
from langchain_community.chat_models import ChatOllama

from langgraph.graph import StateGraph, END, START, MessagesState
from langgraph.prebuilt import ToolNode

from mcp.server.fastmcp import FastMCP

# ─────────────────────────────────────────
# 🔧 Setup
# ─────────────────────────────────────────

# Initialize FastMCP server
mcp = FastMCP("staticdb")

# Load env variables
load_dotenv()
def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

_set_env("MISTRAL_API_KEY")
os.environ['TOKENIZERS_PARALLELISM'] = 'true'

# Load model and DB
llm = init_chat_model("mistral-small-latest", model_provider="mistralai")

db = SQLDatabase.from_uri("duckdb:///data/static.duckdb")
toolkit = SQLDatabaseToolkit(db=db, llm=llm)
tools = toolkit.get_tools()
print([tool.name for tool in tools])

# ─────────────────────────────────────────
# ⚙️ LangGraph Nodes
# ─────────────────────────────────────────

# Get tools
get_schema_tool = next(tool for tool in tools if tool.name == "sql_db_schema")
get_schema_node = ToolNode([get_schema_tool], name="get_schema")

run_query_tool = next(tool for tool in tools if tool.name == "sql_db_query")
run_query_node = ToolNode([run_query_tool], name="run_query")

def list_tables(state: MessagesState):
    tool_call = {
        "name": "sql_db_list_tables",
        "args": {},
        "id": "abc123",
        "type": "tool_call",
    }
    tool_call_message = AIMessage(content="", tool_calls=[tool_call])

    list_tables_tool = next(tool for tool in tools if tool.name == "sql_db_list_tables")
    tool_message = list_tables_tool.invoke(tool_call)
    response = AIMessage(f"Available tables: {tool_message.content}")

    return {"messages": [tool_call_message, tool_message, response]}

def call_get_schema(state: MessagesState):
    messages = state["messages"]
    while messages and isinstance(messages[-1], AIMessage):
        messages = messages[:-1]
    llm_with_tools = llm.bind_tools([get_schema_tool], tool_choice="any")
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

# generate_query_system_prompt = f"""
# You are an agent designed to interact with a SQL database.
# - Prices are stored in the `flight` table, in columns like `price_quartile_middle`.
# - The `route` table defines airport connections, and is linked to `flight` via `route_id`.
# - To answer questions about routes and prices, **JOIN** `flight` and `route` ON `flight.route_id = route.id`.
# Given an input question, create a syntactically correct {db.dialect} query to run,
# then look at the results and return the answer. Limit output to 5 rows.
# """

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

### 💡 Step-by-Step Reasoning:

#### A. For Price Trends or Spikes:

1. Extract departure and destination cities from the question.
2. Lookup city IDs from the `city` table.
3. Use `nearest_airport` to find departure and destination airport IDs.
4. Query the `route` table to find all matching routes.
5. Retrieve matching `flight` entries by joining `route → flight`, filtered by `departure_date` (e.g., year 2025).
6. Analyze one or more pricing columns (`price_quartile_middle`, etc.) by:
   - Grouping by month or day
   - Identifying large jumps ("spikes") in price.

#### B. For Weather-Related Questions:

7. Once a date or date range with a spike is identified, extract:
   - `departure_date` from the flight record
   - `city_id` for the departure and/or destination cities
8. Query the `weather` table for that `city_id` and `date`.
   - Match by `weather.date = flight.departure_date`
9. Retrieve:
   - `weather`, `weather_id`, `alert`
   - Optionally compare weather across cities if the question requires

#### C. When answering questions like “What is the flight price from City A to City B?”, follow this logic:

1. Find the city IDs for the given city names from the `city` table. City A is departure city and B is destination city. 
2. Find the `nearest_airport` for each city using the `city_id`.
3. Use the `route` table to find the route that connects the two airports.
4. Use the `flight` table to find flights for that `route_id` and report prices (e.g., `price_quartile_middle`).
5. Use the `departure_date` column if a date or date range is mentioned.
6. Prices are in USD.   


🔍 Key Guidance on Finding Routes:
When asked “What is the route id from City A to City B?”, find the airport of City A and use it as departure airport, and find the airport of City B and use it as destination airport. Find each airport id and locate the route id. 
When asked 'Summarize the price trends from flights departing from City A in 2025', pull out all routes that has City A as departure city and summarize how the prices decrease/increase over time. 
When asked about how price goes when there's a weather alert, extract all flights with weather alert, calculate the average price for each route in flight table and compare the alert flights price with them.  

---

### ⚠️ Notes:

- Always use **JOINs** to traverse from city → airport → route → flight → weather.
- Never `SELECT *`. Select only the relevant columns.
- Filter queries by date and cities involved.
- When describing weather conditions, state:
  - City, date, and weather (e.g., Clear, Rain, Snow).
- Use `alert = True` to highlight severe weather when relevant.

---

### 📊 Expected Output:

- For price questions: city pair, date(s), price(s)
- For weather questions: weather condition(s), date(s), alert status (if any)
- For combined questions: Explain both the price spike and the corresponding weather on that date"""

def generate_query(state: MessagesState):
    system_message = {"role": "system", "content": generate_query_system_prompt}
    llm_with_tools = llm.bind_tools([run_query_tool])
    # llm_with_tools = llm.bind_tools(tools)
    response = llm_with_tools.invoke([system_message] + state["messages"])
    return {"messages": [response]}

check_query_system_prompt = f"""
You are a SQL expert. Double-check the {db.dialect} query for errors.
Reproduce the correct query if needed.
"""

def check_query(state: MessagesState):
    system_message = {"role": "system", "content": check_query_system_prompt}
    tool_call = state["messages"][-1].tool_calls[0]
    # 🛡️ Guard clause: only proceed if "query" exists
    if "query" not in tool_call["args"]:
        return {"messages": []}  # skip check_query if no query was generated

    user_message = {"role": "user", "content": tool_call["args"]["query"]}
    llm_with_tools = llm.bind_tools([run_query_tool], tool_choice="any")
    response = llm_with_tools.invoke([system_message, user_message])
    response.id = state["messages"][-1].id
    return {"messages": [response]}

# def check_query(state: MessagesState):
#     system_message = {"role": "system", "content": check_query_system_prompt}
#     tool_call = state["messages"][-1].tool_calls[0]

#     if tool_call["name"] == "sql_db_query" and "query" in tool_call["args"]:
#         query_text = tool_call["args"]["query"]
#         user_message = {"role": "user", "content": query_text}
#     else:
#         # Fallback for non-query tools
#         user_message = {"role": "user", "content": "Check this tool call: " + str(tool_call["args"])}

#     llm_with_tools = llm.bind_tools(tools, tool_choice="any")  # Use all tools
#     response = llm_with_tools.invoke([system_message, user_message])

#     # Maintain continuity with prior call ID
#     response.id = state["messages"][-1].id
#     return {"messages": [response]}



def should_continue(state: MessagesState):
    if not state["messages"][-1].tool_calls:
        return END
    return "check_query"



# ─────────────────────────────────────────
# 📊 Build LangGraph Workflow
# ─────────────────────────────────────────

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


langgraph_agent = graph.compile()

# ─────────────────────────────────────────
# 🤖 MCP Tool
# ─────────────────────────────────────────

@mcp.tool()
def ask_sql_question(question: str) -> dict:
    """
    Runs the LangGraph SQL workflow to answer a SQL question.
    Streams results and returns the final summary.
    """
    final_response = None
    print(f"📣 MCP TOOL CALLED with question: {question}")

   

    for step in langgraph_agent.stream(
        {"messages": [{"role": "user", "content": question}]},
        stream_mode="values",
        
    ):
        msg = step["messages"][-1]
        msg.pretty_print()
        final_response = msg  # 🛠️ Update the final response

    if final_response is None:
        return {"success": False, "result": {"content": "No response received."}}

    return {"success": True, "result": {"content": final_response.content}}

# ─────────────────────────────────────────
# 🚀 Run FastMCP Server
# ─────────────────────────────────────────

# if __name__ == "__main__":
#     mcp.run(transport="sse")

if __name__ == "__main__":
    question = "How is the flight price going when there's an alert?"
    # for step in agent.stream(
    #     {"messages": [{"role": "user", "content": question}]},
    #     stream_mode="values",
    # ):
    #     step["messages"][-1].pretty_print()
    ask_sql_question(question)