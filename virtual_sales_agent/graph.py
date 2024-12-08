from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import tools_condition

from virtual_sales_agent.nodes.assistant import Assistant
from virtual_sales_agent.nodes.check_order_status_node import check_order_status_state
from virtual_sales_agent.nodes.create_order_node import (
    add_order_state,
    check_product_quantity_state,
    create_order_state,
    subtract_quantity_state,
)
from virtual_sales_agent.nodes.escalate_to_employee_node import (
    escalate_to_employee_state,
)
from virtual_sales_agent.nodes.query_products_node import query_products_info_state
from virtual_sales_agent.nodes.recommend_product_node import (
    search_products_recommendations_state,
)
from virtual_sales_agent.nodes.routing_functions import (
    route_create_order,
    route_tool,
    routing_fuction,
)
from virtual_sales_agent.nodes.state import State
from virtual_sales_agent.prompts import primary_assistant_prompt
from virtual_sales_agent.tools import (
    check_order_status,
    create_order,
    escalate_to_employee,
    query_products_info,
    search_products_recommendations,
)
from virtual_sales_agent.utils_functions import create_tool_node_with_fallback

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

tools = [
    query_products_info,
    create_order,
    check_order_status,
    search_products_recommendations,
    escalate_to_employee,
]

assistant_runnable = primary_assistant_prompt | llm.bind_tools(tools)

builder = StateGraph(State)

# Define nodes: these do the work
builder.add_node("assistant", Assistant(assistant_runnable))
builder.add_node("tools", create_tool_node_with_fallback(tools))
builder.add_node("route_tool", route_tool)
builder.add_node("query_products_info_state", query_products_info_state)
builder.add_node("create_order_state", create_order_state)
builder.add_node("check_order_status_state", check_order_status_state)
builder.add_node(
    "search_products_recommendations_state", search_products_recommendations_state
)
builder.add_node("escalate_to_employee_state", escalate_to_employee_state)
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

# escalate to employee workflow
builder.add_edge("escalate_to_employee_state", "assistant")

# The checkpointer lets the graph persist its state
# this is a complete memory for the entire graph.
memory = MemorySaver()
app = builder.compile(checkpointer=memory)
