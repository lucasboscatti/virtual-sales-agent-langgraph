from typing import Dict, List

from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableLambda
from langgraph.prebuilt import ToolNode

from virtual_sales_agent.nodes.state import State


def handle_tool_error(state: State) -> Dict[str, List[ToolMessage]]:
    """Handles tool errors.

    Arguments:
        state (State): The state of the graph.

    Returns:
        Dict[str, List[ToolMessage]]: The messages to send to the user.
    """
    error = state.get("error")
    tool_calls = state["messages"][-1].tool_calls
    return {
        "messages": [
            ToolMessage(
                content=f"Error: {repr(error)}\n please fix your mistakes.",
                tool_call_id=tc["id"],
            )
            for tc in tool_calls
        ]
    }


def create_tool_node_with_fallback(tools: list) -> ToolNode:
    """Creates a tool node with fallbacks.
    
    Arguments:
        tools (list): The tools to create the node with.
    
    Returns:
        ToolNode: The tool node with fallbacks.
    """
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )
