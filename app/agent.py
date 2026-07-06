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

def load_competitor_context():
    mapping_str = ""
    user_apt_id = "1589943047991118285"
    try:
        comp_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "competitors.txt")
        with open(comp_file, "r", encoding="utf-8") as f:
            for line in f:
                if ":" in line:
                    parts = line.strip().split(":", 2)
                    if len(parts) == 3:
                        apt_id, fee, name = parts
                        mapping_str += f"\n    - {name}: {apt_id}"
                        if "USER'S APARTMENT" in name:
                            user_apt_id = apt_id
    except Exception:
        pass
    return mapping_str, user_apt_id

COMPETITOR_MAPPING, USER_APT_ID = load_competitor_context()

# Auth initialization
import truststore
truststore.inject_into_ssl()

# Force the use of the free Gemini API (AI Studio) instead of Vertex AI to avoid billing errors
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"
if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
    del os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
if "GOOGLE_CLOUD_PROJECT" in os.environ:
    del os.environ["GOOGLE_CLOUD_PROJECT"]

# Create a global client forcing the API key to bypass any other credentials
api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
global_client = genai.Client(api_key=api_key)

# =====================================================================
# KAGGLE KEY CONCEPT: Agent / Multi-agent system (ADK)
# This file implements a Graph-based Multi-Agent architecture.
# It uses a Semantic Router (Classifier Node) to delegate tasks to 
# specialized sub-agents (Scanner, Lookup, Recommender).
# =====================================================================

# 1. Classifier Node
@node
def classifier(node_input: str):
    """
    Semantic Router Node:
    Instead of rigid command parsing, this node uses Gemini 2.5 Flash
    to semantically understand the user's intent in natural language
    and route the execution flow to the correct specialized sub-agent.
    """
    client = global_client
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

# 2. Sub-Agents (Specialized Roles)
# Here we demonstrate the power of Multi-Agent delegation. Each LlmAgent
# has a specific system prompt and access to specific tools.
scanner_agent = LlmAgent(
    name="scanner_agent",
    model=Gemini(model="gemini-flash-latest", client=global_client),
    instruction="""You are the Airbnb Data Scanner. Your job is to fetch the latest Airbnb listing details
    by running the `run_market_scanner` tool. This tool handles the anti-bot delays and saves the data directly
    into the database. Ensure you ask the user for a start and end date if they are not provided, or infer them.
    Always inform the user when the scan has completed, and specifically state the exact time taken (in seconds or minutes) to finish the operation, which is returned by the tool.
    STRICT RULE: You must ONLY use the tools explicitly provided to you. Do NOT attempt to use unlisted tools like 'view_file'.""",
    tools=[run_market_scanner]
)

price_lookup_agent = LlmAgent(
    name="price_lookup_agent",
    model=Gemini(model="gemini-flash-latest", client=global_client),
    instruction=f"""You are the Airbnb Price Lookup Assistant. Your job is to answer queries like "What is the rate for this period for apartment X?".
    Use the `read_airbnb_data` tool to check the processed rates in the database.
    You can map the following names to apartment IDs:{COMPETITOR_MAPPING}

    Return the nightly rate and any other relevant info (like minStay or specialOffer).
    STRICT RULE: You must ONLY use the tools explicitly provided to you. Do NOT attempt to use unlisted tools like 'view_file'.""",
    tools=[read_airbnb_data]
)

price_recommender = LlmAgent(
    name="price_recommender",
    model=Gemini(model="gemini-flash-latest", client=global_client),
    instruction=f"""You are the Airbnb Pricing Consultant. Your job is to analyze historical and current
    pricing data from the JSON database using the `read_airbnb_data` tool and recommend the best nightly
    rate for the user's apartment for a specific date or period. Take into account how prices change
    over time based on the `collected_at` timestamp vs the `target_date`.
    
    CRITICAL CONTEXT: The user's apartment (referred to as 'my apartment', 'mi departamento', 'Mauro') is ID: {USER_APT_ID}.
    STRICT RULE: You must ONLY use the tools explicitly provided to you. Do NOT attempt to use unlisted tools like 'view_file'.""",
    tools=[read_airbnb_data]
)

competitive_analyzer = LlmAgent(
    name="competitive_analyzer",
    model=Gemini(model="gemini-flash-latest", client=global_client),
    instruction=f"""You are the Airbnb Competitive Analyst. Your job is to analyze the data from the
    JSON database using the `read_airbnb_data` tool to provide a competitive analysis of apartments
    in the market. Identify trends, high and low prices, and positioning.
    
    CRITICAL CONTEXT: The user's apartment (referred to as 'my apartment', 'mi departamento', 'Mauro') is ID: {USER_APT_ID}.
    STRICT RULE: You must ONLY use the tools explicitly provided to you. Do NOT attempt to use unlisted tools like 'view_file'.""",
    tools=[read_airbnb_data]
)

general_agent = LlmAgent(
    name="general_agent",
    model=Gemini(model="gemini-flash-latest", client=global_client),
    instruction="You are a helpful assistant for an Airbnb host. Clarify what the user wants to do with their Airbnb data: update database, look up a price, ask for a price recommendation, or request a competitive analysis."
)

# 3. Workflow Graph Definition
# This defines the directed graph for our Multi-Agent system.
# The user's input always hits the 'classifier' first, which then
# branches out (routes) to the specialized agents based on intent.
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
