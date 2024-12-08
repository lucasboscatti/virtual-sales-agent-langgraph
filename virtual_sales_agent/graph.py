from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import tools_condition
from nodes import (
    Assistant,
    State,
    add_order_state,
    check_order_status_state,
    check_product_quantity_state,
    create_order_state,
    query_products_info_state,
    route_create_order,
    route_tool,
    routing_fuction,
    search_products_recommendations_state,
    subtract_quantity_state,
)
from prompts import primary_assistant_prompt
from tools import (
    check_order_status,
    create_order,
    query_products_info,
    search_products_recommendations,
)
from utils_functions import create_tool_node_with_fallback

llm = ChatGroq(model="llama3-groq-70b-8192-tool-use-preview", temperature=0)

part_1_tools = [
    query_products_info,
    create_order,
    check_order_status,
    search_products_recommendations,
]

assistant_runnable = primary_assistant_prompt | llm.bind_tools(part_1_tools)

builder = StateGraph(State)

# Define nodes: these do the work
builder.add_node("assistant", Assistant(assistant_runnable))
builder.add_node("tools", create_tool_node_with_fallback(part_1_tools))
builder.add_node("route_tool", route_tool)
builder.add_node("query_products_info_state", query_products_info_state)
builder.add_node("create_order_state", create_order_state)
builder.add_node("check_order_status_state", check_order_status_state)
builder.add_node(
    "search_products_recommendations_state", search_products_recommendations_state
)
builder.add_node("check_product_quantity_state", check_product_quantity_state)
builder.add_node("add_order_state", add_order_state)
builder.add_node("subtract_quantity_state", subtract_quantity_state)

# Define edges: these determine how the control flow moves
builder.add_edge(START, "assistant")
builder.add_conditional_edges("assistant", tools_condition, ["tools", END])
builder.add_edge("tools", "route_tool")
builder.add_conditional_edges("route_tool", routing_fuction),

# query products workflow
builder.add_edge("query_products_info_state", "assistant")

# create order workflow
builder.add_edge("create_order_state", "check_product_quantity_state")
builder.add_conditional_edges("check_product_quantity_state", route_create_order),
builder.add_edge("add_order_state", "subtract_quantity_state")
builder.add_edge("subtract_quantity_state", "assistant")

# check order status workflow
builder.add_edge("check_order_status_state", "assistant")

# search products recommendations workflow
builder.add_edge("search_products_recommendations_state", "assistant")

# The checkpointer lets the graph persist its state
# this is a complete memory for the entire graph.
memory = MemorySaver()
part_1_graph = builder.compile(checkpointer=memory)
