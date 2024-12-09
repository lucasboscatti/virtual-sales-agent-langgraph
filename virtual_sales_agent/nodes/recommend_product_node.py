import json
import os
import sys
from contextlib import closing
from typing import Dict

from virtual_sales_agent.nodes.state import State

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.utils.database_functions import get_connection


def search_products_recommendations_state(state: State) -> Dict[str, str]:
    """Search for products recommendations.

    Arguments:
        state (State): The state of the graph.

    Returns:
        Dict[str, str]: The graph state with the recommendations.
    """
    tool_messages = json.loads(state["messages"][-1].content)
    customer_id = tool_messages.get("CustomerId")

    query = """
    WITH RecentOrders AS (
    SELECT 
        od.ProductId, 
        p.Category AS Category, 
        COUNT(od.ProductId) AS ProductFrequency
    FROM orders o
    INNER JOIN orders_details od ON o.OrderId = od.OrderId
    INNER JOIN products p ON od.ProductId = p.ProductId
    WHERE o.CustomerId = ?
    GROUP BY od.ProductId, p.Category
    ORDER BY MAX(o.OrderDate) DESC
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
            p.ProductId, 
            p.ProductName, 
            p.Category, 
            p.Description, 
            p.Price,
            ROW_NUMBER() OVER (PARTITION BY p.Category ORDER BY p.Price DESC) AS Rank
        FROM products p
        WHERE p.Category IN (SELECT Category FROM TopCategories)
        AND p.ProductId NOT IN (SELECT ProductId FROM RecentOrders)
    )
    SELECT 
        ProductId, 
        ProductName, 
        Category, 
        Description, 
        Price
    FROM RecommendedProducts
    WHERE Rank <= 5;
    """
    with get_connection() as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(query, (customer_id,))
            results = cursor.fetchall()

            if results:
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
            else:
                recommendations = {
                    "recommendations": "Este cliente não possui pedidos recentes."
                }
    state["messages"][-1].content = json.dumps(recommendations)
    return state
