import streamlit as st
# ✅ Set page config FIRST
st.set_page_config(page_title="AgriBananaBot🌱🤖", layout="wide")

import os
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image

# Load and display the logo
logo = Image.open("logo.png")  # Replace with your logo file name

# Load environment variables
load_dotenv()

# Configure Gemini API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize Gemini model
model = genai.GenerativeModel("gemini-1.5-flash")
chat = model.start_chat(history=[])

# Function to get response
def get_gemini_response(question, history):
    greetings_map = {
        "good morning": "Good morning! How can I help you?",
        "good afternoon": "Good afternoon! How can I help you?",
        "good evening": "Good evening! How can I help you?",
        "hi": "Hi! How can I help you?",
        "hello": "Hello! How can I help you!",
        "hey": "Hey! How can I help you?"
    }

    cleaned_question = question.lower().strip()
    for keyword in greetings_map:
        if keyword in cleaned_question:
            return [greetings_map[keyword]]  # Direct response for greetings

    prompt = f"""
You are a helpful agriculture assistant focused on banana farming. Here is the conversation history:

{history}

User's new question: {question}

Please:
1. Provide a helpful and relevant answer related to banana farming.
2. At the end, suggest 2–3 follow-up questions. Start the suggestion section with 'Suggested questions:' and list them clearly.
If the query is not related to banana or agriculture, reply with:
"I'm sorry, I'm not able to assist with that topic at the moment."
"""
    response = chat.send_message(prompt, stream=True)
    return response

# Function to generate chat summary for sidebar
def generate_chat_summary(messages):
    full_convo = "\n".join([f"{role.title()}: {msg}" for role, msg in messages])
    prompt = f"Summarize this chat in 4–6 words:\n{full_convo}"
    try:
        summary = model.generate_content(prompt)
        return summary.text.strip().split("\n")[0]
    except:
        return "Untitled Chat"

# === Initialize session state ===
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'suggestion_keys' not in st.session_state:
    st.session_state.suggestion_keys = []
if 'previous_chats' not in st.session_state:
    st.session_state.previous_chats = []
if 'input_box_key' not in st.session_state:
    st.session_state.input_box_key = 0

# === Sidebar ===
st.sidebar.title("Previous Chats")
if st.sidebar.button("\u2795 Start New Chat"):
    if st.session_state.chat_history:
        title = generate_chat_summary(st.session_state.chat_history)
        st.session_state.previous_chats.append({
            "title": title,
            "messages": st.session_state.chat_history.copy()
        })
    st.session_state.chat_history = []
    st.session_state.suggestion_keys = []
    st.session_state.input_box_key += 1
    st.rerun()

# Sidebar: Show chat summaries
if st.session_state.previous_chats:
    for i, chat in enumerate(st.session_state.previous_chats[::-1]):
        with st.sidebar.expander(chat["title"]):
            for role, msg in chat["messages"]:
                st.markdown(f"**{role.title()}:** {msg}")
else:
    st.sidebar.info("No previous chats yet.")

# === Main Chat Area ===
# Center the logo
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    st.image("logo.png", use_container_width=False, width=250)

# Title (optional, can also be centered like logo if needed)
st.markdown("<h1 style='text-align: center;'>AgriBananaBot🌱🤖</h1>", unsafe_allow_html=True)

# Left-aligned app description
st.markdown("""
This app is an **AI Conversational Assistant** designed to help with banana farming-related queries.Simply type your question below, and the assistant will provide expert insights, suggestions, and guidance tailored to banana cultivation.
""")

# Process any pending prompt
if "pending_prompt" in st.session_state:
    prompt = st.session_state["pending_prompt"]
    del st.session_state["pending_prompt"]

    chat_context = "\n".join([f"{role.title()}: {msg}" for role, msg in st.session_state.chat_history])

    with st.spinner("Generating response..."):
        try:
            response_chunks = get_gemini_response(prompt, chat_context)

            if isinstance(response_chunks, list):  # It's a direct greeting
                ai_response = response_chunks[0]
                suggestions = []
            else:
                ai_response = ""
                for chunk in response_chunks:
                    ai_response += chunk.text

                if "Suggested questions:" in ai_response:
                    main_response, suggestions_block = ai_response.split("Suggested questions:", 1)
                    suggestions = [q.strip("- ").strip() for q in suggestions_block.strip().split("\n") if q.strip()]
                    ai_response = main_response.strip()
                else:
                    suggestions = []

        except Exception:
            ai_response = "Sorry, I encountered an error. Please try again."
            suggestions = []

    st.session_state.chat_history.append(("user", prompt))
    st.session_state.chat_history.append(("assistant", ai_response))
    st.session_state.suggestion_keys = suggestions

# Show chat history
for role, message in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(f"**{role.title()}:** {message}")

# Show suggestions if available
if st.session_state.suggestion_keys:
    st.markdown("**Suggested questions:**")
    for idx, suggestion in enumerate(st.session_state.suggestion_keys):
        key = f"suggestion_{idx}"
        if st.button(suggestion, key=key):
            st.session_state["pending_prompt"] = suggestion
            st.rerun()

# Input field
st.markdown("---")
if "pending_prompt" not in st.session_state:
    col1, col2 = st.columns([5, 1])
    with col1:
        user_input = st.text_input("Ask a question...", key=f"user_input_{st.session_state.input_box_key}", label_visibility="collapsed")
    with col2:
        send = st.button("➤", key="send_button")
    if user_input.strip():
        st.session_state["pending_prompt"] = user_input.strip()
        st.session_state.input_box_key += 1
        st.rerun()
