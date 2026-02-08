import streamlit as st
import google.generativeai as genai
import time
import uuid
import hashlib
import sqlite3
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(
    page_title="VidhiDesk | Legal Research Hub",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM THEME (Major Black - Minor Purple) ---
st.markdown("""
<style>
    /* 1. GLOBAL STYLES */
    .stApp {
        background-color: #050505;
        color: #E0E0E0;
    }
    
    /* 2. SIDEBAR */
    section[data-testid="stSidebar"] {
        background-color: #0a0a0a;
        border-right: 1px solid #1F1F1F;
    }
    section[data-testid="stSidebar"] h1, h2, h3, p, label {
        color: #D1C4E9 !important;
    }

    /* 3. INPUT FIELDS */
    .stTextInput > div > div > input, 
    .stSelectbox > div > div > div, 
    .stChatInput textarea {
        background-color: #121212;
        color: #FFFFFF;
        border: 1px solid #2D1B4E;
        border-radius: 12px;
    }
    .stTextInput > div > div > input:focus,
    .stChatInput textarea:focus {
        border-color: #BB86FC;
        box-shadow: 0 0 10px rgba(187, 134, 252, 0.2);
    }

    /* 4. BUTTONS */
    .stButton > button {
        background: linear-gradient(135deg, #6200EA 0%, #3700B3 100%);
        color: white;
        border: none;
        border-radius: 20px;
        font-weight: 500;
        padding: 0.5rem 1.2rem;
        transition: transform 0.2s;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 12px rgba(98, 0, 234, 0.4);
    }
    button[kind="secondary"] {
        background: transparent;
        border: 1px solid #BB86FC;
    }

    /* 5. CARDS & CONTAINERS */
    .css-card {
        background-color: #121212;
        padding: 25px;
        border-radius: 16px;
        border: 1px solid #222;
        border-left: 4px solid #BB86FC;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }

    /* 6. CHAT BUBBLES */
    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 15px;
        padding-bottom: 20px;
    }
    .msg-row {
        display: flex;
        width: 100%;
    }
    .msg-row.user {
        justify-content: flex-end;
    }
    .msg-row.ai {
        justify-content: flex-start;
    }
    .chat-bubble {
        max-width: 80%;
        padding: 12px 18px;
        border-radius: 16px;
        line-height: 1.5;
        font-size: 1rem;
        position: relative;
    }
    .chat-bubble.user {
        background-color: #2D1B4E; /* Deep Purple */
        color: #FFF;
        border-bottom-right-radius: 2px;
    }
    .chat-bubble.ai {
        background-color: #1E1E1E; /* Dark Grey */
        color: #E0E0E0;
        border: 1px solid #333;
        border-bottom-left-radius: 2px;
    }

    /* 7. LOADING ANIMATION */
    .typing {
        display: flex;
        gap: 5px;
        padding: 10px;
        background: #1E1E1E;
        border-radius: 12px;
        width: fit-content;
        border: 1px solid #333;
    }
    .dot {
        width: 8px;
        height: 8px;
        background: #BB86FC;
        border-radius: 50%;
        animation: bounce 1.4s infinite ease-in-out both;
    }
    .dot:nth-child(1) { animation-delay: -0.32s; }
    .dot:nth-child(2) { animation-delay: -0.16s; }
    @keyframes bounce {
        0%, 80%, 100% { transform: scale(0); }
        40% { transform: scale(1); }
    }

    /* HEADERS */
    h1, h2, h3 { color: #BB86FC !important; }
</style>
""", unsafe_allow_html=True)

# --- DATABASE BACKEND (SQLite) ---
class DatabaseManager:
    def __init__(self, db_name="vidhidesk.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        c = self.conn.cursor()
        # Users
        c.execute("""CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY, password TEXT, name TEXT, institution TEXT, year TEXT, setup_complete BOOLEAN
        )""")
        # Spaces
        c.execute("""CREATE TABLE IF NOT EXISTS spaces (
            id TEXT PRIMARY KEY, email TEXT, category TEXT, query TEXT, response TEXT, timestamp TEXT
        )""")
        # Chat History
        c.execute("""CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, role TEXT, content TEXT, timestamp TEXT
        )""")
        self.conn.commit()
        # Default Admin
        try:
            admin_pw = hashlib.sha256("admin123".encode()).hexdigest()
            c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)", 
                     ("admin@law.edu", admin_pw, "Administrator", "VidhiDesk HQ", "Graduate", True))
            self.conn.commit()
        except sqlite3.IntegrityError: pass

    def register(self, email, password):
        try:
            pw_hash = hashlib.sha256(password.encode()).hexdigest()
            self.conn.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)", 
                             (email, pw_hash, "New User", "", "", False))
            self.conn.commit()
            return True, "Registered successfully!"
        except sqlite3.IntegrityError:
            return False, "Email already exists."

    def login(self, email, password):
        pw_hash = hashlib.sha256(password.encode()).hexdigest()
        cur = self.conn.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, pw_hash))
        row = cur.fetchone()
        if row:
            return True, {"email": row[0], "name": row[2], "institution": row[3], "year": row[4], "setup_complete": row[5]}
        return False, "Invalid credentials."

    def update_profile(self, email, name, institution, year):
        self.conn.execute("UPDATE users SET name=?, institution=?, year=?, setup_complete=? WHERE email=?", 
                         (name, institution, year, True, email))
        self.conn.commit()

    def save_chat(self, email, role, content):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.conn.execute("INSERT INTO chat_history (email, role, content, timestamp) VALUES (?, ?, ?, ?)", 
                         (email, role, content, ts))
        self.conn.commit()

    def get_history(self, email):
        cur = self.conn.execute("SELECT role, content FROM chat_history WHERE email=? ORDER BY id ASC", (email,))
        return [{"role": r[0], "content": r[1]} for r in cur.fetchall()]

    def clear_history(self, email):
        self.conn.execute("DELETE FROM chat_history WHERE email=?", (email,))
        self.conn.commit()

    def save_space(self, email, category, query, response):
        id_ = str(uuid.uuid4())
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.conn.execute("INSERT INTO spaces VALUES (?, ?, ?, ?, ?, ?)", (id_, email, category, query, response, ts))
        self.conn.commit()

    def get_spaces(self, email, category):
        cur = self.conn.execute("SELECT id, query, response, timestamp FROM spaces WHERE email=? AND category=? ORDER BY timestamp DESC", (email, category))
        return [{"id": r[0], "query": r[1], "response": r[2], "timestamp": r[3]} for r in cur.fetchall()]

    def delete_space(self, item_id):
        self.conn.execute("DELETE FROM spaces WHERE id=?", (item_id,))
        self.conn.commit()

