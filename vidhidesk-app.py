import streamlit as st
import google.generativeai as genai
import uuid
from datetime import datetime

# --- Configuration & Theme ---
st.set_page_config(page_title="VidhiDesk | Legal Research Hub", page_icon="⚖️", layout="wide")

# Custom CSS for Beige-Purple Aesthetic and Rounded Windows
st.markdown("""
    <style>
    /* Main Theme Colors */
    :root {
        --primary: #6D28D9;
        --beige: #F5F5F4;
        --white: #FFFFFF;
    }

    .stApp {
        background-color: var(--beige);
        color: #1F2937;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: var(--white) !important;
        border-right: 1px solid #E5E7EB;
    }

    /* Rounded Chat Containers */
    .stChatMessage {
        border-radius: 20px !important;
        padding: 15px !important;
        margin-bottom: 10px !important;
    }

    /* Custom Cards for "Spaces" */
    .space-card {
        background-color: white;
        padding: 20px;
        border-radius: 24px;
        border: 1px solid #EDE9FE;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 15px;
        transition: transform 0.2s;
    }
    .space-card:hover {
        transform: translateY(-5px);
        border-color: #6D28D9;
    }

    /* Button Styling */
    .stButton>button {
        border-radius: 12px;
        background-color: #6D28D9;
        color: white;
        border: none;
        padding: 10px 24px;
    }
    
    h1, h2, h3 {
        color: #1F2937 !important;
        font-family: 'Inter', sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)

# --- State Management ---
if "user_authenticated" not in st.session_state:
    st.session_state.user_authenticated = False
if "profile_complete" not in st.session_state:
    st.session_state.profile_complete = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "spaces" not in st.session_state:
    st.session_state.spaces = {
        "Research": [{"name": "Constitutional Basic Structure", "id": str(uuid.uuid4())}],
        "Paper": [{"name": "Data Privacy in India", "id": str(uuid.uuid4())}],
        "Study": [{"name": "CrPC Short Notes", "id": str(uuid.uuid4())}]
    }

# --- Gemini API Setup ---
# Use st.secrets for deployment, or empty string for local testing
API_KEY = st.secrets.get("GEMINI_API_KEY", "")
if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-3-flash')

# --- Logic: Auth & Profile ---
def login_screen():
    st.markdown("<h1 style='text-align: center;'>VidhiDesk</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>The Modern Legal Hub</p>", unsafe_allow_html=True)
    
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            tab1, tab2 = st.tabs(["Login", "Register"])
            with tab1:
                st.text_input("Email", key="login_email")
                st.text_input("Password", type="password", key="login_pass")
                if st.button("Sign In", use_container_width=True):
                    st.session_state.user_authenticated = True
                    st.rerun()
            with tab2:
                st.text_input("Full Name", key="reg_name")
                st.text_input("Email", key="reg_email")
                st.text_input("Password", type="password", key="reg_pass")
                if st.button("Create Account", use_container_width=True):
                    st.session_state.user_authenticated = True
                    st.rerun()

def profile_setup():
    st.markdown("## Setup Your Legal Profile")
    with st.form("profile_form"):
        name = st.text_input("Full Name")
        inst = st.selectbox("Institution", ["TNNLU", "NLSIU", "NALSAR", "DU Faculty of Law", "Other"])
        year = st.select_slider("Year of Study", options=["1st", "2nd", "3rd", "4th", "5th", "LLM", "Ph.D"])
        
        if st.form_submit_button("Complete Setup"):
            st.session_state.profile_data = {"name": name, "inst": inst, "year": year}
            st.session_state.profile_complete = True
            st.rerun()

# --- Main Application UI ---
def main_app():
    # Sidebar
    with st.sidebar:
        st.markdown(f"### ⚖️ VidhiDesk")
        st.divider()
        nav = st.radio("Navigation", ["Discovery", "Spaces", "Profile"])
        st.divider()
        if st.button("Log Out", use_container_width=True):
            st.session_state.user_authenticated = False
            st.rerun()

    if nav == "Discovery":
        st.markdown("## Advance your Legal Research")
        
        # Search Settings
        col1, col2 = st.columns(2)
        with col1:
            tone = st.selectbox("Tone", ["Informative", "Academic", "Casual"])
        with col2:
            difficulty = st.selectbox("Difficulty", ["Simple", "Intermediate", "Bare Act"])

        # Chat Interface
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Ask about an Act, Article, or Case Law..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                if not API_KEY:
                    response = "Please set your Gemini API Key in secrets/environment to enable the AI."
                else:
                    context = f"User is a {st.session_state.profile_data['year']} student at {st.session_state.profile_data['inst']}. Tone: {tone}. Level: {difficulty}."
                    ai_response = model.generate_content(f"{context} \n\n Explain: {prompt}")
                    response = ai_response.text
                
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

    elif nav == "Spaces":
        st.markdown("## Your Research Spaces")
        col_r, col_p, col_s = st.columns(3)
        
        with col_r:
            st.markdown("### 🔍 Research")
            for item in st.session_state.spaces["Research"]:
                st.markdown(f"<div class='space-card'><b>{item['name']}</b><br><small>AI Insights Active</small></div>", unsafe_allow_html=True)
            if st.button("+ New Research"): pass
                
        with col_p:
            st.markdown("### 📝 Paper")
            for item in st.session_state.spaces["Paper"]:
                st.markdown(f"<div class='space-card'><b>{item['name']}</b><br><small>Drafting Phase</small></div>", unsafe_allow_html=True)
            if st.button("+ New Paper"): pass

        with col_p:
            st.markdown("### 📚 Study")
            for item in st.session_state.spaces["Study"]:
                st.markdown(f"<div class='space-card'><b>{item['name']}</b><br><small>Exam Focus</small></div>", unsafe_allow_html=True)
            if st.button("+ New Study"): pass

    elif nav == "Profile":
        p = st.session_state.profile_data
        st.markdown(f"## {p['name']}'s Analytics")
        st.info(f"📍 {p['inst']} | 🎓 {p['year']} Year")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Topic Concentration")
            st.progress(0.85, text="Constitutional Law")
            st.progress(0.40, text="Criminal Law")
            st.progress(0.25, text="Tort Law")
        with col2:
            st.markdown("#### Search Activity")
            st.bar_chart([10, 20, 15, 30, 25, 40])

# --- Router ---
if not st.session_state.user_authenticated:
    login_screen()
elif not st.session_state.profile_complete:
    profile_setup()
else:
    main_app()
