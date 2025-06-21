
from langchain.chat_models import init_chat_model
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langgraph.prebuilt import create_react_agent

import os
from dotenv import load_dotenv
import getpass

from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("staticdb")

# Load mistrial api
def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

_set_env("MISTRAL_API_KEY")
os.environ['TOKENIZERS_PARALLELISM'] = 'true'

# Initialize model and db
llm = init_chat_model("mistral-small-latest", model_provider="mistralai")
db = SQLDatabase.from_uri("duckdb:///data/static.duckdb")  # Or your own DB path

# Extract sql tools for langchain agent
toolkit = SQLDatabaseToolkit(db=db, llm=llm)
tools = toolkit.get_tools()

# set system prompt
sql_prompt = """
You are an agent designed to interact with a SQL database.
Given an input question, create a syntactically correct {dialect} query to run,
then look at the results of the query and return the answer. Unless the user
specifies a specific number of examples they wish to obtain, always limit your
query to at most {top_k} results.

You can order the results by a relevant column to return the most interesting
examples in the database. Never query for all the columns from a specific table,
only ask for the relevant columns given the question.

You MUST double check your query before executing it. If you get an error while
executing a query, rewrite the query and try again.

DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the
database.

To start you should ALWAYS look at the tables in the database to see what you
can query. Do NOT skip this step.

Then you should query the schema of the most relevant tables.
""".format(
    dialect=db.dialect,
    top_k=5,
)

# Create an agent and bind tools
agent = create_react_agent(model=llm, tools=tools, prompt=sql_prompt)

# set mcp tools
@mcp.tool()
def ask_sql_question(question: str) -> dict:
    """
        Ask a natural language question and return the result from the SQL database.
        This tool uses an agent to translate the question into a SQL query, validate it, and run it.
    """

    final_response = None

    for step in agent.stream(
        {"messages": [{"role": "user", "content": question}]},
        stream_mode="values",
    ):
        msg = step["messages"][-1]
        msg.pretty_print()  # Optional: show intermediate output
        final_response = msg  # Save the last one

    return final_response

    # return {"output": result}
# test with a simple query
# if __name__ == "__main__":
#     question = "What is the latest weather?"
#     for step in agent.stream(
#         {"messages": [{"role": "user", "content": question}]},
#         stream_mode="values",
#     ):
#         step["messages"][-1].pretty_print()

# 
if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='sse')