db = DatabaseManager()

# --- CONSTANTS ---
INSTITUTIONS = sorted([
    "National Law School of India University (NLSIU), Bangalore", "National Law University, Delhi (NLUD)",
    "NALSAR University of Law, Hyderabad", "The West Bengal National University of Juridical Sciences (WBNUJS)",
    "National Law University, Jodhpur (NLUJ)", "Hidayatullah National Law University (HNLU), Raipur",
    "Gujarat National Law University (GNLU), Gandhinagar", "Dr. Ram Manohar Lohiya National Law University (RMLNLU)",
    "Rajiv Gandhi National University of Law (RGNUL), Patiala", "Chanakya National Law University (CNLU), Patna",
    "National University of Advanced Legal Studies (NUALS), Kochi", "National Law University Odisha (NLUO)",
    "National University of Study and Research in Law (NUSRL), Ranchi", "National Law University and Judicial Academy (NLUJAA)",
    "Damodaram Sanjivayya National Law University (DSNLU)", "Tamil Nadu National Law University (TNNLU)",
    "Maharashtra National Law University (MNLU), Mumbai", "Maharashtra National Law University (MNLU), Nagpur",
    "Maharashtra National Law University (MNLU), Aurangabad", "Himachal Pradesh National Law University (HPNLU)",
    "Dharmashastra National Law University (DNLU), Jabalpur", "Dr. B.R. Ambedkar National Law University (DBRANLU)",
    "National Law University, Tripura (NLUT)", "GNLU Silvassa Campus", "Dr. Rajendra Prasad National Law University",
    "Faculty of Law, University of Delhi (DU)", "Faculty of Law, Banaras Hindu University (BHU)",
    "Faculty of Law, Aligarh Muslim University (AMU)", "Faculty of Law, Jamia Millia Islamia",
    "Government Law College (GLC), Mumbai", "Symbiosis Law School (SLS), Pune", "Symbiosis Law School (SLS), Noida",
    "School of Law, Christ University", "Army Institute of Law (AIL), Mohali", "Lloyd Law College",
    "KIIT School of Law", "Saveetha School of Law", "School of Law, SASTRA Deemed University",
    "School of Law, UPES", "Institute of Law, Nirma University", "Amity Law School",
    "VIT School of Law (VITSOL)", "M.I.E.T. Engineering College (Tech Law Dept)", "Vel Tech School of Law",
    "Dr. Ambedkar Government Law College, Chennai"
])

