import json
from typing import Literal

from langchain_core.messages import ToolMessage
from state import State


def route_tool(
    state: State,
) -> ToolMessage:
    return state["messages"][-1]


def routing_fuction(
    state: State,
) -> Literal[
    "query_products_info_state",
    "create_order_state",
    "check_order_status_state",
    "search_products_recommendations_state",
]:
    return state["messages"][-1].name + "_state"


def route_create_order(state: State) -> Literal["add_order_state", "assistant"]:
    if any(value == "no" for value in state["products_availability"].values()):
        for product_name, availability in state["products_availability"].items():
            if availability == "no":
                tool_messages = {
                    "Availability": "No quantity available for product: " + product_name
                }
                state["messages"][-1].content = json.dumps(tool_messages)
        return "assistant"
    return "add_order_state"
