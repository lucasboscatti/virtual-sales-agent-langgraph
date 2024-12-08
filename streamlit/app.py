import os
import sys
import uuid

from langchain_core.runnables.graph import MermaidDrawMethod

import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from virtual_sales_agent.graph import app


def set_page_config():
    st.set_page_config(
        page_title="Virtual Sales Agent",
        layout="wide",
    )


def new_chat():
    st.session_state.messages = []


def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []


def display_chat_history():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def chat_agent(question, config):
    events = app.stream({"messages": ("user", question)}, config)
    for event in events:
        if assistant_response := event.get("assistant"):
            if final_response := assistant_response["messages"].content:
                return final_response


def handle_user_input(question: str, config: dict):
    st.session_state.messages.append({"role": "user", "content": question})

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        agent_response = chat_agent(question, config)

        message_placeholder.markdown(agent_response)

        st.session_state.messages.append(
            {"role": "assistant", "content": agent_response}
        )


def get_graph():
    app.get_graph().draw_mermaid_png(
        draw_method=MermaidDrawMethod.API, output_file_path="graph.png"
    )

    return st.image("graph.png")


def main(config):
    set_page_config()
    initialize_session_state()

    st.title("🤖 Virtual Sales Agent")
    st.caption("A virtual sales agent for an e-commerce platform.")

    with st.sidebar:
        st.button("New Chat", on_click=new_chat, type="primary")
        st.button("See Sales Agent Workflow", on_click=get_graph, type="primary")

    display_chat_history()

    if question := st.chat_input("Ask your question:"):
        with st.chat_message("user"):
            st.markdown(question)
        handle_user_input(question, config)


if __name__ == "__main__":
    thread_id = str(uuid.uuid4())

    config = {
        "configurable": {
            "customer_id": "12",
            "thread_id": thread_id,
        }
    }

    main(config)
