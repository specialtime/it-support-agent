import streamlit as st
import requests
import uuid

# Config
API_URL = "http://localhost:8000/ask"

st.set_page_config(page_title="Soporte IT Agente", page_icon="🤖")

st.title("IT Support Chatbot")
st.markdown("Asistente virtual para consultas y solicitudes de soporte IT.")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

user_role = st.sidebar.selectbox("Rol", ["user", "helpdesk", "admin"])

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Escribe tu consulta aquí..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        response = requests.post(API_URL, json={
            "question": prompt,
            "session_id": st.session_state.session_id,
            "role": user_role
        })
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "No response")
            action = data.get("action_executed")
            
            with st.chat_message("assistant"):
                st.markdown(answer)
                if action:
                    st.info(f"Action Executed: {action}")
                st.session_state.messages.append({"role": "assistant", "content": answer})
        else:
            st.error(f"Error from API: {response.status_code}")
    except Exception as e:
        st.error(f"Connection failed: {e}")
