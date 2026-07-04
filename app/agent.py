import os

import google.auth
from google.adk.agents import LlmAgent
from google.adk.apps import App
from google.adk.events.event import Event
from google.adk.models import Gemini
from google.adk.workflow import DEFAULT_ROUTE, Workflow, node
from google.auth.exceptions import DefaultCredentialsError
from google import genai

from app.tools import read_airbnb_data, run_market_scanner

# Auth initialization
import truststore
truststore.inject_into_ssl()

try:
    _, project_id = google.auth.default()
    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
    os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
except DefaultCredentialsError:
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"

# 1. Classifier Node
@node
def classifier(node_input: str):
    """Routes the user request to the appropriate agent based on intent."""
    client = genai.Client()
    prompt = f"""You are a routing agent. You must respond ONLY with the exact route name (e.g., 'lookup_price', 'update_db'). Do not add any punctuation, markdown formatting, explanations, or extra words.
Available routes:
- update_db: updating the database, running the scanner, fetching new data.
- lookup_price: asking for a specific price/rate for an apartment.
- recommend_price: asking for pricing recommendations or advice.
- competitive_analysis: asking for market analysis or competitor comparison.
- general_chat: anything else.

User input: {node_input}"""
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        route_name = response.text.strip()
    except Exception:
        route_name = "general_chat"

    valid_routes = ["update_db", "lookup_price", "recommend_price", "competitive_analysis", "general_chat"]
    if route_name not in valid_routes:
        route_name = "general_chat"

    return Event(output=node_input, route=route_name)

# 2. Sub-Agents
scanner_agent = LlmAgent(
    name="scanner_agent",
    model=Gemini(model="gemini-flash-latest"),
    instruction="""You are the Airbnb Data Scanner. Your job is to fetch the latest Airbnb listing details
    by running the `run_market_scanner` tool. This tool handles the anti-bot delays and saves the data directly
    into the database. Ensure you ask the user for a start and end date if they are not provided, or infer them.
    Always inform the user when the scan has completed, and specifically state the exact time taken (in seconds or minutes)
    to finish the operation, which is returned by the tool.""",
    tools=[run_market_scanner]
)

price_lookup_agent = LlmAgent(
    name="price_lookup_agent",
    model=Gemini(model="gemini-flash-latest"),
    instruction="""You are the Airbnb Price Lookup Assistant. Your job is to answer queries like "What is the rate for this period for apartment X?".
    Use the `read_airbnb_data` tool to check the processed rates in the database.
    You can map the following names to apartment IDs:
    - Mauro: 1589943047991118285
    - Stefania: 602489771443051475
    - Ugo: 1280484040857767756
    - Navona: 1243259212458138393
    - Elegante: 2153298
    - Perla: 1105673287932582735
    - Barbara: 14159837
    - Blue Navona: 14290915
    - Junior Suite: 4050526

    Return the nightly rate and any other relevant info (like minStay or specialOffer).""",
    tools=[read_airbnb_data]
)

price_recommender = LlmAgent(
    name="price_recommender",
    model=Gemini(model="gemini-flash-latest"),
    instruction="""You are the Airbnb Pricing Consultant. Your job is to analyze historical and current
    pricing data from the JSON database using the `read_airbnb_data` tool and recommend the best nightly
    rate for the user's apartment for a specific date or period. Take into account how prices change
    over time based on the `collected_at` timestamp vs the `target_date`.""",
    tools=[read_airbnb_data]
)

competitive_analyzer = LlmAgent(
    name="competitive_analyzer",
    model=Gemini(model="gemini-flash-latest"),
    instruction="""You are the Airbnb Competitive Analyst. Your job is to analyze the data from the
    JSON database using the `read_airbnb_data` tool to provide a competitive analysis of apartments
    in the market. Identify trends, high and low prices, and positioning.""",
    tools=[read_airbnb_data]
)

general_agent = LlmAgent(
    name="general_agent",
    model=Gemini(model="gemini-flash-latest"),
    instruction="You are a helpful assistant for an Airbnb host. Clarify what the user wants to do with their Airbnb data: update database, look up a price, ask for a price recommendation, or request a competitive analysis."
)

# 3. Workflow Graph Definition
root_agent = Workflow(
    name="mr_airbnb",
    edges=[
        ('START', classifier),
        (classifier, {
            "update_db": scanner_agent,
            "lookup_price": price_lookup_agent,
            "recommend_price": price_recommender,
            "competitive_analysis": competitive_analyzer,
            DEFAULT_ROUTE: general_agent
        })
    ],
    description="An AI consultant for analyzing and recommending Airbnb prices.",
)

app = App(
    root_agent=root_agent,
    name="app",
)
