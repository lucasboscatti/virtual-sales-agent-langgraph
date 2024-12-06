import os
import sqlite3
import sys
from contextlib import closing
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.utils.database_functions import get_connection


@tool
def query_products() -> List[Dict[str, Any]]:
    """
    Shows all available products
    """
    query = """
    SELECT
        p.ProductId,
        p.ProductName,
        p.Category,
        p.Description,
        p.Price,
        p.Quantity
    FROM Products p
    WHERE 1=1
    """

    with get_connection() as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(query)
            columns = [column[0] for column in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return results


@tool
def create_order(products: List[Dict[str, Any]], config: RunnableConfig) -> str:
    """Creates a new order"""

    configuration = config.get("configurable", {})
    customer_id = configuration.get("customer_id", None)

    if not customer_id:
        return ValueError("No customer ID configured.")

    order_query = """
    INSERT INTO Orders (CustomerId, OrderDate, Status)
    VALUES (?, datetime('now'), 'Pending');
    """
    order_details_query = """
    INSERT INTO OrderDetails (OrderId, ProductId, Quantity, UnitPrice)
    VALUES (?, ?, ?, ?);
    """
    with get_connection() as conn:
        with closing(conn.cursor()) as cursor:
            # Step 1: Insert the new order
            cursor.execute(order_query, (customer_id,))
            order_id = cursor.lastrowid  # Get the ID of the newly created order

            # Step 2: Insert order details
            for product in products:
                cursor.execute(
                    order_details_query,
                    (
                        order_id,
                        product["ProductId"],
                        product["Quantity"],
                        product["UnitPrice"],
                    ),
                )

            # Commit the transaction
            conn.commit()

            return "Order created successfully with order ID: " + str(order_id)


@tool
def check_order_status(
    order_id, config: RunnableConfig
) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Checks the status of orders for a specific customer.
    """
    configuration = config.get("configurable", {})
    customer_id = configuration.get("customer_id", None)

    if not customer_id:
        return ValueError("No customer ID configured.")

    if order_id:
        # Query to fetch a specific order's details for the customer
        query = """
        SELECT 
            o.OrderId, 
            o.Status, 
            o.OrderDate
        FROM Orders o
        WHERE o.CustomerId = ? AND o.OrderId = ?;
        """
        with get_connection() as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(query, (customer_id, order_id))
                result = cursor.fetchone()

        if result:
            return {"OrderId": result[0], "Status": result[1], "OrderDate": result[2]}
        else:
            return {"error": "Order not found for the given criteria."}
    else:
        # Query to fetch all orders for the customer
        query = """
        SELECT 
            o.OrderId, 
            o.Status, 
            o.OrderDate
        FROM Orders o
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
            return orders
        else:
            return {"error": "No orders found for the given customer."}


@tool
def search_products_recommendations(config: RunnableConfig) -> List[Dict[str, Any]]:
    """Searches for products recommendations"""
    configuration = config.get("configurable", {})
    customer_id = configuration.get("customer_id", None)

    if not customer_id:
        return ValueError("No customer ID configured.")

    query = """
    SELECT 
        p.ProductName, 
        p.Description, 
        p.Price
    FROM Products p
    WHERE p.ProductId IN (
        SELECT od.ProductId
        FROM OrderDetails od
        JOIN Orders o ON od.OrderId = o.OrderId
        WHERE o.CustomerId = ?
        GROUP BY od.ProductId
        ORDER BY SUM(od.Quantity) DESC
        LIMIT 10
    )
    OR p.ProductId IN (
        SELECT od.ProductId
        FROM OrderDetails od
        JOIN Orders o ON od.OrderId = o.OrderId
        WHERE o.CustomerId != ?
        GROUP BY od.ProductId
        ORDER BY SUM(od.Quantity) DESC
        LIMIT 10
    );
    """
    with get_connection() as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(query, (customer_id, customer_id))
            results = cursor.fetchall()

    # Process results into a list of dictionaries
    recommendations = [
        {"ProductName": row[0], "Description": row[1], "Price": row[2]}
        for row in results
    ]
    return recommendations
