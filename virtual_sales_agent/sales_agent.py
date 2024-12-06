import uuid

from graph import part_1_graph
from utils_functions import _print_event

# Visualize your graph
from IPython.display import Image, display

png = part_1_graph.get_graph().draw_mermaid_png(output_file_path="graph.png")


# Let's create an example conversation a user might have with the assistant
# tutorial_questions = [
#     "What is the status of my order 2?",
# ]


# thread_id = str(uuid.uuid4())

# config = {
#     "configurable": {
#         "customer_id": "12345678",
#         "thread_id": thread_id,
#     }
# }


# _printed = set()
# for question in tutorial_questions:
#     events = part_1_graph.stream(
#         {"messages": ("user", question)}, config, stream_mode="values"
#     )
#     for event in events:
#         _print_event(event, _printed)
