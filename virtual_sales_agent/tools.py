from typing import Any, Dict, List, Union

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool


@tool
def query_products(user_message: str) -> Dict[str, str]:
    """
    Creates a query to the products table based on the user's message.
    """
    return {"user_message": user_message}


@tool
def create_order(
    products: List[Dict[str, Any]], *, config: RunnableConfig
) -> Dict[str, str]:
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
def search_products_recommendations(config: RunnableConfig) -> Dict[str, str]:
    """Searches for products recommendations"""
    configuration = config.get("configurable", {})
    customer_id = configuration.get("customer_id", None)

    if not customer_id:
        return ValueError("No customer ID configured.")

    return {"CustomerId": customer_id}