# --- SESSION & STATE ---
if 'user' not in st.session_state: st.session_state.user = None
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'api_key' not in st.session_state: 
    st.session_state.api_key = st.secrets.get("GEMINI_API_KEY", "")

# --- AI ENGINE ---
def get_ai_response(query, tone, difficulty, context="general"):
    if not st.session_state.api_key:
        return "⚠️ Please enter your Gemini API Key in the sidebar."
    
    genai.configure(api_key=st.session_state.api_key)
    
    # Model Fallback Logic
    target_model = "gemini-1.5-flash"
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if any('gemini-1.5-flash' in m for m in models): target_model = 'gemini-1.5-flash'
        elif any('gemini-pro' in m for m in models): target_model = 'gemini-pro'
    except: pass

    prompt = f"""
    Act as VidhiDesk, an Indian Legal Research Assistant.
    Query: {query}
    Tone: {tone} | Difficulty: {difficulty} | Context: {context}
    
    Mandate:
    1. Cite specific Articles/Sections of Indian Acts (Constitution, BNS, IPC, etc).
    2. Reference relevant Supreme Court Case Laws if applicable.
    3. Structure with Markdown (Headers, Bullets).
    """
    try:
        model = genai.GenerativeModel(target_model)
        return model.generate_content(prompt).text
    except Exception as e:
        return f"Error: {str(e)}"

# --- PAGES ---

