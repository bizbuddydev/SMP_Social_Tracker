from openai import OpenAI
import streamlit as st

openai_api_key = st.secrets["openai"]["api_key"]

# Define links to other pages
PAGES = {
    "Overview": "https://smp-bizbuddy-accountoverview.streamlit.app/",
    "Posts": "https://smp-bizbuddy-postoverview.streamlit.app",
    "Scheduler": "https://smp-bizbuddy-postscheduler.streamlit.app/",
}

# Sidebar navigation
st.sidebar.title("Navigation")
for page, url in PAGES.items():
    st.sidebar.markdown(f"[**{page}**]({url})", unsafe_allow_html=True)

st.title("💬 Chatbot")
st.caption("🚀 A BizBuddy chatbot that understands your business, powered by OpenAI")
st.caption("Let's brainstorm!")
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():

    client = OpenAI(api_key=openai_api_key)
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    response = client.chat.completions.create(model="gpt-3.5-turbo", messages=st.session_state.messages)
    msg = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)
