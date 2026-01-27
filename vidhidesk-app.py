import streamlit as st
import google.generativeai as genai
import time
import uuid

# --- CONFIGURATION & SETUP ---
st.set_page_config(
    page_title="VidhiDesk | Legal Research Hub",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS (Dark Mode: Major Black - Minor Purple) ---
st.markdown("""
<style>
    /* Main Background - Deep Black/Grey */
    .stApp {
        background-color: #0E0E0E;
        color: #E0E0E0;
    }
    
    /* Sidebar - Very Dark Purple/Black */
    section[data-testid="stSidebar"] {
        background-color: #120A1A;
        border-right: 1px solid #2D1B4E;
    }
    
    /* Text Coloring in Sidebar */
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3, 
    section[data-testid="stSidebar"] label, 
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] p {
        color: #D1C4E9 !important;
    }

    /* Buttons - Neon Purple & Rounded */
    .stButton > button {
        background: linear-gradient(135deg, #6200EA 0%, #3700B3 100%);
        color: #FFFFFF;
        border-radius: 25px;
        border: 1px solid #7C4DFF;
        padding: 10px 24px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 10px rgba(98, 0, 234, 0.3);
        font-weight: 500;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #7C4DFF 0%, #651FFF 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(124, 77, 255, 0.5);
        border-color: #B388FF;
    }
    
    /* Secondary/Ghost Buttons (if any) */
    button[kind="secondary"] {
        background-color: transparent;
        border: 1px solid #BB86FC;
        color: #BB86FC;
    }

    /* Input Fields - Dark Grey with Purple Borders */
    .stTextInput > div > div > input, 
    .stSelectbox > div > div > div {
        border-radius: 12px;
        background-color: #1E1E1E;
        color: #FFFFFF;
        border: 1px solid #3E2C5A;
    }
    .stTextInput > div > div > input:focus, 
    .stSelectbox > div > div > div:focus {
        border-color: #BB86FC;
        box-shadow: 0 0 5px rgba(187, 134, 252, 0.5);
    }
    
    /* Dropdown Menu Items */
    ul[data-testid="stSelectboxVirtualDropdown"] {
        background-color: #1E1E1E;
        color: white;
    }

    /* Cards/Containers */
    .css-card {
        background-color: #1A1A1A;
        padding: 25px;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
        margin-bottom: 20px;
        border: 1px solid #333;
        border-left: 4px solid #BB86FC; /* Light Purple Accent */
    }

    /* Headers */
    h1, h2, h3 {
        font-family: 'Helvetica Neue', sans-serif;
        color: #BB86FC !important; /* Material Design Purple 200 */
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1E1E1E;
        border-radius: 8px 8px 0 0;
        color: #9E9E9E;
        border: none;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #311B92;
        color: #FFFFFF;
        border-bottom: 2px solid #BB86FC;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background-color: #1E1E1E;
        color: #E0E0E0;
        border-radius: 8px;
    }
    
    /* Animations */
    @keyframes fadeIn {
        0% { opacity: 0; transform: translateY(10px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    .animate-fade {
        animation: fadeIn 0.6s ease-out;
    }
    
    /* Toast */
    div[data-baseweb="toast"] {
        background-color: #311B92;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE MANAGEMENT ---
if 'user' not in st.session_state:
    st.session_state.user = None # {email, name, institution, year}
if 'page' not in st.session_state:
    st.session_state.page = 'login'
if 'spaces' not in st.session_state:
    st.session_state.spaces = {"Research": [], "Paper": [], "Study": []}
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
# Check secrets for API key, else fallback to empty
if 'api_key' not in st.session_state:
    try:
        st.session_state.api_key = st.secrets["GEMINI_API_KEY"]
    except:
        st.session_state.api_key = ""

# --- MOCK DATABASE ---
INSTITUTIONS = [
    "Tamil Nadu National Law University (TNNLU)",
    "National Law School of India University (NLSIU)",
    "NALSAR University of Law",
    "National Law University, Delhi (NLUD)",
    "The West Bengal National University of Juridical Sciences (NUJS)",
    "Symbiosis Law School",
    "School of Law, Christ University",
    "M.I.E.T. Engineering College (Tech Law Dept)", 
    "Dr. Ambedkar Government Law College",
    "Vel Tech School of Law",
]

# --- HELPER FUNCTIONS ---
def set_page(page_name):
    st.session_state.page = page_name

def logout():
    st.session_state.user = None
    st.session_state.page = 'login'

def authenticate(email, password):
    # Mock authentication
    if "@" in email and len(password) > 3:
        return True
    return False

def get_ai_response(query, tone, difficulty, context="general"):
    """
    Interacts with Gemini API.
    """
    if not st.session_state.api_key:
        return "⚠️ Please enter your Gemini API Key in the sidebar settings or set it in Streamlit Secrets."
    
    genai.configure(api_key=st.session_state.api_key)
    
    # 1. Dynamically find a working model
    # This prevents 404 errors by asking the API "what models do I have access to?"
    target_model_name = "gemini-1.5-flash" # Default fallback
    try:
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        # Priority Logic: Prefer Flash -> Pro -> Flash Legacy -> Pro Legacy
        if any('gemini-1.5-flash' in m for m in available_models):
             target_model_name = 'gemini-1.5-flash'
        elif any('gemini-1.5-pro' in m for m in available_models):
             target_model_name = 'gemini-1.5-pro'
        elif len(available_models) > 0:
             # Pick the first one that looks like a gemini model
             target_model_name = available_models[0]
    except Exception:
        # If list_models fails (e.g. permission issues), we stick to the default fallback
        pass

    prompt = f"""
    You are VidhiDesk, an expert Indian legal assistant.
    User Query: {query}
    
    Constraints:
    1. Tone: {tone}
    2. Difficulty: {difficulty}
    3. Context: {context} (If 'bare act', quote the law precisely).
    
    Provide a clear, structured response fitting these constraints. 
    Use markdown formatting (bolding, lists) to make it readable on a dark background.
    If appropriate, include relevant Case Laws.
    """
    
    try:
        model = genai.GenerativeModel(target_model_name)
        with st.spinner(f"Consulting the legal archives ({target_model_name})..."):
            response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error connecting to Gemini ({target_model_name}): {str(e)}"

# --- PAGES ---

def login_page():
    # Centered Logo/Title
    st.markdown("""
        <div style='text-align: center; margin-top: 50px; margin-bottom: 30px;'>
            <h1 style='font-size: 3.5rem; background: -webkit-linear-gradient(#BB86FC, #6200EA); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
                ⚖️ VidhiDesk
            </h1>
            <p style='color: #9E9E9E; font-size: 1.2rem;'>Your AI Legal Research Companion</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        st.markdown("<div class='css-card animate-fade'>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            email = st.text_input("Email", key="login_email", placeholder="student@law.edu")
            password = st.text_input("Password", type="password", key="login_pass", placeholder="••••••••")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Log In", use_container_width=True):
                if authenticate(email, password):
                    st.session_state.user = {"email": email, "name": "User", "setup_complete": False}
                    st.session_state.page = "profile_setup"
                    st.rerun()
                else:
                    st.error("Invalid credentials")
            
            st.markdown("<div style='text-align: center; margin: 15px 0; color: #555;'>— OR —</div>", unsafe_allow_html=True)
            
            if st.button("🔵 Continue with Google", use_container_width=True):
                st.info("Google Auth simulation: Redirecting...")
                time.sleep(1)
                st.session_state.user = {"email": "user@gmail.com", "name": "Google User", "setup_complete": False}
                st.session_state.page = "profile_setup"
                st.rerun()

        with tab2:
            st.text_input("New Email", placeholder="student@law.edu")
            st.text_input("New Password", type="password", placeholder="Create a strong password")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Sign Up", use_container_width=True):
                st.success("Account created! Please log in.")
        
        st.markdown("</div>", unsafe_allow_html=True)

def profile_setup():
    st.markdown("<div class='animate-fade'>", unsafe_allow_html=True)
    st.title("Complete Your Profile")
    st.write("Tell us about your academic background to personalize your experience.")
    
    with st.container():
        st.markdown("<div class='css-card'>", unsafe_allow_html=True)
        full_name = st.text_input("Full Name")
        institution = st.selectbox("Institution", INSTITUTIONS)
        year = st.selectbox("Year of Study", ["1st Year", "2nd Year", "3rd Year", "4th Year", "5th Year", "LLM/PhD", "Graduate"])
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Complete Setup"):
            if full_name and institution:
                st.session_state.user['name'] = full_name
                st.session_state.user['institution'] = institution
                st.session_state.user['year'] = year
                st.session_state.user['setup_complete'] = True
                st.session_state.page = "home"
                st.rerun()
            else:
                st.warning("Please fill in all fields.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def sidebar():
    with st.sidebar:
        st.markdown("<h2 style='color: #BB86FC;'>VidhiDesk</h2>", unsafe_allow_html=True)
        st.markdown(f"**{st.session_state.user['name']}**")
        st.caption(f"{st.session_state.user['institution']}")
        
        st.markdown("---")
        
        if st.button("🏠 Home", use_container_width=True): set_page("home")
        if st.button("🗂️ Spaces", use_container_width=True): set_page("spaces")
        if st.button("⚙️ Settings", use_container_width=True): set_page("settings")
        
        st.markdown("---")
        # API Key input
        api_input = st.text_input("Gemini API Key", type="password", value=st.session_state.api_key, help="Leave empty if using Secrets")
        if api_input:
            st.session_state.api_key = api_input
            
        st.markdown("---")
        if st.button("Logout"): logout()

def home_page():
    st.markdown("<h1 class='animate-fade'>Legal Research Assistant</h1>", unsafe_allow_html=True)
    
    # --- Control Panel ---
    col1, col2, col3 = st.columns(3)
    with col1:
        tone = st.selectbox("Tone", ["Informative", "Academic", "Casual"])
    with col2:
        difficulty = st.selectbox("Difficulty", ["Simple", "Intermediate", "Bare Act"])
    with col3:
        target_space = st.selectbox("Save to Space", ["None", "Research", "Paper", "Study"])

    # --- Chat Interface ---
    st.markdown("<br>", unsafe_allow_html=True)
    query = st.text_input("Ask about Indian Laws, Acts, or Amendments...", placeholder="e.g., Explain Article 21 of the Indian Constitution")
    
    if st.button("Analyze", type="primary"):
        if query:
            response = get_ai_response(query, tone, difficulty)
            
            # Display Result
            st.markdown(f"""
            <div class='css-card animate-fade'>
                <h3 style='color: #BB86FC;'>🏛️ Analysis</h3>
                <div style='color: #E0E0E0; line-height: 1.6;'>{response}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Save to Space Logic
            if target_space != "None":
                entry = {
                    "id": str(uuid.uuid4()),
                    "query": query,
                    "response": response,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M")
                }
                st.session_state.spaces[target_space].append(entry)
                st.toast(f"Saved to {target_space} Space!", icon="✅")

def spaces_page():
    st.markdown("<h1 class='animate-fade'>My Spaces</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📚 Research", "📝 Paper", "🎓 Study"])
    
    def render_space(space_name):
        items = st.session_state.spaces[space_name]
        
        # AI Insight for the Space
        if items:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(f"✨ Generate AI Insights for {space_name}"):
                combined_text = " ".join([item['query'] for item in items])
                insight = get_ai_response(f"Provide a high-level summary/insight connecting these legal topics: {combined_text}", "Academic", "Intermediate", context="insight")
                st.markdown(f"""
                <div class='css-card' style='border-left-color: #03DAC6;'>
                    <strong style='color: #03DAC6;'>AI Insight:</strong>
                    <br>{insight}
                </div>
                """, unsafe_allow_html=True)
        
        if not items:
            st.info(f"Your {space_name} space is empty. Start researching!")
        else:
            for item in items:
                with st.expander(f"📄 {item['query']} ({item['timestamp']})"):
                    st.markdown(item['response'])
                    if st.button("Delete", key=item['id']):
                        st.session_state.spaces[space_name].remove(item)
                        st.rerun()

    with tab1: render_space("Research")
    with tab2: render_space("Paper")
    with tab3: render_space("Study")

# --- MAIN ROUTER ---

if st.session_state.page == "login":
    login_page()
elif st.session_state.page == "profile_setup":
    profile_setup()
else:
    # Authenticated Pages
    sidebar()
    if st.session_state.page == "home":
        home_page()
    elif st.session_state.page == "spaces":
        spaces_page()
    elif st.session_state.page == "settings":
        st.title("Settings")
        st.markdown("<div class='css-card'>User Preferences and Account Management would go here.</div>", unsafe_allow_html=True)
