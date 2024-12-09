import os
import sys
import uuid

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables.graph import MermaidDrawMethod

import streamlit as st
from streamlit.web.server.websocket_headers import _get_websocket_headers

headers = _get_websocket_headers()

session_id = headers.get("Sec-Websocket-Key")

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from virtual_sales_agent.graph import app


def _get_session():
    return headers.get("Sec-Websocket-Key")


def chat_history() -> list[HumanMessage, AIMessage]:
    """Gets the chat history from the session state.

    Returns:
        list[HumanMessage, AIMessage]: The chat history.
    """
    return [
        (
            HumanMessage(content=message["content"])
            if message["role"] == "user"
            else AIMessage(content=message["content"])
        )
        for message in st.session_state.messages
    ]


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
    messages = chat_history()
    messages.append(HumanMessage(content=question))
    events = app.stream({"messages": messages}, config)
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
        /* Estilo para o corpo da página */
        body {
            font-family: 'Arial', sans-serif;
            background-color: #e3f2fd; /* Azul claro suave */
            margin: 0;
            padding: 0;
        }

        /* Estilo para o contêiner principal */
        .main {
            background-color: #ffffff; /* Branco puro */
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0px 6px 12px rgba(0, 0, 0, 0.15); /* Sombra mais suave e elegante */
        }

        /* Títulos */
        h1 {
            color: #1e88e5; /* Azul vibrante */
            font-weight: bold;
        }
        h2, h3, h4 {
            color: #424242; /* Cinza escuro para contraste */
        }

        /* Estilo para a barra lateral */
        .sidebar .element-container {
            background-color: #f0f4c3; /* Verde claro suave */
            border-radius: 15px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0px 3px 6px rgba(0, 0, 0, 0.1);
        }

        /* Botão personalizado */
        .stButton button {
            background-color: #1e88e5; /* Azul vibrante */
            color: white;
            border-radius: 10px;
            padding: 10px 15px;
            font-size: 16px;
            border: none;
            transition: background-color 0.3s ease;
        }
        .stButton button:hover {
            background-color: #1565c0; /* Azul mais escuro para o hover */
            cursor: pointer;
        }

        /* Cabeçalho personalizado */
        .custom-header {
            background-color: #263238; /* Cinza escuro para contraste */
            padding: 15px;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 20px;
            box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.2);
        }
        .custom-header h2 {
            color: #ffffff; /* Branco para contraste */
            font-size: 28px;
        }
        .custom-header h4 {
            color: #b0bec5; /* Cinza claro para subtítulos */
            font-size: 20px;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="custom-header">
            <h2>🛒 Vendedor Virtual</h2>
            <h4>🦜 Construído com LangChain e LangGraph para sua plataforma e-commerce.</h4>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("⚙️ **Configurações**")

        st.button("🆕 Novo Chat", on_click=new_chat, type="primary")
        st.button("🛠️ Visualizar Workflow do Agente", on_click=get_graph, type="primary")

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
    chat_session = _get_session()

    config = {
        "configurable": {
            "customer_id": chat_session,
            "thread_id": thread_id,
        }
    }

    main(config)
