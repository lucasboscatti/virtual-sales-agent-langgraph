import json
import os
import sys
from contextlib import closing
from datetime import datetime

from virtual_sales_agent.nodes.state import State

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.utils.database_functions import get_connection


def create_order_state(state: State) -> State:
    return state


def check_product_quantity_state(state: State) -> State:
    tool_messages = json.loads(state["messages"][-1].content)
    products = tool_messages.get("Products")
    state["products_availability"] = {}

    with get_connection() as conn:
        with closing(conn.cursor()) as cursor:
            for product in products:
                product_name = product["ProductName"].lower()
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
                product_name = product["ProductName"].lower()
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
                product_name = product["ProductName"].lower()
                quantity = product["Quantity"]
                cursor.execute(
                    "UPDATE products SET Quantity = Quantity - ? WHERE ProductName = ?",
                    (quantity, product_name),
                )

    return state
