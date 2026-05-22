from google.adk import Agent
from mcp_server import mcp

# We get the direct functions from your mcp server safely here
try:
    tools_list = [tool.fn for tool in mcp.list_tools_sync()]
except Exception:
    tools_list = []

github_agent = Agent(
    name="github_dev_card_agent", 
    instruction="You are a creative assistant that generates GitHub developer cards. Use the provided tools.",
    model="gemini-2.0-flash",
    tools=tools_list
)