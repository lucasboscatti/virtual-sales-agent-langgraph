import os
import sys
import uuid

from langchain_core.runnables.graph import MermaidDrawMethod

import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from virtual_sales_agent.graph import app


def set_page_config() -> None:
    """Sets the page configuration for the Streamlit app.

    Returns:
        None
    """

    st.set_page_config(
        page_title="Virtual Sales Agent",
        layout="wide",
    )


def new_chat() -> None:
    """Resets the session state and starts a new chat.

    Returns:
        None
    """
    st.session_state.messages = []


def initialize_session_state() -> None:
    """Initializes the session state variables.

    Returns:
        None
    """
    if "messages" not in st.session_state:
        st.session_state.messages = []


def display_chat_history() -> None:
    """Displays the chat history in the Streamlit app.

    Returns:
        None
    """
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def chat_agent(question: str, config: dict) -> str:
    """Generates a response from the chat agent.

    Arguments:
        question (str): The user's question.
        config (dict): The configuration for the chat agent.

    Returns:
        str: The response from the chat agent.
    """
    events = app.stream({"messages": ("user", question)}, config)
    for event in events:
        if assistant_response := event.get("assistant"):
            if final_response := assistant_response["messages"].content:
                return final_response


def handle_user_input(question: str, config: dict) -> None:
    """Handles the user's input and displays the response.

    Arguments:
        question (str): The user's question.
        config (dict): The configuration for the chat agent.

    Returns:
        None
    """
    st.session_state.messages.append({"role": "user", "content": question})

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        agent_response = chat_agent(question, config)

        message_placeholder.markdown(agent_response)

        st.session_state.messages.append(
            {"role": "assistant", "content": agent_response}
        )


def get_graph():
    """Gets the graph for the chat agent.

    Returns:
        st.image: The image of the graph.
    """
    app.get_graph().draw_mermaid_png(
        draw_method=MermaidDrawMethod.API, output_file_path="graph.png"
    )

    return st.image("graph.png")


def main(config: dict) -> None:
    """Main function for the Streamlit app.

    Arguments:
        config (dict): The configuration for the chat agent.

    Returns:
        None
    """
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