def page_login():
    st.markdown("<div style='text-align: center; margin-top: 50px;'><h1 style='font-size: 3.5rem;'>⚖️ VidhiDesk</h1><p style='color:#888;'>Your Intelligent Legal Research Hub</p></div>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown("<div class='css-card'>", unsafe_allow_html=True)
        tab_login, tab_reg = st.tabs(["Login", "Register"])
        
        with tab_login:
            email = st.text_input("Email", key="l_email")
            pwd = st.text_input("Password", type="password", key="l_pwd")
            if st.button("Access Hub", use_container_width=True):
                success, data = db.login(email, pwd)
                if success:
                    st.session_state.user = data
                    st.session_state.page = "home" if data['setup_complete'] else "profile"
                    st.rerun()
                else: st.error(data)
                
        with tab_reg:
            r_email = st.text_input("Email", key="r_email")
            r_pwd = st.text_input("Password", type="password", key="r_pwd")
            if st.button("Create Account", use_container_width=True):
                if len(r_pwd) < 6: st.warning("Password too short")
                else:
                    success, msg = db.register(r_email, r_pwd)
                    if success: st.success(msg)
                    else: st.error(msg)
        st.markdown("</div>", unsafe_allow_html=True)

def page_profile():
    st.markdown("## 👤 Profile Setup")
    with st.container():
        st.markdown("<div class='css-card'>", unsafe_allow_html=True)
        name = st.text_input("Full Name")
        inst = st.selectbox("Institution", INSTITUTIONS)
        year = st.selectbox("Year of Study", ["1st Year", "2nd Year", "3rd Year", "4th Year", "5th Year", "LLM", "PhD"])
        
        if st.button("Complete Setup"):
            if name:
                db.update_profile(st.session_state.user['email'], name, inst, year)
                st.session_state.user.update({"name": name, "institution": inst, "year": year})
                st.session_state.page = "home"
                st.rerun()
            else: st.warning("Name required")
        st.markdown("</div>", unsafe_allow_html=True)

def sidebar():
    with st.sidebar:
        st.markdown(f"### {st.session_state.user['name']}")
        st.caption(st.session_state.user['institution'])
        st.markdown("---")
        
        if st.button("🏠 Home", use_container_width=True): st.session_state.page = "home"; st.rerun()
        if st.button("🗂️ Spaces", use_container_width=True): st.session_state.page = "spaces"; st.rerun()
        
        st.markdown("---")
        key_input = st.text_input("Gemini API Key", value=st.session_state.api_key, type="password")
        if key_input: st.session_state.api_key = key_input
        
        if st.button("Logout", type="secondary"):
            st.session_state.user = None
            st.session_state.page = "login"
            st.rerun()

def page_home():
    st.markdown("## 🏛️ Research Assistant")
    
    # Settings
    with st.expander("⚙️ Parameters", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1: tone = st.selectbox("Tone", ["Informative", "Academic", "Casual"])
        with c2: diff = st.selectbox("Difficulty", ["Simple", "Intermediate", "Bare Act"])
        with c3: space = st.selectbox("Auto-Save", ["None", "Research", "Paper", "Study"])

    # History Logic
    email = st.session_state.user['email']
    history = db.get_history(email)
    
    # 1. Display Chat History
    for msg in history:
        css_class = "user" if msg['role'] == "user" else "ai"
        st.markdown(f"""
            <div class='msg-row {css_class}'>
                <div class='chat-bubble {css_class}'>
                    {msg['content']}
                </div>
            </div>
        """, unsafe_allow_html=True)

    # 2. Handle Input
    if query := st.chat_input("Ask about Indian Laws, Sections, or Case Laws..."):
        # Save User Msg
        db.save_chat(email, "user", query)
        st.rerun()

    # 3. Process Pending Response (If last msg was user)
    if history and history[-1]['role'] == "user":
        latest_query = history[-1]['content']
        
        # Render Loading Animation
        st.markdown("""
            <div class='msg-row ai'>
                <div class='typing'>
                    <div class='dot'></div><div class='dot'></div><div class='dot'></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Generate
        response = get_ai_response(latest_query, tone, diff)
        
        # Save & Refresh
        db.save_chat(email, "ai", response)
        if space != "None":
            db.save_space(email, space, latest_query, response)
            st.toast(f"Saved to {space}!", icon="💾")
        st.rerun()

    # Clear Button
    if history:
        if st.button("Clear Chat", type="secondary"):
            db.clear_history(email)
            st.rerun()

def page_spaces():
    st.markdown("## 🗂️ Knowledge Spaces")
    email = st.session_state.user['email']
    
    tabs = st.tabs(["📚 Research", "📝 Paper", "🎓 Study"])
    cats = ["Research", "Paper", "Study"]
    
    for tab, cat in zip(tabs, cats):
        with tab:
            items = db.get_spaces(email, cat)
            if items:
                # Export
                report_text = f"VidhiDesk {cat} Report\nGenerated: {datetime.now()}\n\n"
                for i in items:
                    report_text += f"Q: {i['query']}\nA: {i['response']}\n{'-'*40}\n\n"
                
                st.download_button(f"📥 Download {cat} Report", report_text, file_name=f"{cat}_Report.txt")
                
                # List Items
                for item in items:
                    with st.expander(f"📄 {item['query'][:80]}...", expanded=False):
                        st.markdown(item['response'])
                        st.caption(f"Saved: {item['timestamp']}")
                        if st.button("Delete", key=item['id']):
                            db.delete_space(item['id'])
                            st.rerun()
            else:
                st.info(f"No items in {cat} space.")

# --- ROUTER ---
if st.session_state.page == "login":
    page_login()
elif st.session_state.page == "profile":
    page_profile()
elif st.session_state.user:
    sidebar()
    if st.session_state.page == "home": page_home()
    elif st.session_state.page == "spaces": page_spaces()
else:
    page_login()
