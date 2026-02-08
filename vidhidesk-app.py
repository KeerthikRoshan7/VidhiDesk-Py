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

# --- 2. THEME: OBSIDIAN & LIQUID GOLD (REFINED) ---
st.markdown("""
<style>
    /* IMPORTS */
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Inter:wght@300;400;600&display=swap');

    /* ANIMATIONS */
    @keyframes fadeInUp {
        from {opacity: 0; transform: translate3d(0, 20px, 0);}
        to {opacity: 1; transform: translate3d(0, 0, 0);}
    }

    /* GLOBAL RESET */
    .stApp {
        background-color: #050505;
        background-image: radial-gradient(circle at 50% 50%, #111 0%, #000 100%);
        color: #E0E0E0;
        font-family: 'Inter', sans-serif;
    }

    /* SIDEBAR */
    section[data-testid="stSidebar"] {
        background-color: #080808;
        border-right: 1px solid #222;
    }
    
    /* TYPOGRAPHY - TITLE FIX */
    .vidhi-title {
        font-family: 'Cinzel', serif;
        font-weight: 700;
        font-size: 4rem; /* Increased size */
        text-align: center;
        margin-bottom: 0;
        /* Smooth Liquid Gold Gradient */
        background: linear-gradient(135deg, #D4AF37 0%, #F2D06B 50%, #B8860B 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        color: transparent;
        text-shadow: 0px 4px 10px rgba(0,0,0,0.5);
        letter-spacing: 4px;
        white-space: nowrap; /* PREVENTS WRAPPING/QUANTIZING */
    }
    
    h1, h2, h3 {
        color: #D4AF37 !important;
        font-family: 'Cinzel', serif;
    }
    
    p, label, span, div {
        color: #B0B0B0;
    }

    /* BUTTONS - GOLD FOIL STYLE */
    .stButton > button {
        background: linear-gradient(145deg, #B8860B, #8A6E0B);
        color: #FFFFFF;
        font-family: 'Cinzel', serif;
        font-weight: 700;
        border: 1px solid #D4AF37;
        border-radius: 4px;
        padding: 0.6rem 1.5rem;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        background: linear-gradient(145deg, #D4AF37, #AA771C);
        box-shadow: 0 0 15px rgba(212, 175, 55, 0.4);
        border-color: #FFF;
        color: #FFF;
    }

    /* SECONDARY BUTTONS */
    button[kind="secondary"] {
        background: transparent !important;
        border: 1px solid #555 !important;
        color: #888 !important;
    }
    button[kind="secondary"]:hover {
        border-color: #D4AF37 !important;
        color: #D4AF37 !important;
    }

    /* INPUTS */
    .stTextInput > div > div > input, .stChatInput textarea {
        background: #0F0F0F;
        border: 1px solid #333;
        color: #FFF;
        border-radius: 6px;
    }
    .stTextInput > div > div > input:focus, .stChatInput textarea:focus {
        border-color: #D4AF37;
        box-shadow: 0 0 8px rgba(212, 175, 55, 0.2);
    }

    /* CHAT BUBBLES */
    .stChatMessage {
        background-color: rgba(255,255,255,0.02);
        border: 1px solid #222;
        border-radius: 12px;
        animation: fadeInUp 0.4s ease-out;
    }
    .stChatMessage[data-testid="stChatMessageAvatar"] {
        background-color: #D4AF37;
        color: #000;
        border-radius: 50%;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. CONFIGURATION & CREDENTIALS ---
# PRIMARY KEY
INTERNAL_API_KEY = "AIzaSyCW3LoC7mL4nS9BmMIRjIhS4ZBFp1jUq7E"

INSTITUTIONS = sorted([
    "National Law School of India University (NLSIU), Bangalore", "NALSAR University of Law, Hyderabad",
    "National Law University, Delhi (NLUD)", "The West Bengal National University of Juridical Sciences (WBNUJS)",
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
    "Symbiosis Law School (SLS), Hyderabad", "School of Law, Christ University", "Army Institute of Law (AIL), Mohali",
    "Lloyd Law College", "KIIT School of Law", "Saveetha School of Law", "School of Law, SASTRA Deemed University",
    "School of Law, UPES", "Institute of Law, Nirma University", "Amity Law School, Noida", "Amity Law School, Delhi",
    "VIT School of Law (VITSOL)", "M.I.E.T. Engineering College (Tech Law Dept)", "Vel Tech School of Law",
    "Dr. Ambedkar Government Law College, Chennai", "ILS Law College, Pune", "DES Shri Navalmal Firodia Law College",
    "Ramaiah College of Law", "Bangalore Institute of Legal Studies", "Kle Society's Law College",
    "School of Law, Pondicherry University", "University College of Law, Osmania University",
    "School of Excellence in Law (SOEL), Chennai", "Jindal Global Law School", "ICFAI Law School"
])

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

# --- 5. AI ENGINE (FIXED) ---
def get_gemini_response(query, tone, difficulty, institution, passed_key):
    # FORCE USE of internal key if passed key is empty or invalid format
    api_key = passed_key
    if not api_key or len(api_key) < 10:
        api_key = INTERNAL_API_KEY

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

    # STABILITY FIX: Only use the standard stable models. 
    models = ['gemini-1.5-flash', 'gemini-1.5-pro']
    
    last_error = ""
    for model_name in models:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(f"{sys_instruction}\n\nUSER QUERY: {query}")
            return response.text 
        except Exception as e:
            last_error = str(e)
            continue 

    # If all fail, return clean error
    return f"❌ **System Unavailable:** Connection failed. (Details: {last_error})"

# --- 6. UI LOGIC ---

if "user" not in st.session_state: st.session_state.user = None

def login_page():
    # Centered Login with FIXED COLUMN RATIOS to prevent text breaking
    # Changed from [1, 0.6, 1] to [1, 2, 1] to give the title breathing room
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        # Using CSS class 'vidhi-title' defined above for smooth rendering
        st.markdown("<div class='vidhi-title'>VIDHIDESK</div>", unsafe_allow_html=True)
        st.markdown("<div style='height: 1px; width: 100%; background: linear-gradient(90deg, transparent, #D4AF37, transparent); margin: 10px 0 30px 0;'></div>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #888; font-size: 0.8rem; letter-spacing: 3px; text-transform: uppercase;'>Intelligent Legal Infrastructure</p>", unsafe_allow_html=True)
        
        with st.container(border=True):
            email = st.text_input("IDENTITY TOKEN (EMAIL)")
            password = st.text_input("SECURITY KEY (PASSWORD)", type="password")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("INITIATE SESSION", use_container_width=True):
                with st.spinner("Authenticating..."):
                    time.sleep(0.5) # UI Effect
                    user = db.login(email, password)
                    if user:
                        st.session_state.user = user
                        st.rerun()
                    else:
                        st.error("Authentication Failed")

def main_app():
    # --- SIDEBAR ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/924/924915.png", width=50)
        st.markdown(f"### {st.session_state.user['name'].upper()}")
        st.markdown(f"<span style='color: #D4AF37; font-size: 0.8rem;'>{st.session_state.user['institution']}</span>", unsafe_allow_html=True)
        
        st.markdown("---")
        nav = st.radio("SYSTEM MODULES", ["Research Core", "Knowledge Vault"], label_visibility="collapsed")
        
        st.markdown("---")
        # Hidden API Key Input (Auto-filled with internal key logic)
        # Only show if user explicitly needs to override
        with st.expander("System Config", expanded=False):
             user_api_key = st.text_input("Override API Key", type="password")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("TERMINATE UPLINK"):
            st.session_state.user = None
            st.rerun()

    # --- RESEARCH CORE ---
    if nav == "Research Core":
        st.markdown("# RESEARCH CORE")
        st.markdown("<div style='height: 1px; width: 60px; background: #D4AF37; margin-bottom: 30px;'></div>", unsafe_allow_html=True)

        # Control Panel
        with st.container(border=True):
            c1, c2, c3 = st.columns(3)
            tone = c1.select_slider("OUTPUT TONE", ["Casual", "Professional", "Academic"], value="Academic")
            diff = c2.select_slider("ANALYSIS DEPTH", ["Summary", "Detailed", "Bare Act"], value="Detailed")
            space = c3.selectbox("AUTO-ARCHIVE TO", ["None", "Research", "Paper", "Study"])

        # Chat Interface
        history = db.get_history(st.session_state.user['email'])
        for msg in history:
            avatar = "🧑‍⚖️" if msg['role'] == "user" else "⚖️"
            with st.chat_message(msg['role'], avatar=avatar):
                st.markdown(msg['content'])

        # Input Area
        if query := st.chat_input("Input legal query, section, or case citation..."):
            with st.chat_message("user", avatar="🧑‍⚖️"):
                st.markdown(query)
            db.save_message(st.session_state.user['email'], "user", query)

            with st.chat_message("assistant", avatar="⚖️"):
                # Custom Aesthetic Spinner
                spinner_ph = st.empty()
                spinner_ph.markdown("""
                    <div style='display: flex; align-items: center; color: #D4AF37; padding: 10px;'>
                        <span style='margin-right: 12px; font-size: 1.2rem;'>⚡</span> 
                        <span style='font-family: Cinzel; font-weight: 600; letter-spacing: 1px;'>ANALYZING LEGAL CORPUS...</span>
                    </div>
                """, unsafe_allow_html=True)
                
                # AI Call
                response = get_gemini_response(
                    query, tone, diff, 
                    st.session_state.user['institution'],
                    user_api_key if 'user_api_key' in locals() and user_api_key else ""
                )
                
                spinner_ph.empty() # Remove spinner
                
                # Fade In Response
                st.markdown(response)
                db.save_message(st.session_state.user['email'], "assistant", response)

                if space != "None" and "Connection Failed" not in response:
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
        st.markdown("# KNOWLEDGE VAULT")
        st.markdown("<div style='height: 1px; width: 60px; background: #D4AF37; margin-bottom: 30px;'></div>", unsafe_allow_html=True)
        
        t1, t2, t3 = st.tabs(["📚 RESEARCH", "📝 PAPERS", "🎓 STUDY"])
        
        cats = ["Research", "Paper", "Study"]
        for tab, cat in zip([t1, t2, t3], cats):
            with tab:
                items = db.get_space_items(st.session_state.user['email'], cat)
                if not items:
                    st.info(f"Sector '{cat}' is empty.", icon="ℹ️")
                else:
                    for item in items:
                        with st.expander(f"📌 {item['timestamp'][:16]} | {item['query'][:60]}..."):
                            st.markdown(item['response'])
                            if st.button("DELETE RECORD", key=f"del_{item['id']}"):
                                db.delete_space_item(item['id'])
                                st.rerun()

if __name__ == "__main__":
    if st.session_state.user:
        main_app()
    else:
        login_page()
