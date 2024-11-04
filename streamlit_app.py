# streamlit run streamlit_app.py
import os
import streamlit as st
from caller_agent import CONVERSATION, receive_message_from_caller
from tools import APPOINTMENTS
from langchain_core.messages import HumanMessage
import langsmith

# Load environment variables
with open(".env", "r") as f:
    for line in f:
        key, value = line.strip().split("=")
        os.environ[key] = value

# Enable debugging
langsmith.debug = True

# Streamlit setup
st.set_page_config(layout="wide")

# Function to handle message submission
def submit_message():
    receive_message_from_caller(st.session_state["message"])

# Layout
col1, col2 = st.columns(2)

with col1:
    st.subheader("Appointment Manager")
    for message in CONVERSATION:
        if isinstance(message, HumanMessage):
            with st.chat_message("user"):
                st.write(message.content)
        else:
            with st.chat_message("assistant"):
                st.write(message.content)
    
    st.chat_input("Type message here", on_submit=submit_message, key="message")

with col2:
    st.header("Appointments")
    st.write(APPOINTMENTS)
