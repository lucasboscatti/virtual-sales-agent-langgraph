import json
import os
from typing import Annotated, Dict

from dotenv import load_dotenv
from langchain import hub
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_community.utilities import SQLDatabase
from langchain_groq import ChatGroq
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from typing_extensions import Annotated, TypedDict

from virtual_sales_agent.nodes.state import State

load_dotenv()

query_prompt_template = hub.pull("langchain-ai/sql-query-system-prompt")

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)


def get_engine_for_chinook_db() -> Engine:
    """
    Creates an SQLAlchemy engine for the chinook database.

    Returns:
        Engine: An SQLAlchemy engine object.
    """

    script_dir = os.path.dirname(os.path.abspath(""))
    db_path = os.path.join(script_dir, "vendedor_virtual/database/db/chinook.db")
    db_uri = f"sqlite:///{db_path}"
    return create_engine(
        db_uri,
    )


class QueryOutput(TypedDict):
    """Generated SQL query."""

    query: Annotated[str, ..., "Syntactically valid SQL query."]


def query_products_info_state(state: State) -> Dict[str, str]:
    """Create a SQL query based on the user's message.

    Arguments:
        state (State): The state of the graph.

    Returns:
        Dict[str, str]: The graph state with the SQL query result.
    """
    tool_messages = json.loads(state["messages"][-1].content)
    user_message = tool_messages.get("user_message")

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
    response = execute_query_tool.invoke(result["query"])
    state["messages"][-1].content = json.dumps(
        {
            "query_result": "Para a pergunta do usuário: "
            + user_message
            + " o resultado da consulta SQL é: "
            + str(response),
            "query": result["query"],
        }
    )
    return state
