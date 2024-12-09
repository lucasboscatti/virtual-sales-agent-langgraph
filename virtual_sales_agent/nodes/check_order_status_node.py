import json
import os
import sys
from contextlib import closing
from typing import Dict

from virtual_sales_agent.nodes.state import State

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.utils.database_functions import get_connection


def check_order_status_state(state: State) -> Dict[str, str]:
    """Check the status of an order.

    Arguments:
        state (State): The state of the graph.

    Returns:
        Dict[str, str]: The graph state with the order information.
    """
    tool_messages = json.loads(state["messages"][-1].content)
    order_id = tool_messages.get("OrderId", None)
    customer_id = tool_messages.get("CustomerId")

    if order_id:
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
            state["messages"][-1].content = json.dumps(
                {"error": "Pedido não encontrado"}
            )

    else:
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
                {"error": "Nenhum pedido encontrado para este cliente"}
            )

    return state
