import uuid
from datetime import datetime
from typing import Annotated, Literal

from langchain_core.messages import AIMessage, ToolMessage
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
) -> Literal[
    "get_products",
    "create_order",
    "check_order_status",
    "search_products_recommendations",
]:
    return state["messages"][-1].tool_calls[0].name + "_state"


def get_products_state(state: State): ...


def create_order_state(state: State): ...


def check_order_status_state(state: State): ...


def search_products_recommendations_state(state: State): ...


# a = {
#     "messages": [
#         HumanMessage(
#             content="What is the status of my order 2?",
#             additional_kwargs={},
#             response_metadata={},
#             id="771fb37a-11be-495e-a498-c0d0cb7ea833",
#         ),
#         AIMessage(
#             content="",
#             additional_kwargs={
#                 "tool_calls": [
#                     {
#                         "id": "call_1zcn",
#                         "function": {
#                             "arguments": '{"order_id": "2"}',
#                             "name": "check_order_status",
#                         },
#                         "type": "function",
#                     }
#                 ]
#             },
#             response_metadata={
#                 "token_usage": {
#                     "completion_tokens": 28,
#                     "prompt_tokens": 851,
#                     "total_tokens": 879,
#                     "completion_time": 0.085924612,
#                     "prompt_time": 0.058083344,
#                     "queue_time": 0.0009591959999999955,
#                     "total_time": 0.144007956,
#                 },
#                 "model_name": "llama3-groq-70b-8192-tool-use-preview",
#                 "system_fingerprint": "fp_ee4b521143",
#                 "finish_reason": "tool_calls",
#                 "logprobs": None,
#             },
#             id="run-ecb31670-45bc-49b3-a2b8-1e56bce653fd-0",
#             tool_calls=[
#                 {
#                     "name": "check_order_status",
#                     "args": {"order_id": "2"},
#                     "id": "call_1zcn",
#                     "type": "tool_call",
#                 }
#             ],
#             usage_metadata={
#                 "input_tokens": 851,
#                 "output_tokens": 28,
#                 "total_tokens": 879,
#             },
#         ),
#         ToolMessage(
#             content='{"OrderId": 2, "Status": "Pending", "OrderDate": "2024-12-06 14:11:35"}',
#             name="check_order_status",
#             id="2d26186d-1837-4b55-ae06-a571fa8bd8c2",
#             tool_call_id="call_1zcn",
#         ),
#     ]
# }
