import streamlit as st
import openai
import asyncio
import json
from typing import List, Dict, Any
from dataclasses import dataclass
import openmeteo_requests
import requests_cache
from retry_requests import retry
from datetime import datetime

# Configure OpenAI - API key loaded from Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]


@dataclass
class ReasoningStep:
    step_id: str
    tool: str
    params: Dict[str, Any]
    description: str


@dataclass
class QueryPlan:
    steps: List[ReasoningStep]
    final_synthesis: str


class WeatherMCPTool:
    """Weather MCP Tool - adapted from your existing code"""

    def __init__(self):
        # Setup the Open-Meteo API client with cache and retry on error
        cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        self.client = openmeteo_requests.Client(session=retry_session)

        self.city_coords = {
            "london": (51.5074, -0.1278),
            "new york": (40.7128, -74.0060),
            "tokyo": (35.6762, 139.6503),
            "paris": (48.8566, 2.3522),
            "sydney": (-33.8688, 151.2093),
            "mumbai": (19.0760, 72.8777),
            "berlin": (52.5200, 13.4050),
            "moscow": (55.7558, 37.6176),
            "beijing": (39.9042, 116.4074),
            "los angeles": (34.0522, -118.2437),
            "chicago": (41.8781, -87.6298),
            "toronto": (43.6532, -79.3832),
            "rome": (41.9028, 12.4964),
            "madrid": (40.4168, -3.7038),
            "amsterdam": (52.3676, 4.9041),
            "stockholm": (59.3293, 18.0686)
        }

    def get_coordinates_for_city(self, city: str) -> tuple:
        city_lower = city.lower().strip()
        return self.city_coords.get(city_lower, self.city_coords["london"])

    async def get_current_weather(self, city: str) -> str:
        """Get current weather for a city"""
        try:
            latitude, longitude = self.get_coordinates_for_city(city)

            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "current": ["temperature_2m", "relative_humidity_2m", "wind_speed_10m", "weather_code"],
                "timezone": "auto"
            }

            responses = self.client.weather_api(url, params=params)
            response = responses[0]

            current = response.Current()
            current_temp = current.Variables(0).Value()
            current_humidity = current.Variables(1).Value()
            current_wind_speed = current.Variables(2).Value()
            current_weather_code = current.Variables(3).Value()

            weather_descriptions = {
                0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
                45: "Fog", 61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
                95: "Thunderstorm"
            }

            weather_desc = weather_descriptions.get(int(current_weather_code), "Unknown")

            return f"Weather in {city.title()}: {current_temp:.1f}°C, {weather_desc}, Humidity: {current_humidity:.0f}%, Wind: {current_wind_speed:.1f} km/h"

        except Exception as e:
            return f"Error fetching weather for {city}: {str(e)}"

    async def get_weather_forecast(self, city: str, days: int = 3) -> str:
        """Get weather forecast for a city"""
        try:
            latitude, longitude = self.get_coordinates_for_city(city)

            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "daily": ["temperature_2m_max", "temperature_2m_min", "weather_code"],
                "timezone": "auto",
                "forecast_days": min(days, 7)
            }

            responses = self.client.weather_api(url, params=params)
            response = responses[0]

            daily = response.Daily()
            daily_temp_max = daily.Variables(0).ValuesAsNumpy()
            daily_temp_min = daily.Variables(1).ValuesAsNumpy()

            forecast_text = f"{days}-day forecast for {city.title()}:\n"
            for i in range(min(days, len(daily_temp_max))):
                forecast_text += f"Day {i + 1}: High {daily_temp_max[i]:.1f}°C, Low {daily_temp_min[i]:.1f}°C\n"

            return forecast_text

        except Exception as e:
            return f"Error fetching forecast for {city}: {str(e)}"


class ReWOOQueryDecomposer:
    """ReWOO-based query decomposer using OpenAI"""

    def __init__(self):
        # API key is loaded from Streamlit secrets at module level
        self.available_tools = {
            "weather_current": "Get current weather for a city",
            "weather_forecast": "Get weather forecast for a city (1-7 days)",
            # Placeholder for future tools
            "flight_data": "Get flight pricing and booking data (NOT IMPLEMENTED)",
            "event_data": "Get concert/event information (NOT IMPLEMENTED)",
            "google_trends": "Get Google Trends data (NOT IMPLEMENTED)"
        }

    async def decompose_query(self, user_query: str) -> QueryPlan:
        """Decompose user query into reasoning steps using ReWOO approach"""

        tools_description = "\n".join([f"- {tool}: {desc}" for tool, desc in self.available_tools.items()])

        decomposition_prompt = f"""
You are a query decomposer using the ReWOO (Reasoning WithOut Observation) approach. 
Break down the user's question into a series of reasoning steps that can be executed by available tools.

Available tools:
{tools_description}

User Query: {user_query}

For WEATHER-related queries, use the available weather tools.
For other queries (flights, events, trends), acknowledge the limitation but show how you WOULD decompose them.

Respond with a JSON object containing:
1. "steps": Array of reasoning steps, each with:
   - "step_id": unique identifier (e.g., "step1", "step2")
   - "tool": tool name to use
   - "params": parameters for the tool
   - "description": what this step accomplishes
2. "final_synthesis": Description of how to combine results

Example format:
{{
    "steps": [
        {{
            "step_id": "step1",
            "tool": "weather_current",
            "params": {{"city": "New York"}},
            "description": "Get current weather for New York"
        }}
    ],
    "final_synthesis": "Present the weather information to the user"
}}
"""

        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": decomposition_prompt}],
                temperature=0.1
            )

            result = json.loads(response.choices[0].message.content)

            steps = [ReasoningStep(
                step_id=step["step_id"],
                tool=step["tool"],
                params=step["params"],
                description=step["description"]
            ) for step in result["steps"]]

            return QueryPlan(steps=steps, final_synthesis=result["final_synthesis"])

        except Exception as e:
            # Fallback for simple weather queries
            if any(weather_word in user_query.lower() for weather_word in ["weather", "temperature", "rain", "storm"]):
                return QueryPlan(
                    steps=[ReasoningStep(
                        step_id="step1",
                        tool="weather_current",
                        params={"city": "London"},  # Default city
                        description="Get weather information"
                    )],
                    final_synthesis="Present weather information"
                )
            else:
                return QueryPlan(
                    steps=[],
                    final_synthesis=f"Error decomposing query: {str(e)}"
                )


