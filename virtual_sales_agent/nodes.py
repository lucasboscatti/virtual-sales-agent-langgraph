import json
import os
import sys
from contextlib import closing
from datetime import datetime
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

        return {
            "messages": result,
            "tool_calls": result.tool_calls,
        }


def route_tool(
    state: State,
) -> ToolMessage:
    return state["messages"][-1]


def get_products_state(state: State) -> State: ...


def create_order_state(state: State) -> State:
    return state


def check_product_quantity_state(state: State) -> State:
    tool_messages = json.loads(state["messages"][-1].content)
    products = tool_messages.get("Products")
    state["products_availability"] = {}

    with get_connection() as conn:
        with closing(conn.cursor()) as cursor:
            for product in products:
                product_name = product["ProductName"]
                product_quantity = product["Quantity"]
                cursor.execute(
                    "SELECT Quantity FROM products WHERE ProductName = ?",
                    (product_name,),
                )
                result = cursor.fetchone()
                if result:
                    if result[0] < product_quantity:
                        state["products_availability"][product_name] = "no"
                    else:
                        state["products_availability"][product_name] = "yes"
    return state


def add_order_state(state: State) -> State:
    tool_messages = json.loads(state["messages"][-1].content)
    customer_id = tool_messages.get("CustomerId")
    products = tool_messages.get("Products")

    with get_connection() as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(
                "INSERT INTO orders (CustomerId, OrderDate, Status) VALUES (?, ?, ?)",
                (customer_id, datetime.now(), "Pending"),
            )
            order_id = cursor.lastrowid

            for product in products:
                product_name = product["ProductName"]
                product_quantity = product["Quantity"]
                cursor.execute(
                    "SELECT ProductId, Price FROM products WHERE ProductName = ?",
                    (product_name,),
                )
                product_data = cursor.fetchone()

                if not product_data:
                    raise ValueError(f"Product {product_name} not found.")

                product_id, price = product_data

                cursor.execute(
                    "INSERT INTO orders_details (OrderId, ProductId, Quantity, UnitPrice) VALUES (?, ?, ?, ?)",
                    (order_id, product_id, product_quantity, price),
                )

    tool_messages["OrderId"] = order_id
    state["messages"][-1].content = json.dumps(tool_messages)
    return state


def subtract_quantity_state(state: State) -> State:
    tool_messages = json.loads(state["messages"][-1].content)
    products = tool_messages.get("Products")

    with get_connection() as conn:
        with closing(conn.cursor()) as cursor:
            for product in products:
                product_name = product["ProductName"]
                quantity = product["Quantity"]
                cursor.execute(
                    "UPDATE products SET Quantity = Quantity - ? WHERE ProductName = ?",
                    (quantity, product_name),
                )

    return state


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


def search_products_recommendations_state(state: State):
    tool_messages = json.loads(state["messages"][-1].content)
    customer_id = tool_messages.get("CustomerId")

    query = """
    WITH RecentOrders AS (
    SELECT 
        od.ProductId, 
        p.Category, 
        COUNT(od.ProductId) AS ProductFrequency
    FROM orders o
    INNER JOIN orders_details od ON o.OrderId = od.OrderId
    INNER JOIN products p ON od.ProductId = p.ProductId
    WHERE o.CustomerId = ? -- Replace with the target customer ID
    ORDER BY o.OrderDate DESC
    LIMIT 5
    ),
    TopCategories AS (
        SELECT 
            Category, 
            COUNT(Category) AS CategoryFrequency
        FROM RecentOrders
        GROUP BY Category
        ORDER BY CategoryFrequency DESC
    ),
    RecommendedProducts AS (
        SELECT 
            ProductId, 
            ProductName, 
            Category, 
            Description, 
            Price 
        FROM products
        WHERE Category IN (SELECT Category FROM TopCategories)
        AND ProductId NOT IN (SELECT ProductId FROM RecentOrders)
    )
    SELECT * FROM RecommendedProducts
    LIMIT 10;
    """
    with get_connection() as conn:
        with closing(conn.cursor()) as cursor:
            # Only pass one parameter as the query uses one placeholder
            cursor.execute(query, (customer_id,))
            results = cursor.fetchall()  # Use fetchall to handle multiple rows

    # Process results into a list of dictionaries
    recommendations = [
        {
            "ProductId": row[0],
            "ProductName": row[1],
            "Category": row[2],
            "Description": row[3],
            "Price": row[4],
        }
        for row in results
    ]
    state["messages"][-1].content = json.dumps(recommendations)
    return state


def routing_fuction(
    state: State,
) -> Literal[
    "get_products_state",
    "create_order_state",
    "check_order_status_state",
    "search_products_recommendations_state",
]:
    return state["messages"][-1].name + "_state"


def route_create_order(state: State) -> Literal["add_order_state", "assistant"]:
    print("STATE", state)
    if any(value == "no" for value in state["products_availability"].values()):
        for product_name, availability in state["products_availability"].items():
            if availability == "no":
                tool_messages = {
                    "Availability": "No quantity available for product: " + product_name
                }
                state["messages"][-1].content = json.dumps(tool_messages)
        return "assistant"
    return "add_order_state"
