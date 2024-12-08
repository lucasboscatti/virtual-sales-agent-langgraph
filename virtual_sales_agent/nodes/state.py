from langgraph.graph.message import AnyMessage, add_messages
from typing_extensions import Annotated, TypedDict


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]