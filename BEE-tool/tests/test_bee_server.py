"""This script creates an AI Agent and tests whether the bee_server 
works properly"""

import asyncio
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain_core.messages import convert_to_messages
from langgraph.checkpoint.memory import InMemorySaver

from langchain.tools import tool

SERVER_PATH = Path(__file__).resolve().parent.parent/"MCP"/"bee_server.py"

# Create an MCP client configuration that points to the local BEE server
client = MultiServerMCPClient(
    {
        "BEE":{
            "command": "python",
            "args": [str(SERVER_PATH)],
            "transport": "stdio",
        }
    }
)

def pretty_print(response):
    """Convert a sequence of messages into a list of messages 
        and print it in a human-readable format"""
    format_message = convert_to_messages(response["messages"])
    for message in format_message:
        message.pretty_print()

@tool
async def read_BEE_docs() -> str:
    """Read BEE Documentation."""
    blobs  = await client.get_resources("BEE", uris=["https://BEE/docs"])
    return blobs[0].as_string()


async def main():
    """Connect to the MCP server, create an agent to call the available 
        tools, and print the results"""

    tools = await client.get_tools()

    print("The following tools are available: ")
    for tool in tools:
        print(f"  - {tool.name}")
    
    agent = create_agent(
            model="gpt-oss-120b",
            tools=[*tools,read_BEE_docs],
            checkpointer=InMemorySaver()
    )

    # thread that remembers interactions within a single conversation
    thread_config = {"configurable": {"thread_id": "1"}}

    print("\n=== Submitting Workflow ===")
    submit_response = await agent.ainvoke(
        {"messages": [{
            "role": "user",
            "content": "Submit this workflow: cat, cat-grep-tar.tgz, workflow.cwl, "
                       "input.yml,input.yml,test_workdir\n"
                       "Make sure to capture the response and extract "
                       "the workflow ID." }]}, thread_config)

    pretty_print(submit_response)

    print("\n=== Querying Workflow ===")
    query_response = await agent.ainvoke(
        {"messages": [{
            "role": "user",
            "content": "Using the workflow id you extracted when submitting the workflow,\n"
                       "Call query_workflow to fetch its current status." }]}, thread_config)

    pretty_print(query_response)

    print("\n=== Canceling Workflow ===")
    cancel_response = await agent.ainvoke(
        {"messages": [{
            "role": "user",
            "content": "Using the workflow id you extracted when submitting the workflow,\n"
                       "Call cancel_workflow to cancel the submitted workflow"}]}, thread_config)

    pretty_print(cancel_response)

    print("\n=== Listing all Workflows ===")
    list_response = await agent.ainvoke(
            {"messages": [{
                "role":"user",
                "content":"Can you list all the workflows"}]}, thread_config)
    pretty_print(list_response)

    print("\n=== Fetching a Resource ===")
    resource_response = await agent.ainvoke(
            {"messages": [{
                "role": "user",
                "content": "Can you read the documentation for BEE. More"
                           "specifically, can you read the example section."
                           "DO NOT GIVE ME THE CONTENTS OF THE ENTIRE DOCUMENTATION."
                           "DO NOT GIVE ME HTML OF THE DOCUMENTATION"
                           "Do NOT make up your own commands. Give me exactly what the"
                           "two example workflows are and what the associated commands are"
                           "DIRECTLY from the BEE documentation. JUST focus on the two"
                           "workflows and the commands necessary to run them. Give me a"
                           "step by step checklist on how to run general workflows after"
                           "that. An example command is beeflow core start for starting"
                           "the BEE daemon."}]}, thread_config)
    pretty_print(resource_response)

    print("\nTest completed successfully")

if __name__ == "__main__":
    asyncio.run(main())
