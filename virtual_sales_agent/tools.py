import os
import sys
from contextlib import closing
from typing import Any, Dict, List, Union

from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from typing_extensions import Annotated, TypedDict

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langchain import hub

from database.utils.database_functions import get_connection

query_prompt_template = hub.pull("langchain-ai/sql-query-system-prompt")

llm = ChatGroq(model="llama-3.1-70b-versatile", temperature=0)


def get_engine_for_chinook_db() -> Engine:
    """
    Creates an SQLAlchemy engine for the chinook database.

    Returns:
        Engine: An SQLAlchemy engine object.
    """

    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, "../database/db/chinook.db")

    db_uri = f"sqlite:///{db_path}"
    return create_engine(
        db_uri,
    )


class QueryOutput(TypedDict):
    """Generated SQL query."""

    query: Annotated[str, ..., "Syntactically valid SQL query."]


@tool
def query_products(user_message: str) -> List[Dict[str, Any]]:
    """
    Creates a query to the products table based on the user's message.
    """
    engine = get_engine_for_chinook_db()
    db = SQLDatabase(engine)
    prompt = query_prompt_template.invoke(
        {
            "dialect": db.dialect,
            "top_k": 10,
            "table_info": db.get_table_info(table_names=["products"]),
            "input": user_message,
        }
    )
    structured_llm = llm.with_structured_output(QueryOutput)
    result = structured_llm.invoke(prompt)

    execute_query_tool = QuerySQLDataBaseTool(db=db)
    return execute_query_tool.invoke(result["query"])


@tool
def create_order(products: List[Dict[str, Any]], *, config: RunnableConfig) -> str:
    """Creates a new order when the customer wants to buy products

    Args:
        products (List[Dict[str, Any]]): List of products to be included in the order

    Returns:
        str: Order ID

    Example:
        create_order([{"ProductName": "Product A", "Quantity": 2}, {"ProductName": "Product B", "Quantity": 1}])
        >>> "Order created successfully with order ID: 123"
    """

    configuration = config.get("configurable", {})
    customer_id = configuration.get("customer_id", None)

    if not customer_id:
        return ValueError("No customer ID configured.")

    order_query = """
    INSERT INTO orders (CustomerId, OrderDate, Status)
    VALUES (?, datetime('now'), 'Pending');
    """
    order_details_query = """
    INSERT INTO orders_details (OrderId, ProductId, Quantity, UnitPrice)
    VALUES (?, ?, ?, ?);
    """
    get_product_query = """
    SELECT ProductId, Price FROM products WHERE ProductName = ?;
    """
    subtract_quantity_query = """
    UPDATE products
    SET Quantity = Quantity - ?
    WHERE ProductName = ?;
    """

    with get_connection() as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(order_query, (customer_id,))
            order_id = cursor.lastrowid

            for product in products:
                cursor.execute(get_product_query, (product["ProductName"],))
                product_data = cursor.fetchone()

                if not product_data:
                    raise ValueError(f"Product not found: {product['ProductName']}")

                product_id, unit_price = product_data
                quantity = product["Quantity"]

                cursor.execute(
                    order_details_query,
                    (order_id, product_id, quantity, unit_price),
                )

                cursor.execute(
                    subtract_quantity_query,
                    (quantity, product["ProductName"]),
                )
            conn.commit()

            return f"Order created successfully with order ID: {order_id}"


@tool
def check_order_status(
    order_id: Union[str, None], *, config: RunnableConfig
) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Checks the status of orders for a specific customer.

    Args:
        order_id (Union[str, None]): The ID of the specific order to check. If not provided, all orders for the customer will be returned.

    Returns:
        Union[List[Dict[str, Any]], Dict[str, Any]]: A list of dictionaries containing order details if no order_id is provided,
        or a dictionary containing details of the specific order if an order_id is provided.
        Each dictionary includes the following keys:
        - OrderId: The ID of the order
        - Status: The current status of the order
        - OrderDate: The date the order was placed
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
        FROM orders o
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
