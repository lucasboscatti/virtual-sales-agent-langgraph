import os
import sys
import uuid

from langchain_core.runnables.graph import MermaidDrawMethod

import streamlit as st
from streamlit.runtime import get_instance
from streamlit.runtime.scriptrunner import get_script_run_ctx

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from virtual_sales_agent.graph import app


def get_chat_session() -> str:
    """Gets the chat session ID.

    Returns:
        str: The chat session ID.
    """
    runtime = get_instance()
    session_id = get_script_run_ctx().session_id
    session_info = runtime._session_mgr.get_session_info(session_id)
    if session_info is None:
        raise RuntimeError("Couldn't get your Streamlit Session object.")
    return session_info.session.id


def set_page_config() -> None:
    """Sets the page configuration for the Streamlit app.

    Returns:
        None
    """

    st.set_page_config(
        page_title="🛒 Vendedor Virtual com IA",
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

    st.markdown(
        """
    <style>
        body {
            font-family: 'Arial', sans-serif;
            background-color: #f5f5f5;
        }
        .main {
            background-color: #ffffff;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
        }
        h1 {
            color: #4CAF50;
        }
        h2, h3, h4 {
            color: #333333;
        }
        .sidebar .element-container {
            background-color: #f9f9f9;
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1);
        }
        .stButton button {
            background-color: #4CAF50;
            color: white;
            border-radius: 5px;
        }
        .stButton button:hover {
            background-color: #45a049;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.title("🛒 Vendedor Virtual")
    st.caption(
        "🦜 Vendedor Virtual com LangChain e LangGraph para sua plataforma e-commerce."
    )

    with st.sidebar:
        st.header("⚙️ **Configurações**")

        st.button("🆕 Novo Chat", on_click=new_chat, type="primary")
        st.button("🛠️ Visualizar Workflow do Agente", on_click=get_graph, type="primary")

        st.markdown("## 🤖 Funcionalidades")
        st.markdown("## 🛠️ **Funcionalidades do Vendedor Virtual**")
        st.markdown(
            """
        ### 🛒 **Consulta de Produtos**
        - Pergunte sobre produtos disponíveis, preços e estoque.
        - **Exemplo**: “Quais são os produtos disponíveis?” ou “Qual o preço do produto X?”

        ### 📝 **Criação de Pedidos**
        - Permite a criação de pedidos baseados em informações do banco de dados.
        - **Exemplo**: “Quero comprar 5 unidades do produto Y.”

        ### 📦 **Consulta de Pedidos**
        - Consulte o status de pedidos anteriores.
        - **Exemplo**: “Qual é o status do meu pedido #12345?”

        ### 🎯 **Sugestões Personalizadas**
        - Recomendações com base no histórico de pedidos do cliente.
        - **Exemplo**: “Baseado na sua última compra, recomendamos o produto Z.”

        ### 👨‍💻 **Escalonamento para um Agente Humano**
        - Escale a conversa para um atendente humano, se necessário.
        - **Exemplo**: “Preciso falar com um atendente humano.”
        """
        )

    display_chat_history()

    if question := st.chat_input("Ask your question:"):
        with st.chat_message("user"):
            st.markdown(question)
        handle_user_input(question, config)


if __name__ == "__main__":
    thread_id = str(uuid.uuid4())
    chat_session = get_chat_session()

    config = {
        "configurable": {
            "customer_id": chat_session,
            "thread_id": thread_id,
        }
    }

    main(config)
