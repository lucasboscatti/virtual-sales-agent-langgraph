import os
import sys

import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from virtual_sales_agent.sales_agent import chat_agent


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


def handle_user_input(question: str):
    st.session_state.messages.append({"role": "user", "content": question})

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        agent_response = chat_agent(question)

        message_placeholder.markdown(agent_response)

        st.session_state.messages.append(
            {"role": "assistant", "content": agent_response}
        )


def main():
    set_page_config()
    initialize_session_state()

    st.title("🤖 Virtual Sales Agent")
    st.caption("A virtual sales agent for an e-commerce platform.")

    with st.sidebar:
        st.button("New Chat", on_click=new_chat, type="primary")
    display_chat_history()

    if question := st.chat_input("Ask your question:"):
        with st.chat_message("user"):
            st.markdown(question)
        handle_user_input(question)


if __name__ == "__main__":
    main()
