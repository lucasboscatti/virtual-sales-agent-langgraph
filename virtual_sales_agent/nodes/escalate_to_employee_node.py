import json
import os
import sys
from contextlib import closing
from typing import Dict

from virtual_sales_agent.nodes.state import State

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.utils.database_functions import get_connection


def escalate_to_employee_state(state: State) -> Dict[str, str]:
    """Escalate the order to an employee.

    Arguments:
        state (State): The state of the graph.

    Returns:
        Dict[str, str]: The graph state with the employee information.
    """
    tool_messages = json.loads(state["messages"][-1].content)
    customer_id = tool_messages.get("CustomerId", None)

    query = """
    SELECT LastName, FirstName, Email
    FROM employees
    WHERE Title = 'Sales Support Agent'
    ORDER BY RANDOM()
    LIMIT 1;
    """

    with closing(get_connection()) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(query)
            result = cursor.fetchone()

            state["messages"][-1].content = json.dumps(
                {
                    "Employee": {
                        "LastName": result[0],
                        "FirstName": result[1],
                        "Email": result[2],
                    },
                    "CustomerId": customer_id,
                }
            )

            return state
