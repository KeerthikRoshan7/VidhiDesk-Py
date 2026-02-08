import streamlit as st
import google.generativeai as genai
import sqlite3
import hashlib
import time
from datetime import datetime

# --- 1. APP CONFIGURATION ---
st.set_page_config(
    page_title="VidhiDesk | Legal Intelligence",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. OBSIDIAN & GOLD THEME ---
st.markdown("""
<style>
    /* MAIN BACKGROUND - Obsidian Black */
    .stApp {
        background-color: #050505;
        color: #E0E0E0;
    }
    
    /* SIDEBAR - Charcoal */
    section[data-testid="stSidebar"] {
        background-color: #0F0F0F;
        border-right: 1px solid #333;
    }
    
    /* HEADERS - Gold Gradient */
    h1, h2, h3 {
        background: linear-gradient(90deg, #D4AF37, #F2D06B);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'Cinzel', serif; /* Elegant font if avail, else serif */
    }
    
    /* BUTTONS - Gold Leaf Style */
    .stButton > button {
        background: linear-gradient(135deg, #B8860B 0%, #D4AF37 100%);
        color: #000000;
        border: none;
        border-radius: 4px;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(212, 175, 55, 0.4);
        color: #000;
    }
    
    /* SECONDARY BUTTONS - Gold Outline */
    button[kind="secondary"] {
        background: transparent !important;
        border: 1px solid #D4AF37 !important;
        color: #D4AF37 !important;
    }

    /* INPUT FIELDS - Matte Black */
    .stTextInput > div > div > input, 
    .stSelectbox > div > div > div, 
    .stChatInput textarea {
        background-color: #121212;
        color: #E0E0E0;
        border: 1px solid #333;
        border-radius: 4px;
    }
    .stTextInput > div > div > input:focus,
    .stChatInput textarea:focus {
        border-color: #D4AF37;
        box-shadow: 0 0 8px rgba(212, 175, 55, 0.2);
    }

    /* CHAT MESSAGES */
    .stChatMessage {
        background-color: #0F0F0F;
        border: 1px solid #222;
        border-radius: 8px;
    }
    .stChatMessage[data-testid="stChatMessageAvatar"] {
        background-color: #D4AF37;
    }

    /* TABS */
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background-color: #121212;
        color: #D4AF37;
        border-bottom-color: #D4AF37;
    }
    
    /* CARDS/EXPANDERS */
    .streamlit-expanderHeader {
        background-color: #121212;
        border: 1px solid #333;
        color: #D4AF37 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. DATABASE MANAGER ---
class DBHandler:
    def __init__(self, db_name="vidhidesk_users.db"):
        self.db_name = db_name
        self.verify_db()

    def get_connection(self):
        return sqlite3.connect(self.db_name, check_same_thread=False)

    def verify_db(self):
        try:
            conn = self.get_connection()
            conn.execute("SELECT 1 FROM users LIMIT 1")
            conn.close()
        except sqlite3.OperationalError:
            self.create_schema()

    def create_schema(self):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, password TEXT, name TEXT, institution TEXT, year TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS chats (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, role TEXT, content TEXT, timestamp DATETIME)''')
        c.execute('''CREATE TABLE IF NOT EXISTS spaces (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, category TEXT, query TEXT, response TEXT, timestamp DATETIME)''')
        conn.commit()
        conn.close()

    def login(self, email, password):
        conn = self.get_connection()
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        cur = conn.execute("SELECT name, institution, year FROM users WHERE email=? AND password=?", (email, hashed_pw))
        user = cur.fetchone()
        conn.close()
        if user:
            return {"email": email, "name": user[0], "institution": user[1], "year": user[2]}
        return None

    def save_message(self, email, role, content):
        conn = self.get_connection()
        conn.execute("INSERT INTO chats (email, role, content, timestamp) VALUES (?, ?, ?, ?)", 
                     (email, role, content, datetime.now()))
        conn.commit()
        conn.close()

    def get_history(self, email):
        conn = self.get_connection()
        cur = conn.execute("SELECT role, content FROM chats WHERE email=? ORDER BY id ASC", (email,))
        data = [{"role": row[0], "content": row[1]} for row in cur.fetchall()]
        conn.close()
        return data

    def clear_history(self, email):
        conn = self.get_connection()
        conn.execute("DELETE FROM chats WHERE email=?", (email,))
        conn.commit()
        conn.close()

    def save_to_space(self, email, category, query, response):
        conn = self.get_connection()
        conn.execute("INSERT INTO spaces (email, category, query, response, timestamp) VALUES (?, ?, ?, ?, ?)", 
                     (email, category, query, response, datetime.now()))
        conn.commit()
        conn.close()

    def get_space_items(self, email, category):
        conn = self.get_connection()
        cur = conn.execute("SELECT id, query, response, timestamp FROM spaces WHERE email=? AND category=? ORDER BY id DESC", (email, category))
        data = [{"id": r[0], "query": r[1], "response": r[2], "timestamp": r[3]} for r in cur.fetchall()]
        conn.close()
        return data

    def delete_space_item(self, item_id):
        conn = self.get_connection()
        conn.execute("DELETE FROM spaces WHERE id=?", (item_id,))
        conn.commit()
        conn.close()

db = DBHandler()

# --- 4. AI ENGINE (ROBUST MODEL HUNTER) ---
def get_gemini_response(query, tone, difficulty, institution, api_key):
    # FALLBACK: If API key is empty string, try using the hardcoded one explicitly
    if not api_key:
        api_key = "AIzaSyBXwTtS5c6OsGQ_nI_tR-meZaRBCFZgkGY"

    genai.configure(api_key=api_key)
    
    sys_instruction = f"""
    ROLE: You are VidhiDesk, an elite legal research assistant for {institution}.
    TONE: {tone} | DEPTH: {difficulty}
    
    MANDATE:
    1. PRIORITIZE Indian Statutes: BNS (Bharatiya Nyaya Sanhita), BNSS, BSA, and Constitution.
    2. COMPARE with old acts (IPC/CrPC/Evidence Act) where relevant.
    3. CITE relevant Case Laws (Supreme Court/High Court) with year.
    4. FORMAT using Markdown: Use '### Headers', '**Bold**' for emphasis, and '>' for blockquotes.
    """

    # Try models in priority order
    models = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-2.0-flash-exp']
    
    last_error = "Unknown Error"

    for model_name in models:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(f"{sys_instruction}\n\nUSER QUERY: {query}")
            return response.text # Success
        except Exception as e:
            last_error = str(e)
            continue # Try next

    # Return the ACTUAL error message from the last attempt for debugging
    return f"❌ **Connection Failed:** Could not reach Google AI.\n\n**Debug Details:** {last_error}"

# --- 5. UI COMPONENTS ---

# Session Init
if "user" not in st.session_state: st.session_state.user = None

# HARDCODED API KEY INTEGRATION (FORCE UPDATE)
# We check if it is missing OR empty, then force fill it.
if "api_key" not in st.session_state or not st.session_state.api_key: 
    st.session_state.api_key = "AIzaSyBXwTtS5c6OsGQ_nI_tR-meZaRBCFZgkGY"

def login_page():
    # Centered Login Card
    c1, c2, c3 = st.columns([1, 0.6, 1])
    with c2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center; font-size: 3rem;'>⚖️ VidhiDesk</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #D4AF37; margin-bottom: 30px;'>EXCLUSIVE LEGAL RESEARCH HUB</p>", unsafe_allow_html=True)
        
        with st.container(border=True):
            email = st.text_input("Access ID (Email)")
            password = st.text_input("Secure Key (Password)", type="password")
            
            if st.button("Authenticate", use_container_width=True):
                user = db.login(email, password)
                if user:
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("Access Denied: Invalid Credentials")

def main_app():
    # --- SIDEBAR ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/924/924915.png", width=40)
        st.markdown(f"### {st.session_state.user['name']}")
        st.caption(f"🏛 {st.session_state.user['institution']}")
        
        st.markdown("---")
        nav = st.radio("MODULES", ["Research Assistant", "Knowledge Spaces"], label_visibility="collapsed")
        
        st.markdown("---")
        st.markdown("#### 🔑 API Key")
        # Pre-filled API Key from Session State
        api_key_input = st.text_input("Gemini API Key", type="password", value=st.session_state.api_key, label_visibility="collapsed")
        # If user manually changes it, update session state
        if api_key_input: 
            st.session_state.api_key = api_key_input

        st.markdown("---")
        if st.button("Terminate Session"):
            st.session_state.user = None
            st.rerun()

    # --- RESEARCH ASSISTANT ---
    if nav == "Research Assistant":
        st.title("Research Assistant")
        st.markdown(f"Welcome back, **{st.session_state.user['name'].split()[0]}**. Ready to analyze?")

        # Filter Bar
        with st.container(border=True):
            c1, c2, c3 = st.columns(3)
            tone = c1.select_slider("Tone", ["Casual", "Professional", "Academic"], value="Academic")
            diff = c2.select_slider("Depth", ["Summary", "Detailed", "Bare Act"], value="Detailed")
            space = c3.selectbox("Auto-Archive", ["None", "Research", "Paper", "Study"])

        # Chat History
        history = db.get_history(st.session_state.user['email'])
        for msg in history:
            avatar = "🧑‍⚖️" if msg['role'] == "user" else "⚖️"
            with st.chat_message(msg['role'], avatar=avatar):
                st.markdown(msg['content'])

        # Input
        if query := st.chat_input("Enter legal query, section, or case citation..."):
            # User Msg
            with st.chat_message("user", avatar="🧑‍⚖️"):
                st.markdown(query)
            db.save_message(st.session_state.user['email'], "user", query)

            # AI Msg
            with st.chat_message("assistant", avatar="⚖️"):
                # Custom Spinner
                with st.spinner("Consulting Legal Archives..."):
                    # Use the key from session state, fallback to hardcoded if empty
                    current_key = st.session_state.api_key if st.session_state.api_key else "AIzaSyBXwTtS5c6OsGQ_nI_tR-meZaRBCFZgkGY"
                    
                    response = get_gemini_response(
                        query, tone, diff, 
                        st.session_state.user['institution'], 
                        current_key
                    )
                    st.markdown(response)
                    db.save_message(st.session_state.user['email'], "assistant", response)

                    if space != "None" and "Connection Failed" not in response:
                        db.save_to_space(st.session_state.user['email'], space, query, response)
                        st.toast(f"Archived to {space}", icon="📂")

        # Clear Button
        if history:
            col1, col2 = st.columns([0.85, 0.15])
            with col2:
                if st.button("Clear Chat", type="secondary"):
                    db.clear_history(st.session_state.user['email'])
                    st.rerun()

    # --- KNOWLEDGE SPACES ---
    elif nav == "Knowledge Spaces":
        st.title("Knowledge Spaces")
        
        tab1, tab2, tab3 = st.tabs(["📚 RESEARCH", "📝 PAPERS", "🎓 STUDY"])
        
        cats = ["Research", "Paper", "Study"]
        for tab, cat in zip([tab1, tab2, tab3], cats):
            with tab:
                items = db.get_space_items(st.session_state.user['email'], cat)
                if not items:
                    st.info(f"Space '{cat}' is empty.", icon="ℹ️")
                else:
                    for item in items:
                        with st.expander(f"📌 {item['timestamp'][:16]} | {item['query'][:60]}..."):
                            st.markdown(item['response'])
                            if st.button("Delete Entry", key=f"del_{item['id']}"):
                                db.delete_space_item(item['id'])
                                st.rerun()

# --- 6. MAIN EXECUTION ---
if __name__ == "__main__":
    if st.session_state.user:
        main_app()
    else:
        login_page()
