from typing import Annotated, Literal

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.messages.tool import ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import AnyMessage, add_messages
from langgraph.prebuilt import tools_condition
from tools import (
    check_order_status,
    create_order,
    query_products,
    search_products_recommendations,
)
from typing_extensions import TypedDict
from utils_functions import (
    _print_event,
    create_tool_node_with_fallback,
    handle_tool_error,
)


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: State, config: RunnableConfig):
        while True:
            configuration = config.get("configurable", {})
            passenger_id = configuration.get("customer_id", None)
            state = {**state, "user_info": passenger_id}
            result = self.runnable.invoke(state)
            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break
        return {"messages": result, "tool_calls": result.tool_calls}


def route_tool(
    state: State,
) -> ToolMessage:
    return state["messages"][-1]


def get_products_state(state: State): ...


def create_order_state(state: State): ...


def check_order_status_state(state: str): ...


def search_products_recommendations_state(state: State): ...


def routing_fuction(state: State):
    return state["messages"][-1].name + "_state"
