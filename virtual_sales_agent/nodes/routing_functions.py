import json
from typing import Literal

from langchain_core.messages import ToolMessage

from virtual_sales_agent.nodes.state import State


def route_tool(
    state: State,
) -> ToolMessage:
    """Route the message to the appropriate tool.

    Arguments:
        state (State): The state of the graph.

    Returns:
        ToolMessage: The message to send to the tool.
    """
    return state["messages"][-1]


def routing_fuction(
    state: State,
) -> Literal[
    "query_products_info_state",
    "create_order_state",
    "check_order_status_state",
    "search_products_recommendations_state",
    "escalate_to_employee_state",
]:
    """Routing function for the graph.

    Arguments:
        state (State): The state of the graph.

    Returns:
        Literal["query_products_info_state", "create_order_state", "check_order_status_state", "search_products_recommendations_state", "escalate_to_employee_state"]: The next node to call.
    """
    return state["messages"][-1].name + "_state"


def route_validate_product_name(
    state: State,
) -> Literal["check_product_quantity_state", "assistant"]:
    """Validate the product name.

    Arguments:
        state (State): The state of the graph.

    Returns:
        Literal["check_product_quantity_state", "assistant"]: The next node to call.
    """
    if any(value == "no" for value in state["valid_products"].values()):
        for product_name, availability in state["valid_products"].items():
            if availability == "no":
                tool_messages = {
                    "Availability": "Produto: "
                    + product_name
                    + " não disponível no estoque"
                }
                state["messages"][-1].content = json.dumps(tool_messages)
        return "assistant"
    return "check_product_quantity_state"


def route_create_order(state: State) -> Literal["add_order_state", "assistant"]:
    """Route to validate product quantity.

    Arguments:
        state (State): The state of the graph.

    Returns:
        Literal["add_order_state", "assistant"]: The next node to call.
    """
    if any(value == "no" for value in state["products_availability"].values()):
        for product_name, availability in state["products_availability"].items():
            if availability == "no":
                tool_messages = {
                    "Availability": "Quantidade insuficiente do produto: "
                    + product_name
                }
                state["messages"][-1].content = json.dumps(tool_messages)
        return "assistant"
    return "add_order_state"
