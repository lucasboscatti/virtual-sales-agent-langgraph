import uuid

from virtual_sales_agent.graph import app
from virtual_sales_agent.utils_functions import _print_event

# from IPython.display import Image, display
# Visualize your graph

# png = part_1_graph.get_graph().draw_mermaid_png(output_file_path="graph.png")


thread_id = str(uuid.uuid4())

config = {
    "configurable": {
        "customer_id": "12",
        "thread_id": thread_id,
    }
}


def chat_agent(question):
    set = ()
    events = app.stream({"messages": ("user", question)}, config)
    for event in events:
        if assistant_response := event.get("assistant"):
            if final_response := assistant_response["messages"].content:
                return final_response
