from typing import Any, Dict, List, Union

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool


@tool
def query_products_info(user_message: str) -> Dict[str, str]:
    """
    Buscas informações sobre produtos

    Arguments:
        user_message (str): Mensagem do usuário em linguagem natural

    example:
        query_products_info("Qual produto mais caro?")
    """
    return {"user_message": user_message}


@tool
def create_order(
    products: List[Dict[str, Any]], *, config: RunnableConfig
) -> Dict[str, str]:
    """
    Cria um novo pedido (compra de produtos) para o cliente.

    Arguments:
        products (List[Dict[str, Any]]): A lista de produtos a serem comprados.

    Returns:
        str: Order ID

    Example:
        create_order([{"ProductName": "Produto A", "Quantity": 2}, {"ProductName": "Produto B", "Quantity": 1}])
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
    Verifica o status de um pedido específico ou todos os pedidos do cliente.

    Arguments:
        order_id (Union[str, None]): o ID do pedido a ser verificado. Se nulo, todos os pedidos do cliente serão retornados.
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
    """Busca por recomendações de produtos para o cliente."""
    configuration = config.get("configurable", {})
    customer_id = configuration.get("customer_id", None)

    if not customer_id:
        return ValueError("No customer ID configured.")

    return {"CustomerId": customer_id}


@tool
def escalate_to_employee(config: RunnableConfig) -> Dict[str, str]:
    """Escala o atendimento para atendente humano se o cliente pedir ou se você não está conseguindo ajudar o cliente."""
    configuration = config.get("configurable", {})
    customer_id = configuration.get("customer_id", None)

    if not customer_id:
        return ValueError("No customer ID configured.")

    return {"CustomerId": customer_id}
