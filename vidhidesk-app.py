import streamlit as st
from google import genai
import sqlite3
import hashlib
import time
import uuid
from datetime import datetime

# --- 1. APP CONFIGURATION & SESSION INIT ---
st.set_page_config(
    page_title="VidhiDesk | Legal Intelligence",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session States
if "user" not in st.session_state: st.session_state.user = None
if "theme" not in st.session_state: st.session_state.theme = "dark"

# --- 2. DYNAMIC THEME SYSTEM (LIGHT/DARK) ---
def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"

if st.session_state.theme == "dark":
    t_bg = "#050505"
    t_container = "#0A0A0B"
    t_text = "#E2E8F0"
    t_subtext = "#94A3B8"
    t_border = "rgba(212, 175, 55, 0.2)"
    t_input_bg = "#0F0F11"
    t_chat_bg = "rgba(255, 255, 255, 0.03)"
else:
    t_bg = "#F4F6F9"
    t_container = "#FFFFFF"
    t_text = "#1E293B"
    t_subtext = "#64748B"
    t_border = "rgba(212, 175, 55, 0.4)"
    t_input_bg = "#FFFFFF"
    t_chat_bg = "rgba(0, 0, 0, 0.03)"

st.markdown(f"""
<style>
    /* IMPORTS */
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');

    /* GLOBAL RESET & DYNAMIC THEME */
    .stApp {{
        background-color: {t_bg};
        color: {t_text};
        font-family: 'Inter', sans-serif;
        transition: background-color 0.4s ease, color 0.4s ease;
    }}

    header[data-testid="stHeader"] {{ background: transparent !important; }}

    section[data-testid="stSidebar"] {{
        background-color: {t_container} !important;
        border-right: 1px solid {t_border} !important;
    }}
    
    /* TYPOGRAPHY */
    h1, h2, h3, h4, h5, h6 {{
        font-family: 'Cinzel', serif !important;
        font-weight: 600 !important;
        color: {t_text} !important;
    }}
    
    /* TITLE & DIVIDERS */
    .vidhi-title-container {{
        width: 100%; text-align: center; padding-top: 3vh; padding-bottom: 2rem;
    }}
    .vidhi-title {{
        font-size: clamp(2.5rem, 6vw, 4.5rem); 
        margin: 0 auto;
        background: linear-gradient(135deg, #BF953F 0%, #FCF6BA 40%, #B38728 60%, #AA771C 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        color: transparent;
        letter-spacing: 0.15em; 
        white-space: nowrap !important;
        font-weight: 700 !important;
        text-shadow: 0px 4px 20px rgba(212, 175, 55, 0.2);
    }}
    .temple-divider {{
        height: 1px; width: 200px;
        background: linear-gradient(90deg, transparent, #D4AF37, transparent);
        margin: 15px auto;
    }}
    .vidhi-subtitle {{
        color: {t_subtext}; font-size: 0.8rem; letter-spacing: 4px; text-transform: uppercase;
    }}

    p, label, span, div {{ color: {t_text}; }}

    /* ========================================================
       BUG FIXES: POINTERS & ANNOYING TOOLTIPS 
       ======================================================== */
    
    /* Hide 'Press Enter to Apply' completely */
    div[data-testid="InputInstructions"] {{ display: none !important; }}
    
    /* Fix Dropdown Cursor - Make it a pointer, hide text cursor (caret) */
    div[data-baseweb="select"] {{ cursor: pointer !important; }}
    div[data-baseweb="select"] * {{ cursor: pointer !important; }}
    div[data-baseweb="select"] input {{ caret-color: transparent !important; cursor: pointer !important; }}

    /* SELECTBOX (DROPDOWNS) */
    div[data-baseweb="select"] > div {{
        background-color: {t_input_bg} !important;
        border: 1px solid {t_border} !important;
        color: {t_text} !important;
        border-radius: 6px !important;
    }}
    div[data-baseweb="select"] > div:hover {{ border-color: #D4AF37 !important; }}
    div[data-baseweb="popover"] {{ background-color: {t_container} !important; border: 1px solid #D4AF37 !important; }}
    div[data-baseweb="popover"] li {{ color: {t_text} !important; }}
    div[data-baseweb="popover"] li:hover {{ background-color: rgba(212, 175, 55, 0.2) !important; color: #D4AF37 !important; }}

    /* INPUTS & CHAT BOX */
    .stTextInput > div > div > input, .stChatInput textarea {{
        background-color: {t_input_bg} !important;
        border: 1px solid {t_border} !important;
        color: {t_text} !important;
        border-radius: 6px !important;
        padding: 10px !important;
    }}
    .stTextInput > div > div > input:focus, .stChatInput textarea:focus {{
        border-color: #D4AF37 !important; box-shadow: 0 0 10px rgba(212, 175, 55, 0.2) !important;
    }}

    /* BUTTONS - ELEGANT GOLD */
    .stButton > button {{
        background: linear-gradient(135deg, #1A1500 0%, #2A2205 100%) !important;
        color: #D4AF37 !important;
        font-family: 'Cinzel', serif !important;
        font-weight: 600 !important;
        border: 1px solid rgba(212, 175, 55, 0.5) !important;
        border-radius: 4px !important;
        text-transform: uppercase; letter-spacing: 1.5px; width: 100%;
        transition: all 0.3s ease !important;
    }}
    .stButton > button:hover {{
        background: linear-gradient(135deg, #2A2205 0%, #3D320A 100%) !important;
        border-color: #D4AF37 !important; color: #FFF !important;
        box-shadow: 0 4px 15px rgba(212, 175, 55, 0.2) !important;
    }}
    button[kind="secondary"] {{
        background: transparent !important; border: 1px solid {t_subtext} !important; color: {t_subtext} !important;
    }}
    button[kind="secondary"]:hover {{ border-color: #D4AF37 !important; color: #D4AF37 !important; }}

    /* CHAT BUBBLES */
    .stChatMessage {{
        background-color: {t_chat_bg} !important;
        border: 1px solid {t_border} !important;
        border-radius: 12px !important; padding: 1.2rem !important; margin-bottom: 1rem !important;
    }}
    .stChatMessage[data-testid="stChatMessageAvatar"] {{
        background-color: #111 !important; border: 1px solid #D4AF37 !important; color: #D4AF37 !important;
    }}
    
    /* CARDS & TABS */
    div[data-testid="stContainer"] > div > div > div {{ background-color: {t_container}; border-radius: 8px; }}
    div[data-testid="stExpander"] {{ background-color: {t_container} !important; border: 1px solid {t_border} !important; border-radius: 8px !important; }}
    
    /* TABS STYLING */
    button[data-baseweb="tab"] {{ color: {t_subtext} !important; font-weight: 600 !important; }}
    button[aria-selected="true"] {{ color: #D4AF37 !important; border-bottom: 2px solid #D4AF37 !important; }}
</style>
""", unsafe_allow_html=True)

# --- 3. HARDCODED LISTS ---
INSTITUTIONS = sorted([
    "National Law School of India University (NLSIU), Bangalore", "NALSAR University of Law, Hyderabad",
    "National Law University, Delhi (NLUD)", "The West Bengal National University of Juridical Sciences (WBNUJS)",
    "National Law University, Jodhpur (NLUJ)", "Hidayatullah National Law University (HNLU), Raipur",
    "Gujarat National Law University (GNLU), Gandhinagar", "Dr. Ram Manohar Lohiya National Law University (RMLNLU)",
    "Rajiv Gandhi National University of Law (RGNUL), Patiala", "Chanakya National Law University (CNLU), Patna",
    "National University of Advanced Legal Studies (NUALS), Kochi", "National Law University Odisha (NLUO)",
    "Tamil Nadu National Law University (TNNLU)", "Maharashtra National Law University (MNLU), Mumbai",
    "Faculty of Law, University of Delhi (DU)", "Government Law College (GLC), Mumbai", 
    "Symbiosis Law School (SLS), Pune", "School of Law, Christ University", "Jindal Global Law School", "Other"
]) 

# --- 4. DATABASE MANAGER (WITH TOKEN & REGISTER SUPPORT) ---
class DBHandler:
    def __init__(self, db_name="vidhidesk_users.db"):
        self.db_name = db_name
        self.verify_db()

    def get_connection(self):
        return sqlite3.connect(self.db_name, check_same_thread=False)

    def verify_db(self):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, password TEXT, name TEXT, institution TEXT, year TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS chats (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, role TEXT, content TEXT, timestamp DATETIME)''')
        c.execute('''CREATE TABLE IF NOT EXISTS spaces (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, category TEXT, query TEXT, response TEXT, timestamp DATETIME)''')
        # Add auth_token column if not exists for 'Remember Me'
        try:
            c.execute('''ALTER TABLE users ADD COLUMN auth_token TEXT''')
        except sqlite3.OperationalError:
            pass
        conn.commit()
        conn.close()

    def register_user(self, email, password, name, inst, year):
        conn = self.get_connection()
        try:
            hashed_pw = hashlib.sha256(password.encode()).hexdigest()
            conn.execute("INSERT INTO users (email, password, name, institution, year, auth_token) VALUES (?, ?, ?, ?, ?, ?)", 
                         (email, hashed_pw, name, inst, year, ""))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def login(self, email, password, remember_me=False):
        conn = self.get_connection()
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        cur = conn.execute("SELECT name, institution, year FROM users WHERE email=? AND password=?", (email, hashed_pw))
        user = cur.fetchone()
        
        if user:
            token = ""
            if remember_me:
                token = str(uuid.uuid4())
                conn.execute("UPDATE users SET auth_token=? WHERE email=?", (token, email))
                conn.commit()
            conn.close()
            return {"email": email, "name": user[0], "institution": user[1], "year": user[2], "token": token}
        
        conn.close()
        return None

    def login_with_token(self, token):
        conn = self.get_connection()
        cur = conn.execute("SELECT email, name, institution, year FROM users WHERE auth_token=?", (token,))
        user = cur.fetchone()
        conn.close()
        if user and token != "":
            return {"email": user[0], "name": user[1], "institution": user[2], "year": user[3], "token": token}
        return None

    def logout(self, email):
        conn = self.get_connection()
        conn.execute("UPDATE users SET auth_token='' WHERE email=?", (email,))
        conn.commit()
        conn.close()

    def save_message(self, email, role, content):
        conn = self.get_connection()
        conn.execute("INSERT INTO chats (email, role, content, timestamp) VALUES (?, ?, ?, ?)", (email, role, content, datetime.now()))
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
        conn.execute("INSERT INTO spaces (email, category, query, response, timestamp) VALUES (?, ?, ?, ?, ?)", (email, category, query, response, datetime.now()))
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

# Auto-Login via "Remember Me" Token (Query Params)
if not st.session_state.user:
    saved_token = st.query_params.get("auth_token", None)
    if saved_token:
        auto_user = db.login_with_token(saved_token)
        if auto_user:
            st.session_state.user = auto_user

# --- 5. AI ENGINE (PROGRESSIVE STREAMING) ---
def get_gemini_stream(query, tone, difficulty, institution):
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        yield "❌ **System Config Error:** The server administrator has not configured the `GEMINI_API_KEY` in Streamlit Secrets."
        return

    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        yield f"❌ **System Config Error:** {str(e)}"
        return
    
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
    
    for model_name in models_to_try:
        try:
            # Using generate_content_stream for progressive typing effect
            response_stream = client.models.generate_content_stream(
                model=model_name,
                contents=sys_instruction + "\n\nUSER QUERY: " + query
            )
            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text
            return # Exit generator successfully
        except Exception as e:
            if "API_KEY_INVALID" in str(e) or "not found" in str(e).lower():
                yield "❌ **Authentication Failed:** The server's API key is invalid or revoked."
                return
            continue 

    yield "❌ **System Unavailable:** AI servers failed to respond."

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
            tab_login, tab_reg, tab_guest = st.tabs(["LOGIN", "REGISTER", "GUEST"])
            
            # --- LOGIN TAB ---
            with tab_login:
                st.markdown("<br>", unsafe_allow_html=True)
                email = st.text_input("IDENTITY TOKEN (EMAIL)", key="log_email")
                password = st.text_input("SECURITY KEY (PASSWORD)", type="password", key="log_pwd")
                remember_me = st.checkbox("Keep me signed in (Remember Me)")
                
                if st.button("INITIATE SESSION", use_container_width=True):
                    with st.spinner("Authenticating..."):
                        time.sleep(0.5) 
                        user = db.login(email, password, remember_me)
                        if user:
                            st.session_state.user = user
                            if remember_me and user["token"]:
                                st.query_params["auth_token"] = user["token"]
                            st.rerun()
                        else:
                            st.error("Authentication Failed: Invalid token or key.")
                            
            # --- REGISTER TAB ---
            with tab_reg:
                st.markdown("<br>", unsafe_allow_html=True)
                r_name = st.text_input("FULL NAME")
                r_email = st.text_input("EMAIL ADDRESS")
                r_pwd = st.text_input("CREATE PASSWORD", type="password")
                r_inst = st.selectbox("INSTITUTION", INSTITUTIONS)
                r_year = st.selectbox("YEAR / STATUS", ["1st Year", "2nd Year", "3rd Year", "4th Year", "5th Year", "Graduate", "Faculty", "Other"])
                
                if st.button("REGISTER ACCOUNT", use_container_width=True):
                    if r_name and r_email and r_pwd:
                        success = db.register_user(r_email, r_pwd, r_name, r_inst, r_year)
                        if success:
                            st.success("Registration Successful! Please navigate to Login.")
                        else:
                            st.error("Error: Email already registered in the system.")
                    else:
                        st.warning("Please fill out all required fields.")

            # --- GUEST TAB ---
            with tab_guest:
                st.markdown("<br><p style='text-align: center;'>Temporary access mode. Search history and Vault data will be tied to a temporary session.</p><br>", unsafe_allow_html=True)
                if st.button("CONTINUE AS GUEST", type="secondary", use_container_width=True):
                    guest_email = f"guest_{int(time.time())}@vidhidesk.local"
                    st.session_state.user = {
                        "email": guest_email,
                        "name": "Guest User",
                        "institution": "Independent Researcher",
                        "year": "N/A"
                    }
                    st.rerun()

def main_app():
    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown(f"<h3 style='margin-bottom: 0; color: {t_text} !important;'>{st.session_state.user['name'].upper()}</h3>", unsafe_allow_html=True)
        st.markdown(f"<span style='color: #D4AF37; font-size: 0.8rem; font-weight: 500;'>{st.session_state.user['institution']}</span>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        nav = st.radio("MODULES", ["Research Core", "Knowledge Vault"], label_visibility="collapsed")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Theme Toggle
        theme_icon = "☀️ Light Mode" if st.session_state.theme == "dark" else "🌙 Dark Mode"
        if st.button(theme_icon, key="theme_toggle", type="secondary"):
            toggle_theme()
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        
        if "GEMINI_API_KEY" in st.secrets:
            st.markdown(f"""
            <div style='border: 1px solid {t_border}; padding: 12px; border-radius: 6px; background: transparent; margin-top:10px;'>
                <div style='display:flex; align-items:center; margin-bottom:5px;'>
                    <span style='color: #4CAF50; font-size: 1.2rem; margin-right: 8px;'>●</span> 
                    <span style='color: #D4AF37; font-weight:600;'>System Online</span>
                </div>
                <div style='font-size: 0.7rem; color: {t_subtext};'>Engine: GenAI 2.5 Streaming</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error("Server Config Error: API Key missing in Secrets.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("LOGOUT / TERMINATE UPLINK"):
            db.logout(st.session_state.user["email"])
            st.session_state.user = None
            if "auth_token" in st.query_params:
                del st.query_params["auth_token"]
            st.rerun()

    # --- RESEARCH CORE ---
    if nav == "Research Core":
        st.markdown(f"<h2 style='margin-bottom: 0; color: {t_text} !important;'>RESEARCH CORE</h2>", unsafe_allow_html=True)
        st.markdown("<div class='temple-divider' style='margin: 10px 0 30px 0; width: 80px; margin-left: 0;'></div>", unsafe_allow_html=True)

        with st.container(border=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                tone = st.selectbox("OUTPUT TONE", ["Casual", "Professional", "Academic"], index=2)
            with c2:
                diff = st.selectbox("ANALYSIS DEPTH", ["Summary", "Detailed", "Bare Act"], index=1)
            with c3:
                space = st.selectbox("AUTO-ARCHIVE TO", ["None", "Research", "Paper", "Study"])

        st.markdown("<br>", unsafe_allow_html=True)

        history = db.get_history(st.session_state.user['email'])
        for msg in history:
            avatar = "🧑‍⚖️" if msg['role'] == "user" else "⚖️"
            with st.chat_message(msg['role'], avatar=avatar):
                st.markdown(msg['content'])

        if query := st.chat_input("Enter legal query, section, or case citation..."):
            with st.chat_message("user", avatar="🧑‍⚖️"):
                st.markdown(query)
            db.save_message(st.session_state.user['email'], "user", query)

            with st.chat_message("assistant", avatar="⚖️"):
                # PROGRESSIVE STREAMING GENERATION
                stream = get_gemini_stream(
                    query, tone, diff, 
                    st.session_state.user['institution']
                )
                full_response = st.write_stream(stream)
                
                db.save_message(st.session_state.user['email'], "assistant", full_response)

                if space != "None" and "❌" not in full_response:
                    db.save_to_space(st.session_state.user['email'], space, query, full_response)
                    st.toast(f"Archived to {space}", icon="📂")

        if history:
            c1, c2 = st.columns([0.85, 0.15])
            with c2:
                if st.button("CLEAR LOGS", type="secondary"):
                    db.clear_history(st.session_state.user['email'])
                    st.rerun()

    # --- KNOWLEDGE VAULT ---
    elif nav == "Knowledge Vault":
        st.markdown(f"<h2 style='margin-bottom: 0; color: {t_text} !important;'>KNOWLEDGE VAULT</h2>", unsafe_allow_html=True)
        st.markdown("<div class='temple-divider' style='margin: 10px 0 30px 0; width: 80px; margin-left: 0;'></div>", unsafe_allow_html=True)
        
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