class MCPToolRouter:
    """Routes decomposed queries to appropriate MCP tools"""

    def __init__(self):
        self.weather_tool = WeatherMCPTool()

    async def execute_step(self, step: ReasoningStep) -> str:
        """Execute a single reasoning step"""
        try:
            if step.tool == "weather_current":
                city = step.params.get("city", "London")
                return await self.weather_tool.get_current_weather(city)

            elif step.tool == "weather_forecast":
                city = step.params.get("city", "London")
                days = step.params.get("days", 3)
                return await self.weather_tool.get_weather_forecast(city, days)

            elif step.tool in ["flight_data", "event_data", "google_trends"]:
                return f"Tool '{step.tool}' not implemented yet. Would query: {step.params}"

            else:
                return f"Unknown tool: {step.tool}"

        except Exception as e:
            return f"Error executing {step.tool}: {str(e)}"

    async def execute_plan(self, plan: QueryPlan) -> Dict[str, Any]:
        """Execute the full query plan"""
        results = {}

        for step in plan.steps:
            st.write(f"🔄 Executing: {step.description}")
            result = await self.execute_step(step)
            results[step.step_id] = {
                "tool": step.tool,
                "params": step.params,
                "result": result,
                "description": step.description
            }

        return results


# Streamlit App
def main():
    st.set_page_config(
        page_title="ReWOO Query Decomposer with MCP",
        page_icon="🤖",
        layout="wide"
    )

    st.title("🤖 ReWOO Query Decomposer with MCP Integration")
    st.markdown("Ask complex questions that require multiple reasoning steps!")

    # Sidebar configuration
    st.sidebar.header("⚙️ Configuration")
    st.sidebar.success("✅ OpenAI API Key loaded from secrets")
    st.sidebar.info("Using GPT-4o-mini for query decomposition")

    # Initialize components
    try:
        decomposer = ReWOOQueryDecomposer()
        router = MCPToolRouter()
    except Exception as e:
        st.error(f"Failed to initialize components. Check that OPENAI_API_KEY is set in Streamlit secrets: {e}")
        return

    # Example queries
    st.sidebar.subheader("📝 Example Queries")
    example_queries = [
        "What's the weather like in New York?",
        "Compare weather in London and Paris",
        "Give me a 5-day forecast for Tokyo",
        "Which cities had weather alerts during major events in August 2023?",  # Will show limitation
        "Find flight price spikes correlated with storms"  # Will show limitation
    ]

    selected_example = st.sidebar.selectbox(
        "Choose an example:",
        [""] + example_queries
    )

    # Main query interface
    st.subheader("🔍 Ask Your Question")

    user_query = st.text_area(
        "Enter your query:",
        value=selected_example if selected_example else "",
        height=100,
        placeholder="e.g., What's the weather like in New York and London?"
    )

    if st.button("🚀 Process Query", type="primary"):
        if user_query:
            with st.spinner("Decomposing query..."):
                # Step 1: Decompose query
                plan = asyncio.run(decomposer.decompose_query(user_query))

                st.subheader("📋 Query Decomposition")

                # Show the plan
                for i, step in enumerate(plan.steps, 1):
                    with st.expander(f"Step {i}: {step.description}"):
                        st.json({
                            "Tool": step.tool,
                            "Parameters": step.params,
                            "Description": step.description
                        })

                st.write(f"**Final Synthesis Plan:** {plan.final_synthesis}")

                # Step 2: Execute the plan
                st.subheader("⚡ Execution Results")

                results = asyncio.run(router.execute_plan(plan))

                # Display results
                for step_id, result_data in results.items():
                    st.write(f"**{step_id.upper()}:** {result_data['description']}")

                    if "not implemented" in result_data['result'].lower():
                        st.warning(result_data['result'])
                    else:
                        st.success(result_data['result'])
                    st.write("---")

                # Step 3: Final synthesis (placeholder)
                st.subheader("🎯 Final Answer")
                if results:
                    st.info("Here's what I found based on the available tools...")
                    # In a real implementation, you'd use another LLM call to synthesize
                    for result_data in results.values():
                        if "Error" not in result_data['result'] and "not implemented" not in result_data[
                            'result'].lower():
                            st.write(f"• {result_data['result']}")
                else:
                    st.warning("No tools were available to process this query.")

        else:
            st.warning("Please enter a query.")

    # Information section
    st.markdown("---")
    st.subheader("ℹ️ About This System")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **🔧 Currently Available Tools:**
        - Weather (current conditions)
        - Weather (forecasting)

        **🚧 Planned Tools (for hackathon):**
        - Flight data API
        - Event/concert data API  
        - Google Trends API
        - News/alerts API
        """)

    with col2:
        st.markdown("""
        **🧠 ReWOO Architecture:**
        1. **Query Decomposition**: Break down complex questions
        2. **Tool Routing**: Route to appropriate MCP servers
        3. **Execution**: Run tools in sequence
        4. **Synthesis**: Combine results into final answer

        **🔌 MCP Integration:**
        Each tool connects to an MCP server for data access
        """)


if __name__ == "__main__":
    main()