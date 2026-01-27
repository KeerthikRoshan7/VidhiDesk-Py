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

# --- CUSTOM CSS (Beige-Purple Theme, Rounded UI) ---
st.markdown("""
<style>
    /* Main Background - Beige */
    .stApp {
        background-color: #F9F7F2;
        color: #333333;
    }
    
    /* Sidebar - Deep Purple */
    [data-testid="stSidebar"] {
        background-color: #2E1A47;
    }
    [data-testid="stSidebar"] * {
        color: #F9F7F2 !important;
    }

    /* Buttons - Purple & Rounded */
    .stButton > button {
        background-color: #6A0DAD;
        color: white;
        border-radius: 25px;
        border: none;
        padding: 10px 24px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stButton > button:hover {
        background-color: #8A2BE2;
        transform: translateY(-2px);
    }

    /* Input Fields - Rounded */
    .stTextInput > div > div > input, .stSelectbox > div > div > div {
        border-radius: 15px;
        background-color: #FFFFFF;
        border: 1px solid #D1C4E9;
    }

    /* Cards/Containers */
    .css-card {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 20px;
        box-shadow: 0 4px 15px rgba(106, 13, 173, 0.1);
        margin-bottom: 20px;
        border-left: 5px solid #6A0DAD;
    }

    /* Headers */
    h1, h2, h3 {
        font-family: 'Helvetica Neue', sans-serif;
        color: #4A148C;
    }
    
    /* Animations */
    @keyframes fadeIn {
        0% { opacity: 0; transform: translateY(10px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    .animate-fade {
        animation: fadeIn 0.8s ease-out;
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
# Check if API key is in secrets, otherwise default to empty
if 'api_key' not in st.session_state:
    st.session_state.api_key = st.secrets["GEMINI_API_KEY"] if "GEMINI_API_KEY" in st.secrets else ""

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
    # ... In a real app, this list would contain all ~100 institutions
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
        return "⚠️ Please enter your Gemini API Key in the sidebar settings."
    
    genai.configure(api_key=st.session_state.api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    You are VidhiDesk, an expert Indian legal assistant.
    User Query: {query}
    
    Constraints:
    1. Tone: {tone}
    2. Difficulty: {difficulty}
    3. Context: {context} (If 'bare act', quote the law precisely).
    
    Provide a clear, structured response fitting these constraints. 
    If appropriate, include relevant Case Laws.
    """
    
    try:
        with st.spinner("Consulting the legal archives..."):
            response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

# --- PAGES ---

def login_page():
    st.markdown("<div style='text-align: center; margin-top: 50px;'><h1 style='font-size: 3rem;'>⚖️ VidhiDesk</h1><p>Your AI Legal Research Companion</p></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        st.markdown("<div class='css-card animate-fade'>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_pass")
            if st.button("Log In", use_container_width=True):
                if authenticate(email, password):
                    # Mock fetching user profile
                    st.session_state.user = {"email": email, "name": "User", "setup_complete": False}
                    st.session_state.page = "profile_setup"
                    st.rerun()
                else:
                    st.error("Invalid credentials")
            st.markdown("---")
            if st.button("🔵 Continue with Google", use_container_width=True):
                st.info("Google Auth simulation: Redirecting...")
                time.sleep(1)
                st.session_state.user = {"email": "user@gmail.com", "name": "Google User", "setup_complete": False}
                st.session_state.page = "profile_setup"
                st.rerun()

        with tab2:
            st.text_input("New Email")
            st.text_input("New Password", type="password")
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
        st.title("VidhiDesk")
        st.write(f"👤 **{st.session_state.user['name']}**")
        st.caption(f"{st.session_state.user['institution']}")
        
        st.markdown("---")
        
        if st.button("🏠 Home", use_container_width=True): set_page("home")
        if st.button("🗂️ Spaces", use_container_width=True): set_page("spaces")
        if st.button("⚙️ Settings", use_container_width=True): set_page("settings")
        
        st.markdown("---")
        # API Key input for the prototype
        api_input = st.text_input("Gemini API Key", type="password", value=st.session_state.api_key)
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
            st.markdown(f"<div class='css-card animate-fade'><h3>🏛️ Analysis</h3>{response}</div>", unsafe_allow_html=True)
            
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
            if st.button(f"✨ Generate AI Insights for {space_name}"):
                combined_text = " ".join([item['query'] for item in items])
                insight = get_ai_response(f"Provide a high-level summary/insight connecting these legal topics: {combined_text}", "Academic", "Intermediate", context="insight")
                st.info(f"**AI Insight:** {insight}")
        
        if not items:
            st.info(f"Your {space_name} space is empty. Start researching!")
        else:
            for item in items:
                with st.expander(f"📄 {item['query']} ({item['timestamp']})"):
                    st.write(item['response'])
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
        st.write("User Preferences and Account Management would go here.")
