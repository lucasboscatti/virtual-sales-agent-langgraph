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

    return {"Products": products, "CustomerId": customer_id}


@tool
def check_order_status(
    order_id: Union[str, None], *, config: RunnableConfig
) -> Dict[str, Union[str, None]]:
    """
    Checks the status of orders for a specific customer.

    Args:
        order_id (Union[str, None]): The ID of the specific order to check. If not provided, all orders for the customer will be returned.

    Returns:
        Dict[str:str]: A dictionary containing the order ID and the Customer ID.
    """
    configuration = config.get("configurable", {})
    customer_id = configuration.get("customer_id", None)

    if not customer_id:
        return ValueError("No customer ID configured.")

    if order_id:
        return {"OrderId": order_id, "CustomerId": customer_id}
    else:
        return {"OrderId": None, "CustomerId": customer_id}


@tool
def search_products_recommendations(config: RunnableConfig) -> List[Dict[str, Any]]:
    """Searches for products recommendations"""
    configuration = config.get("configurable", {})
    customer_id = configuration.get("customer_id", None)

    if not customer_id:
        return ValueError("No customer ID configured.")

    return {"CustomerId": customer_id}
