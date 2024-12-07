import json
import os
import sys
from contextlib import closing
from typing import Annotated, Dict, Literal

from langchain_core.messages import ToolMessage
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.graph.message import AnyMessage, add_messages
from typing_extensions import TypedDict

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.utils.database_functions import get_connection


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: State, config: RunnableConfig):
        while True:
            configuration = config.get("configurable", {})
            passenger_id = configuration.get("customer_id", None)
            state = {**state, "user_info": passenger_id}
            result = self.runnable.invoke(state)
            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break
        return {"messages": result, "tool_calls": result.tool_calls}


def route_tool(
    state: State,
) -> ToolMessage:
    return state["messages"][-1]


def get_products_state(state: State): ...


def create_order_state(state: State): ...


## see available products
## if product is available, add to order
## subtract quantity
## if product quantity is not available
## return no quantity


def check_order_status_state(state: State) -> Dict[str, str]:
    tool_messages = json.loads(state["messages"][-1].content)
    order_id = tool_messages.get("OrderId", None)
    customer_id = tool_messages.get("CustomerId")

    if order_id:
        # Query to fetch a specific order's details for the customer
        query = """
        SELECT 
            o.OrderId, 
            o.Status, 
            o.OrderDate
        FROM orders o
        WHERE o.CustomerId = ? AND o.OrderId = ?;
        """
        with get_connection() as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(query, (customer_id, order_id))
                result = cursor.fetchone()

        if result:
            state["messages"][-1].content = json.dumps(result)
        else:
            state["messages"][-1].content = json.dumps({"error": "Order not found."})

    else:
        # Query to fetch all orders for the customer
        query = """
        SELECT 
            o.OrderId, 
            o.Status, 
            o.OrderDate
        FROM orders o
        WHERE o.CustomerId = ?
        ORDER BY o.OrderDate DESC;
        """
        with get_connection() as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(query, (customer_id,))
                results = cursor.fetchall()

        if results:
            orders = [
                {"OrderId": row[0], "Status": row[1], "OrderDate": row[2]}
                for row in results
            ]
            state["messages"][-1].content = json.dumps(orders)
        else:
            state["messages"][-1].content = json.dumps(
                {"error": "No orders found for the given customer."}
            )

    return state


def search_products_recommendations_state(state: State): ...


def routing_fuction(
    state: State,
) -> Literal[
    "get_products_state",
    "create_order_state",
    "check_order_status_state",
    "search_products_recommendations_state",
]:
    return state["messages"][-1].name + "_state"
