import streamlit as st
import google.generativeai as genai
import uuid
from datetime import datetime

# --- Configuration & Theme ---
st.set_page_config(page_title="VidhiDesk | Dark Hub", page_icon="⚖️", layout="wide")

# Custom CSS for Major Black - Minor Purple Aesthetic
st.markdown("""
    <style>
    /* Theme Variables */
    :root {
        --primary-purple: #8B5CF6;
        --deep-black: #09090B;
        --card-bg: #18181B;
        --text-white: #FAFAFA;
        --text-muted: #A1A1AA;
        --border-color: #27272A;
    }

    /* Global Overrides */
    .stApp {
        background-color: var(--deep-black);
        color: var(--text-white);
    }

    /* Sidebar - Major Black with Purple Border */
    section[data-testid="stSidebar"] {
        background-color: #000000 !important;
        border-right: 1px solid var(--primary-purple);
    }
    
    section[data-testid="stSidebar"] .stText, 
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown p {
        color: var(--text-white) !important;
    }

    /* Buttons */
    .stButton>button {
        background-color: var(--primary-purple) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        width: 100%;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        box-shadow: 0 0 15px var(--primary-purple);
        transform: translateY(-2px);
    }

    /* Text Inputs & Selectboxes */
    input, select, textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: var(--card-bg) !important;
        color: var(--text-white) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
    }

    /* Chat Messages */
    .stChatMessage {
        background-color: var(--card-bg) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 20px !important;
        color: var(--text-white) !important;
    }
    
    /* "Spaces" Cards */
    .space-card {
        background-color: var(--card-bg);
        padding: 24px;
        border-radius: 20px;
        border: 1px solid var(--border-color);
        margin-bottom: 16px;
        transition: border 0.3s ease;
    }
    .space-card:hover {
        border-color: var(--primary-purple);
    }
    .space-card h4 {
        color: var(--text-white) !important;
        margin-bottom: 8px;
    }
    .space-card p {
        color: var(--text-muted) !important;
        font-size: 0.85rem;
    }

    /* Headers */
    h1, h2, h3, h4, h5 {
        color: var(--text-white) !important;
        font-family: 'Inter', sans-serif;
    }

    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: transparent;
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        background-color: var(--card-bg);
        border-radius: 10px 10px 0 0;
        color: var(--text-muted);
    }
    .stTabs [aria-selected="true"] {
        color: var(--primary-purple) !important;
        border-bottom: 2px solid var(--primary-purple) !important;
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
        "Research": [{"name": "Constitutional Basic Structure", "desc": "Focus on Kesavananda Bharati"}],
        "Paper": [{"name": "Data Privacy in India", "desc": "Drafting for Law Seminar"}],
        "Study": [{"name": "Criminal Law II", "desc": "Semester V Prep"}]
    }

# --- Gemini API Setup ---
API_KEY = st.secrets.get("GEMINI_API_KEY", "")

def get_ai_model():
    if not API_KEY:
        return None
    try:
        genai.configure(api_key=API_KEY)
        # Using the standard model string with version 0.8.8+ ensures v1 endpoint usage
        return genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error(f"Failed to initialize AI: {e}")
        return None

# Attempt to initialize the model
model = get_ai_model()

# --- Router Components ---

def login_screen():
    st.markdown("<h1 style='text-align: center; color: #8B5CF6 !important;'>VidhiDesk</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #A1A1AA;'>The Black-Edition Legal Hub</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        tab1, tab2 = st.tabs(["Login", "Register"])
        with tab1:
            st.text_input("Email", placeholder="advocate@vidhidesk.com", key="l_email")
            st.text_input("Password", type="password", key="l_pass")
            if st.button("Sign In"):
                st.session_state.user_authenticated = True
                st.rerun()
        with tab2:
            st.text_input("Full Name", placeholder="e.g. Rahul Sharma", key="r_name")
            st.text_input("Register Email", key="r_email")
            st.text_input("Choose Password", type="password", key="r_pass")
            if st.button("Create Account"):
                st.session_state.user_authenticated = True
                st.rerun()

def profile_setup():
    st.markdown("## 👤 Initialize Legal Profile")
    with st.container():
        st.markdown("<div style='background-color:#18181B; padding:30px; border-radius:20px; border:1px solid #27272A;'>", unsafe_allow_html=True)
        name = st.text_input("Full Name")
        inst = st.selectbox("Institution", ["Tamil Nadu National Law University (TNNLU)", "NLSIU", "NALSAR", "GNLU", "DU Faculty of Law", "Other"])
        year = st.select_slider("Year of Study", options=["1st", "2nd", "3rd", "4th", "5th", "LLM", "Research"])
        
        if st.button("Enter the Hub"):
            if name:
                st.session_state.profile_data = {"name": name, "inst": inst, "year": year}
                st.session_state.profile_complete = True
                st.rerun()
            else:
                st.error("Please enter your name.")
        st.markdown("</div>", unsafe_allow_html=True)

def main_app():
    # Sidebar
    with st.sidebar:
        st.markdown(f"<h2 style='color:#8B5CF6 !important;'>⚖️ VidhiDesk</h2>", unsafe_allow_html=True)
        st.divider()
        nav = st.radio("NAVIGATION", ["Discovery", "Spaces", "Insights"], label_visibility="collapsed")
        st.divider()
        st.write(f"Logged in: **{st.session_state.profile_data['name']}**")
        if st.button("Log Out"):
            st.session_state.user_authenticated = False
            st.rerun()

    if nav == "Discovery":
        st.markdown("<h2 style='margin-bottom:0;'>Discovery Hub</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color:#A1A1AA;'>Chat with AI to clarify Acts and Amendments</p>", unsafe_allow_html=True)
        
        # Search Settings
        col1, col2 = st.columns(2)
        with col1:
            tone = st.selectbox("Tone", ["Informative", "Academic", "Casual"])
        with col2:
            difficulty = st.selectbox("Complexity", ["Simple", "Intermediate", "Bare Act"])

        st.divider()

        # Chat display
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Ask about IPC Section 302, Article 370..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                if not API_KEY:
                    response = "⚠️ **API Key Missing**: Please add `GEMINI_API_KEY` to your Streamlit Secrets."
                elif not model:
                    response = "❌ **AI Initialization Error**: Check your API key and network connection."
                else:
                    with st.spinner("Analyzing Legal Context..."):
                        try:
                            context = f"Student Profile: {st.session_state.profile_data['year']} year at {st.session_state.profile_data['inst']}. Tone: {tone}. Difficulty: {difficulty}."
                            # Request AI response
                            ai_response = model.generate_content(f"{context} \n\n Explain this legal concept: {prompt}")
                            response = ai_response.text
                        except Exception as e:
                            response = f"An error occurred: {str(e)}. Tip: Try re-deploying to refresh the package cache."
                
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

    elif nav == "Spaces":
        st.markdown("## Research Spaces")
        st.markdown("<p style='color:#A1A1AA;'>Organized clusters of your legal queries</p>", unsafe_allow_html=True)
        
        tabs = st.tabs(["🔍 Research", "📝 Papers", "📚 Study Hub"])
        
        categories = ["Research", "Paper", "Study"]
        for i, tab in enumerate(tabs):
            with tab:
                cat = categories[i]
                cols = st.columns(2)
                for idx, space in enumerate(st.session_state.spaces[cat]):
                    with cols[idx % 2]:
                        st.markdown(f"""
                            <div class='space-card'>
                                <h4>{space['name']}</h4>
                                <p>{space['desc']}</p>
                                <div style='color:#8B5CF6; font-size:12px; margin-top:10px;'>✨ AI Insights Active</div>
                            </div>
                        """, unsafe_allow_html=True)
                if st.button(f"+ New {cat} Cluster", key=f"btn_{cat}"):
                    st.toast(f"New {cat} space initiated...")

    elif nav == "Insights":
        p = st.session_state.profile_data
        st.markdown(f"## {p['name']}'s Research Analytics")
        
        col1, col2 = st.columns([1, 1.5])
        with col1:
            st.markdown("#### Topic Concentration")
            st.markdown("<br>", unsafe_allow_html=True)
            st.write("Constitutional Law")
            st.progress(0.85)
            st.write("Criminal Law")
            st.progress(0.60)
            st.write("Intellectual Property")
            st.progress(0.30)
        
        with col2:
            st.markdown("#### Weekly Research Intensity")
            st.bar_chart([15, 30, 10, 45, 20, 50, 60], color="#8B5CF6")

# --- Application Entry ---
if not st.session_state.user_authenticated:
    login_screen()
elif not st.session_state.profile_complete:
    profile_setup()
else:
    main_app()
