import streamlit as st
from google import genai
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

# --- 2. THEME: ULTIMATE OBSIDIAN & LIQUID GOLD ---
st.markdown("""
<style>
    /* IMPORTS */
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');

    /* ANIMATIONS */
    @keyframes fadeInUp {
        from {opacity: 0; transform: translateY(10px);}
        to {opacity: 1; transform: translateY(0);}
    }
    @keyframes subtleGlow {
        0% { box-shadow: 0 0 5px rgba(212, 175, 55, 0.1); }
        50% { box-shadow: 0 0 15px rgba(212, 175, 55, 0.3); }
        100% { box-shadow: 0 0 5px rgba(212, 175, 55, 0.1); }
    }

    /* GLOBAL RESET & PREMIUM BACKGROUND */
    .stApp {
        background-color: #050505;
        color: #E2E8F0;
        font-family: 'Inter', sans-serif;
    }

    /* HIDE DEFAULT HEADER */
    header[data-testid="stHeader"] {
        background: transparent !important;
    }

    /* SIDEBAR STYLING */
    section[data-testid="stSidebar"] {
        background-color: #0A0A0B !important;
        border-right: 1px solid rgba(212, 175, 55, 0.15) !important;
    }
    
    /* TYPOGRAPHY */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Cinzel', serif !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        letter-spacing: 0.05em;
    }
    
    /* TITLES & DIVIDERS */
    .vidhi-title-container {
        width: 100%;
        text-align: center;
        padding-top: 3vh;
        padding-bottom: 2rem;
    }
    .vidhi-title {
        font-size: clamp(2.5rem, 5vw, 4rem); 
        margin: 0 auto;
        background: linear-gradient(135deg, #E6C27A 0%, #FFF4D2 50%, #D4AF37 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        color: transparent;
        letter-spacing: 0.15em; 
        white-space: nowrap !important;
        font-weight: 700 !important;
        text-shadow: 0px 4px 20px rgba(212, 175, 55, 0.15);
    }
    .temple-divider {
        height: 1px;
        width: 200px;
        background: linear-gradient(90deg, transparent, rgba(212, 175, 55, 0.8), transparent);
        margin: 15px auto;
    }
    .vidhi-subtitle {
        color: #94A3B8;
        font-size: 0.8rem;
        letter-spacing: 4px;
        text-transform: uppercase;
        font-weight: 400;
    }

    /* RADIO BUTTONS (SIDEBAR NAV) */
    div[role="radiogroup"] > label > div:first-of-type {
        background-color: #111 !important;
        border-color: #D4AF37 !important;
    }
    div[role="radiogroup"] div[data-testid="stMarkdownContainer"] p {
        font-size: 1rem !important;
        font-weight: 500 !important;
        color: #E2E8F0 !important;
    }

    /* SELECTBOX (DROPDOWNS) - Clean & Sleek */
    div[data-baseweb="select"] > div {
        background-color: #0F0F11 !important;
        border: 1px solid rgba(212, 175, 55, 0.3) !important;
        color: #E2E8F0 !important;
        border-radius: 6px !important;
        transition: all 0.3s ease;
    }
    div[data-baseweb="select"] > div:hover, div[data-baseweb="select"] > div:focus-within {
        border-color: #D4AF37 !important;
        box-shadow: 0 0 10px rgba(212, 175, 55, 0.15) !important;
    }
    
    /* INPUTS & CHAT BOX */
    .stTextInput > div > div > input, .stChatInput textarea {
        background-color: #0F0F11 !important;
        border: 1px solid rgba(212, 175, 55, 0.3) !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        padding: 12px !important;
        transition: all 0.3s ease;
    }
    .stTextInput > div > div > input:focus, .stChatInput textarea:focus {
        border-color: #D4AF37 !important;
        box-shadow: 0 0 15px rgba(212, 175, 55, 0.2) !important;
    }

    /* BUTTONS - ELEGANT GOLD */
    .stButton > button {
        background: linear-gradient(135deg, #1A1500 0%, #2A2205 100%) !important;
        color: #D4AF37 !important;
        font-family: 'Cinzel', serif !important;
        font-weight: 600 !important;
        border: 1px solid rgba(212, 175, 55, 0.5) !important;
        border-radius: 6px !important;
        padding: 0.6rem 2rem !important;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        transition: all 0.3s ease !important;
        width: 100%;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #2A2205 0%, #3D320A 100%) !important;
        border-color: #D4AF37 !important;
        color: #FFF !important;
        box-shadow: 0 4px 15px rgba(212, 175, 55, 0.2) !important;
        transform: translateY(-1px);
    }

    /* CHAT BUBBLES */
    .stChatMessage {
        background-color: #0A0A0B !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        margin-bottom: 1rem !important;
        animation: fadeInUp 0.4s ease-out;
    }
    .stChatMessage[data-testid="stChatMessageAvatar"] {
        background-color: #111 !important;
        border: 1px solid #D4AF37 !important;
        color: #D4AF37 !important;
    }
    
    /* CARDS / CONTAINERS */
    div[data-testid="stContainer"] > div > div > div {
        background-color: #0A0A0B;
        border-radius: 10px;
    }
    
    /* EXPANDERS */
    div[data-testid="stExpander"] {
        background-color: #0A0A0B !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 8px !important;
    }
    div[data-testid="stExpander"]:hover {
        border-color: rgba(212, 175, 55, 0.4) !important;
    }
    
    /* CUSTOM STATUS PILL */
    .status-pill {
        display: flex;
        align-items: center;
        background: rgba(10, 255, 10, 0.05);
        border: 1px solid rgba(10, 255, 10, 0.2);
        padding: 10px 15px;
        border-radius: 8px;
        margin-top: 15px;
    }
    .status-dot {
        height: 8px; width: 8px;
        background-color: #4CAF50;
        border-radius: 50%;
        margin-right: 10px;
        box-shadow: 0 0 8px #4CAF50;
    }
    .status-text {
        color: #E2E8F0;
        font-size: 0.85rem;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE INIT ---
if "user" not in st.session_state: st.session_state.user = None

# --- 4. DATABASE MANAGER ---
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

# --- 5. AI ENGINE (SECURE SECRETS INTEGRATION) ---
def get_gemini_response(query, tone, difficulty, institution):
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        return "❌ **System Config Error:** The server administrator has not configured the `GEMINI_API_KEY` in Streamlit Secrets."

    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        return f"❌ **System Config Error:** {str(e)}"
    
    sys_instruction = f"""
    ROLE: You are VidhiDesk, an elite legal research assistant for {institution}.
    TONE: {tone} | DEPTH: {difficulty}
    
    MANDATE:
    1. PRIORITIZE Indian Statutes: BNS (Bharatiya Nyaya Sanhita), BNSS, BSA, and Constitution.
    2. COMPARE with old acts (IPC/CrPC/Evidence Act) where relevant.
    3. CITE relevant Case Laws (Supreme Court/High Court) with year.
    4. FORMAT using Markdown: Use '### Headers', '**Bold**' for emphasis, and '>' for blockquotes.
    """

    models_to_try = ['gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-2.0-flash']
    
    last_error = ""
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=sys_instruction + "\n\nUSER QUERY: " + query
            )
            return response.text 
        except Exception as e:
            last_error = str(e)
            if "API_KEY_INVALID" in last_error or "not found" in last_error.lower():
                return f"❌ **Authentication Failed:** The server's API key is invalid or revoked."
            continue 

    return f"❌ **System Unavailable:** AI servers failed to respond. (Diagnostics: {last_error})"

# --- 6. UI LOGIC ---

def login_page():
    st.markdown("""
        <div class='vidhi-title-container'>
            <h1 class='vidhi-title'>VIDHIDESK</h1>
            <div class='temple-divider'></div>
            <div class='vidhi-subtitle'>Intelligent Legal Infrastructure</div>
        </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        with st.container(border=True):
            st.markdown("<div style='padding: 10px;'>", unsafe_allow_html=True)
            email = st.text_input("IDENTITY TOKEN (EMAIL)", placeholder="gkrosh.0712@gmail.com")
            password = st.text_input("SECURITY KEY (PASSWORD)", type="password")
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("INITIATE SESSION", use_container_width=True):
                with st.spinner("Authenticating..."):
                    time.sleep(0.5) 
                    user = db.login(email, password)
                    if user:
                        st.session_state.user = user
                        st.rerun()
                    else:
                        st.error("Authentication Failed: Invalid token or key.")

def main_app():
    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown(f"<h2 style='margin-bottom: 0;'>{st.session_state.user['name'].upper()}</h2>", unsafe_allow_html=True)
        st.markdown(f"<span style='color: #D4AF37; font-size: 0.8rem; font-weight: 500;'>{st.session_state.user['institution']}</span>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        nav = st.radio("MODULES", ["Research Core", "Knowledge Vault"], label_visibility="collapsed")
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        if "GEMINI_API_KEY" in st.secrets:
            st.markdown("""
            <div class='status-pill'>
                <div class='status-dot'></div>
                <div class='status-text'>System Online <br><span style='font-size: 0.7rem; color: #888; font-weight: 400;'>Engine: GenAI 2.5 Node</span></div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error("Server Config Error: API Key missing in Secrets.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("TERMINATE UPLINK"):
            st.session_state.user = None
            st.rerun()

    # --- RESEARCH CORE ---
    if nav == "Research Core":
        st.markdown("<h2 style='margin-bottom: 0;'>RESEARCH CORE</h2>", unsafe_allow_html=True)
        st.markdown("<div class='temple-divider' style='margin: 10px 0 30px 0; width: 80px;'></div>", unsafe_allow_html=True)

        # REPLACED UGLY SLIDERS WITH CLEAN DROPDOWNS
        with st.container(border=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                tone = st.selectbox("OUTPUT TONE", ["Casual", "Professional", "Academic"], index=2)
            with c2:
                diff = st.selectbox("ANALYSIS DEPTH", ["Summary", "Detailed", "Bare Act"], index=1)
            with c3:
                space = st.selectbox("AUTO-ARCHIVE TO", ["None", "Research", "Paper", "Study"])

        st.markdown("<br>", unsafe_allow_html=True)

        # CHAT HISTORY
        history = db.get_history(st.session_state.user['email'])
        for msg in history:
            avatar = "🧑‍⚖️" if msg['role'] == "user" else "⚖️"
            with st.chat_message(msg['role'], avatar=avatar):
                st.markdown(msg['content'])

        # CHAT INPUT
        if query := st.chat_input("Enter legal query, section, or case citation..."):
            with st.chat_message("user", avatar="🧑‍⚖️"):
                st.markdown(query)
            db.save_message(st.session_state.user['email'], "user", query)

            with st.chat_message("assistant", avatar="⚖️"):
                spinner_ph = st.empty()
                spinner_ph.markdown("""
                    <div style='display: flex; align-items: center; color: #D4AF37; padding: 10px;'>
                        <span style='margin-right: 12px; font-size: 1.2rem;'>⚖️</span> 
                        <span style='font-family: Cinzel; font-weight: 600; letter-spacing: 1px;'>ANALYZING LEGAL CORPUS...</span>
                    </div>
                """, unsafe_allow_html=True)
                
                response = get_gemini_response(
                    query, tone, diff, 
                    st.session_state.user['institution']
                )
                
                spinner_ph.empty()
                st.markdown(response)
                db.save_message(st.session_state.user['email'], "assistant", response)

                if space != "None" and "❌" not in response:
                    db.save_to_space(st.session_state.user['email'], space, query, response)
                    st.toast(f"Archived to {space}", icon="📂")

        if history:
            c1, c2 = st.columns([0.85, 0.15])
            with c2:
                if st.button("CLEAR LOGS", type="secondary"):
                    db.clear_history(st.session_state.user['email'])
                    st.rerun()

    # --- KNOWLEDGE VAULT ---
    elif nav == "Knowledge Vault":
        st.markdown("<h2 style='margin-bottom: 0;'>KNOWLEDGE VAULT</h2>", unsafe_allow_html=True)
        st.markdown("<div class='temple-divider' style='margin: 10px 0 30px 0; width: 80px;'></div>", unsafe_allow_html=True)
        
        t1, t2, t3 = st.tabs(["📚 RESEARCH", "📝 PAPERS", "🎓 STUDY"])
        for tab, cat in zip([t1, t2, t3], ["Research", "Paper", "Study"]):
            with tab:
                st.markdown("<br>", unsafe_allow_html=True)
                items = db.get_space_items(st.session_state.user['email'], cat)
                if not items:
                    st.info(f"Sector '{cat}' is empty.", icon="ℹ️")
                else:
                    for item in items:
                        with st.expander(f"📌 {item['timestamp'][:16]} | {item['query'][:60]}..."):
                            st.markdown(item['response'])
                            if st.button("DELETE RECORD", key=f"del_{item['id']}", type="secondary"):
                                db.delete_space_item(item['id'])
                                st.rerun()

if __name__ == "__main__":
    if st.session_state.user:
        main_app()
    else:
        login_page()
