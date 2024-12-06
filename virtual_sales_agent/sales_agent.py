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
from prompts import query_check_system, query_gen_system
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

llm = ChatGroq(
    model="llama3-groq-70b-8192-tool-use-preview", temperature=0, streaming=True
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
        return {"messages": result}


primary_assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a helpful virtual sales assistant for an e-commerce platform. 
Your primary tasks are to assist users with product information, stock availability, order placement, order tracking, and personalized product suggestions based on purchase history.
Use the provided tools to query product catalogs, customer information, and order details from the database to resolve user inquiries.
Be persistent when retrieving information—expand your query bounds if the initial attempt does not yield results.
If no relevant information is found after expanding your search, politely inform the user and guide them toward other available options or next steps.
\n\nCurrent user:\n<User>\n{user_info}\n</User>
\nCurrent time: {time}.
""",
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now)

part_1_tools = [
    query_products,
    create_order,
    check_order_status,
    search_products_recommendations,
]

part_1_assistant_runnable = primary_assistant_prompt | llm.bind_tools(part_1_tools)


builder = StateGraph(State)


# Define nodes: these do the work
builder.add_node("assistant", Assistant(part_1_assistant_runnable))
builder.add_node("tools", create_tool_node_with_fallback(part_1_tools))
# Define edges: these determine how the control flow moves
builder.add_edge(START, "assistant")
builder.add_conditional_edges(
    "assistant",
    tools_condition,
)
builder.add_edge("tools", "assistant")

# The checkpointer lets the graph persist its state
# this is a complete memory for the entire graph.
memory = MemorySaver()
part_1_graph = builder.compile(checkpointer=memory)


# Let's create an example conversation a user might have with the assistant
tutorial_questions = [
    "What are the available products?",
]


thread_id = str(uuid.uuid4())

config = {
    "configurable": {
        "customer_id": "1234567890",
        "thread_id": thread_id,
    }
}


_printed = set()
for question in tutorial_questions:
    events = part_1_graph.stream(
        {"messages": ("user", question)}, config, stream_mode="values"
    )
    for event in events:
        _print_event(event, _printed)
