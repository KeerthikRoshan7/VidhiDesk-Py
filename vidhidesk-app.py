import streamlit as st
from google import genai
from google.genai import types
import sqlite3
import hashlib
import time
import uuid
from datetime import datetime
import PyPDF2
from docx import Document
import io

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
    t_chat_bg = "rgba(255, 255, 255, 0.02)"
else:
    t_bg = "#F4F6F9"
    t_container = "#FFFFFF"
    t_text = "#1E293B"
    t_subtext = "#64748B"
    t_border = "rgba(212, 175, 55, 0.4)"
    t_input_bg = "#FFFFFF"
    t_chat_bg = "rgba(0, 0, 0, 0.02)"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');

    .stApp {{
        background-color: {t_bg}; color: {t_text}; font-family: 'Inter', sans-serif;
        transition: background-color 0.4s ease, color 0.4s ease;
    }}
    header[data-testid="stHeader"] {{ background: transparent !important; }}
    section[data-testid="stSidebar"] {{
        background-color: {t_container} !important; border-right: 1px solid {t_border} !important;
    }}
    h1, h2, h3, h4, h5, h6 {{ font-family: 'Cinzel', serif !important; font-weight: 600 !important; color: {t_text} !important; }}
    
    .block-container {{ padding-top: 2rem !important; padding-bottom: 6rem !important; }}

    div[data-testid="stVerticalBlock"]:has(#sticky-header-marker):not(:has(div[data-testid="stVerticalBlock"]:has(#sticky-header-marker))) {{
        position: sticky !important; top: 2rem !important; z-index: 999 !important;
        background-color: {t_bg} !important; padding: 5px 0px 15px 0px !important;
        border-bottom: 1px solid {t_border} !important; margin-bottom: 20px !important;
    }}

    .vidhi-title-container {{ width: 100%; text-align: center; padding-top: 3vh; padding-bottom: 2rem; }}
    .vidhi-title {{
        font-size: clamp(2.5rem, 6vw, 4.5rem); margin: 0 auto;
        background: linear-gradient(135deg, #BF953F 0%, #FCF6BA 40%, #B38728 60%, #AA771C 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; color: transparent;
        letter-spacing: 0.15em; white-space: nowrap !important; font-weight: 700 !important;
        text-shadow: 0px 4px 20px rgba(212, 175, 55, 0.2);
    }}
    .temple-divider {{ height: 1px; width: 200px; background: linear-gradient(90deg, transparent, #D4AF37, transparent); margin: 15px auto; }}
    .vidhi-subtitle {{ color: {t_subtext}; font-size: 0.8rem; letter-spacing: 4px; text-transform: uppercase; }}
    p, label, span, div {{ color: {t_text}; }}

    ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb {{ background: rgba(212, 175, 55, 0.5); border-radius: 4px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: rgba(212, 175, 55, 0.8); }}

    div[data-testid="InputInstructions"] {{ display: none !important; }}
    div[data-baseweb="select"] {{ cursor: pointer !important; }}
    div[data-baseweb="select"] * {{ cursor: pointer !important; }}
    div[data-baseweb="select"] input {{ caret-color: transparent !important; cursor: pointer !important; }}

    div[data-baseweb="select"] > div {{
        background-color: {t_input_bg} !important; border: 1px solid {t_border} !important;
        color: {t_text} !important; border-radius: 6px !important;
    }}
    div[data-baseweb="select"] > div:hover {{ border-color: #D4AF37 !important; }}
    div[data-baseweb="popover"] {{ background-color: {t_container} !important; border: 1px solid #D4AF37 !important; }}
    div[data-baseweb="popover"] li {{ color: {t_text} !important; }}
    div[data-baseweb="popover"] li:hover {{ background-color: rgba(212, 175, 55, 0.2) !important; color: #D4AF37 !important; }}
    
    div[data-testid="stPopover"] > button {{ min-height: 48px !important; border-radius: 8px !important; }}

    .stTextInput > div > div > input, .stChatInput textarea, .stTextArea textarea {{
        background-color: {t_input_bg} !important; border: 1px solid {t_border} !important;
        color: {t_text} !important; border-radius: 6px !important; padding: 10px !important;
    }}
    .stTextInput > div > div > input:focus, .stChatInput textarea:focus, .stTextArea textarea:focus {{
        border-color: #D4AF37 !important; box-shadow: 0 0 10px rgba(212, 175, 55, 0.2) !important;
    }}

    .stButton > button {{
        background: linear-gradient(135deg, #1A1500 0%, #2A2205 100%) !important;
        color: #D4AF37 !important; font-family: 'Cinzel', serif !important; font-weight: 600 !important;
        border: 1px solid rgba(212, 175, 55, 0.5) !important; border-radius: 4px !important;
        text-transform: uppercase; letter-spacing: 1.5px; width: 100%; transition: all 0.3s ease !important;
    }}
    .stButton > button:hover {{
        background: linear-gradient(135deg, #2A2205 0%, #3D320A 100%) !important;
        border-color: #D4AF37 !important; color: #FFF !important; box-shadow: 0 4px 15px rgba(212, 175, 55, 0.2) !important;
    }}
    button[kind="secondary"] {{ background: transparent !important; border: 1px solid {t_subtext} !important; color: {t_subtext} !important; }}
    button[kind="secondary"]:hover {{ border-color: #D4AF37 !important; color: #D4AF37 !important; }}

    .stChatMessage {{
        background-color: {t_chat_bg} !important; border: 1px solid {t_border} !important;
        border-radius: 12px !important; padding: 1.2rem !important; margin-bottom: 1rem !important;
    }}
    .stChatMessage[data-testid="stChatMessageAvatar"] {{ background-color: #111 !important; border: 1px solid #D4AF37 !important; color: #D4AF37 !important; }}
    
    div[data-testid="stContainer"] > div > div > div {{ background-color: {t_container}; border-radius: 8px; }}
    div[data-testid="stExpander"] {{ background-color: {t_container} !important; border: 1px solid {t_border} !important; border-radius: 8px !important; margin-bottom: 0px !important; }}
    
    button[data-baseweb="tab"] {{ color: {t_subtext} !important; font-weight: 600 !important; }}
    button[aria-selected="true"] {{ color: #D4AF37 !important; border-bottom: 2px solid #D4AF37 !important; }}
</style>
""", unsafe_allow_html=True)

# --- 3. HARDCODED LISTS ---
INSTITUTIONS = sorted([
    "National Law School of India University (NLSIU), Bangalore", "NALSAR University of Law, Hyderabad",
    "National Law University, Delhi (NLUD)", "The West Bengal National University of Juridical Sciences (WBNUJS)",
    "National Law University, Jodhpur (NLUJ)", "Hidayatullah National Law University (HNLU), Raipur",
    "Tamil Nadu National Law University (TNNLU)", "Maharashtra National Law University (MNLU), Mumbai",
    "Faculty of Law, University of Delhi (DU)", "Government Law College (GLC), Mumbai", 
    "Symbiosis Law School (SLS), Pune", "School of Law, Christ University", "Jindal Global Law School", "Other"
]) 

# --- 4. DATABASE MANAGER ---
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

if not st.session_state.user:
    saved_token = st.query_params.get("auth_token", None)
    if saved_token:
        auto_user = db.login_with_token(saved_token)
        if auto_user:
            st.session_state.user = auto_user

# --- 5. FILE EXTRACTOR & WORD EXPORT ---
def extract_pdf_text(uploaded_file):
    try:
        reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Error reading PDF: {e}"

def generate_word_document(query, response, title="VidhiDesk Legal Document"):
    doc = Document()
    doc.add_heading(title, 0)
    
    if query:
        doc.add_heading('Context / Facts:', level=1)
        doc.add_paragraph(query)
    
    doc.add_heading('Legal Analysis:', level=1)
    clean_response = response.replace("**", "").replace("*", "")
    doc.add_paragraph(clean_response)
    
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- 6. AI ENGINE ---
def get_gemini_stream(query, tone, difficulty, institution, pdf_text=None, audio_bytes=None, enable_search=False, strict_citation=False):
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        yield "❌ **System Config Error:** API Key missing in Streamlit Secrets."
        return

    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        yield f"❌ **System Config Error:** {str(e)}"
        return
    
    sys_instruction = f"""
    ROLE: You are VidhiDesk, an elite legal research assistant for {institution}.
    TONE: {tone} | DEPTH: {difficulty}
    MANDATE: Prioritize Indian Statutes (BNS, BNSS, BSA, Constitution). Cite relevant Case Laws. Use Markdown.
    """
    
    if strict_citation:
        sys_instruction += "\nCRITICAL RULE (STRICT CITATION MODE): You MUST ONLY cite real, verifiable Indian case laws. Provide the exact year, volume, and court. Under NO circumstances should you invent or hallucinate a case. If you cannot find a verifiable precedent, explicitly state 'No verifiable case law found for this specific query'."

    contents = [sys_instruction]
    
    if pdf_text:
        contents.append(f"\n[DOCUMENT CONTEXT UPLOADED BY USER]:\n{pdf_text[:15000]}\n\n(Base your answer heavily on the document above if relevant).")
        
    if audio_bytes:
        contents.append({"mime_type": "audio/wav", "data": audio_bytes})
        
    if query:
        contents.append(f"\nUSER QUERY: {query}")

    config = types.GenerateContentConfig(temperature=0.1 if strict_citation else 0.3)
    if enable_search:
        config.tools = [{"google_search": {}}]

    models_to_try = ['gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-2.0-flash']
    
    for model_name in models_to_try:
        try:
            response_stream = client.models.generate_content_stream(
                model=model_name,
                contents=contents,
                config=config
            )
            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text
            return 
        except Exception as e:
            if "API_KEY_INVALID" in str(e) or "not found" in str(e).lower():
                yield "❌ **Authentication Failed:** API key invalid or revoked."
                return
            continue 

    yield "❌ **System Unavailable:** AI servers failed to respond."

def get_drafting_stream(doc_type, facts, institution, pdf_text=None):
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        client = genai.Client(api_key=api_key)
    except Exception:
        yield "❌ **System Config Error.**"
        return
        
    sys_instruction = f"""
    ROLE: You are a Senior Legal Draftsman at {institution} in India.
    TASK: Draft a professional, court-ready '{doc_type}'.
    MANDATE: 
    - Use strict, formal Indian legal terminology.
    - Format properly using clear headings and numbered paragraphs.
    - Use placeholders like [CLIENT NAME], [DATE], [AMOUNT] for missing facts.
    - Base the entire draft strictly on the facts and documents provided below.
    """
    
    contents = [sys_instruction]
    if pdf_text:
        contents.append(f"\n[REFERENCE DOCUMENT UPLOADED]:\n{pdf_text[:15000]}\n\n(Use this document for context, references, or template structure).")
    if facts:
        contents.append(f"\n[CLIENT FACTS]:\n{facts}")
        
    try:
        response_stream = client.models.generate_content_stream(model='gemini-2.5-flash', contents=contents)
        for chunk in response_stream:
            if chunk.text: yield chunk.text
    except Exception as e:
        yield f"❌ **Drafting Engine Error:** {str(e)}"

def get_translation_stream(text, target_lang, institution, pdf_text=None):
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        client = genai.Client(api_key=api_key)
    except Exception:
        yield "❌ **System Config Error.**"
        return
        
    sys_instruction = f"""
    ROLE: You are an expert Legal Translator at {institution}.
    TASK: Translate the provided legal document/text accurately into highly formal {target_lang}.
    MANDATE: 
    - Preserve all legal meanings, liabilities, and nuances perfectly.
    - Maintain the original formatting and paragraph structure.
    - If there are Latin legal maxims, keep them in Latin but add the translated meaning in brackets.
    """
    
    contents = [sys_instruction]
    if pdf_text:
        contents.append(f"\n[DOCUMENT TO TRANSLATE]:\n{pdf_text[:15000]}")
    if text:
        contents.append(f"\n[ADDITIONAL TEXT TO TRANSLATE]:\n{text}")
        
    try:
        response_stream = client.models.generate_content_stream(model='gemini-2.5-flash', contents=contents)
        for chunk in response_stream:
            if chunk.text: yield chunk.text
    except Exception as e:
        yield f"❌ **Translation Engine Error:** {str(e)}"


# --- 7. UI LOGIC ---
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

            with tab_guest:
                st.markdown("<br><p style='text-align: center;'>Temporary access mode. Data will be tied to a temporary session.</p><br>", unsafe_allow_html=True)
                if st.button("CONTINUE AS GUEST", type="secondary", use_container_width=True):
                    guest_email = f"guest_{int(time.time())}@vidhidesk.local"
                    st.session_state.user = {
                        "email": guest_email, "name": "Guest User", "institution": "Independent Researcher", "year": "N/A"
                    }
                    st.rerun()

def main_app():
    with st.sidebar:
        st.markdown(f"<h3 style='margin-bottom: 0; color: {t_text} !important;'>{st.session_state.user['name'].upper()}</h3>", unsafe_allow_html=True)
        st.markdown(f"<span style='color: #D4AF37; font-size: 0.8rem; font-weight: 500;'>{st.session_state.user['institution']}</span>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        nav = st.radio("MODULES", ["Research Core", "Drafting Studio", "Translation Desk", "Knowledge Vault"], label_visibility="collapsed")
        
        st.markdown("<br>", unsafe_allow_html=True)
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
            st.error("Config Error: API Key missing.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("LOGOUT / TERMINATE UPLINK"):
            db.logout(st.session_state.user["email"])
            st.session_state.user = None
            if "auth_token" in st.query_params:
                del st.query_params["auth_token"]
            st.rerun()

    # --- RESEARCH CORE ---
    if nav == "Research Core":
        sticky_header = st.container()
        with sticky_header:
            st.markdown("<span id='sticky-header-marker'></span>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='margin-bottom: 0; color: {t_text} !important;'>RESEARCH CORE</h2>", unsafe_allow_html=True)
            st.markdown("<div class='temple-divider' style='margin: 10px 0 20px 0; width: 80px; margin-left: 0;'></div>", unsafe_allow_html=True)

            param_col, mic_col = st.columns([0.85, 0.15], vertical_alignment="center")
            
            with param_col:
                with st.expander("⚙️ Advanced Research Parameters & Grounding", expanded=False):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        tone = st.selectbox("OUTPUT TONE", ["Casual", "Professional", "Academic"], index=2)
                    with c2:
                        diff = st.selectbox("ANALYSIS DEPTH", ["Summary", "Detailed", "Bare Act"], index=1)
                    with c3:
                        space = st.selectbox("AUTO-ARCHIVE TO", ["None", "Research", "Paper", "Study"])
                        
                    st.markdown("---")
                    sc1, sc2, sc3 = st.columns([1, 1, 1])
                    with sc1:
                        st.markdown("<br>", unsafe_allow_html=True)
                        enable_search = st.toggle("🌐 Web Grounding (Live Search)")
                    with sc2:
                        st.markdown("<br>", unsafe_allow_html=True)
                        strict_citation = st.toggle("🛡️ Strict Citation Mode")
                    with sc3:
                        uploaded_pdf = st.file_uploader("📄 Upload PDF Context", type=["pdf"], key="res_pdf")

            with mic_col:
                with st.popover("🎙️ VOICE", use_container_width=True):
                    st.markdown("<div style='text-align:center; font-size:0.9rem; color:#888; margin-bottom:10px;'>Speak your legal query</div>", unsafe_allow_html=True)
                    audio_data = st.audio_input("Record", label_visibility="collapsed")
                    submit_audio = st.button("SEND AUDIO", use_container_width=True, type="secondary")

        history = db.get_history(st.session_state.user['email'])
        for msg in history:
            avatar = "🧑‍⚖️" if msg['role'] == "user" else "⚖️"
            with st.chat_message(msg['role'], avatar=avatar):
                st.markdown(msg['content'])

        query = st.chat_input("Enter legal query, section, or case citation...")
        is_audio_submission = audio_data is not None and submit_audio

        if query or is_audio_submission:
            with st.chat_message("user", avatar="🧑‍⚖️"):
                if query: st.markdown(query)
                if is_audio_submission:
                    st.audio(audio_data)
                    if not query: query = "Please analyze this audio recording."
            
            db.save_message(st.session_state.user['email'], "user", query)

            with st.chat_message("assistant", avatar="⚖️"):
                pdf_extracted_text = None
                if uploaded_pdf:
                    with st.spinner("Reading Document..."):
                        pdf_extracted_text = extract_pdf_text(uploaded_pdf)
                
                audio_bytes = audio_data.getvalue() if is_audio_submission else None

                stream = get_gemini_stream(
                    query, tone, diff, st.session_state.user['institution'],
                    pdf_text=pdf_extracted_text, audio_bytes=audio_bytes,
                    enable_search=enable_search, strict_citation=strict_citation
                )
                
                full_response = st.write_stream(stream)
                db.save_message(st.session_state.user['email'], "assistant", full_response)

                if space != "None" and "❌" not in full_response:
                    db.save_to_space(st.session_state.user['email'], space, query, full_response)
                    st.toast(f"Archived to {space}", icon="📂")
            st.rerun()

        if history:
            c1, c2 = st.columns([0.85, 0.15])
            with c2:
                if st.button("CLEAR LOGS", type="secondary"):
                    db.clear_history(st.session_state.user['email'])
                    st.rerun()

    # --- DRAFTING STUDIO ---
    elif nav == "Drafting Studio":
        st.markdown(f"<h2 style='margin-bottom: 0; color: {t_text} !important;'>DRAFTING STUDIO</h2>", unsafe_allow_html=True)
        st.markdown("<div class='temple-divider' style='margin: 10px 0 30px 0; width: 80px; margin-left: 0;'></div>", unsafe_allow_html=True)
        
        st.markdown("Automated generation of court-ready legal documents based on standard Indian formats.", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown("#### Draft Configuration")
            doc_type = st.selectbox("Document Type", [
                "Legal Notice (General)", "Legal Notice (Sec 138 NI Act - Cheque Bounce)", 
                "Non-Disclosure Agreement (NDA)", "Bail Application (Under BNSS)", 
                "Lease / Rent Agreement", "Writ Petition (Draft Format)"
            ])
            
            facts = st.text_area("Client Facts & Details (Optional if PDF provided)", height=150, placeholder="E.g., Client name is Rahul. Tenant hasn't paid rent of Rs 50,000...")
            
            uploaded_draft_pdf = st.file_uploader("📄 Upload Reference Document / Old Contract (PDF)", type=["pdf"], key="draft_pdf")
            
            if st.button("GENERATE DRAFT", use_container_width=True):
                if not facts and not uploaded_draft_pdf:
                    st.warning("Please provide either text facts or upload a reference PDF to generate a draft.")
                else:
                    st.markdown("---")
                    st.markdown(f"### Generated Draft: {doc_type}")
                    
                    pdf_extracted_text = None
                    if uploaded_draft_pdf:
                        with st.spinner("Extracting Reference Document..."):
                            pdf_extracted_text = extract_pdf_text(uploaded_draft_pdf)
                            
                    stream = get_drafting_stream(doc_type, facts, st.session_state.user['institution'], pdf_text=pdf_extracted_text)
                    final_draft = st.write_stream(stream)
                    
                    if "❌" not in final_draft:
                        context_note = f"Facts provided:\n{facts}\n\n[Reference PDF was uploaded and used in this draft]" if uploaded_draft_pdf else f"Facts provided:\n{facts}"
                        doc_bytes = generate_word_document(context_note, final_draft, title=f"Draft: {doc_type}")
                        st.download_button(
                            label="📄 DOWNLOAD DRAFT AS WORD",
                            data=doc_bytes,
                            file_name=f"Draft_{doc_type.replace(' ', '_')}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            type="primary"
                        )

    # --- TRANSLATION DESK ---
    elif nav == "Translation Desk":
        st.markdown(f"<h2 style='margin-bottom: 0; color: {t_text} !important;'>TRANSLATION DESK</h2>", unsafe_allow_html=True)
        st.markdown("<div class='temple-divider' style='margin: 10px 0 30px 0; width: 80px; margin-left: 0;'></div>", unsafe_allow_html=True)
        
        st.markdown("High-fidelity legal translation preserving complex terminology and legal nuances.", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        with st.container(border=True):
            target_lang = st.selectbox("Translate To", ["Hindi", "Tamil", "Marathi", "Bengali", "Telugu", "Gujarati", "Malayalam", "English"])
            
            source_text = st.text_area("Source Text (Optional if PDF provided)", height=150, placeholder="Paste legal document text here...")
            
            uploaded_trans_pdf = st.file_uploader("📄 Upload Document to Translate (PDF)", type=["pdf"], key="trans_pdf")
            
            if st.button("TRANSLATE", use_container_width=True):
                if not source_text and not uploaded_trans_pdf:
                    st.warning("Please paste text or upload a PDF to translate.")
                else:
                    st.markdown("---")
                    st.markdown(f"### {target_lang} Translation")
                    
                    pdf_extracted_text = None
                    if uploaded_trans_pdf:
                        with st.spinner("Extracting PDF Text for Translation..."):
                            pdf_extracted_text = extract_pdf_text(uploaded_trans_pdf)
                            
                    stream = get_translation_stream(source_text, target_lang, st.session_state.user['institution'], pdf_text=pdf_extracted_text)
                    final_translation = st.write_stream(stream)
                    
                    if "❌" not in final_translation:
                        context_note = f"Source Text:\n{source_text}\n\n[PDF Document Translated]" if uploaded_trans_pdf else f"Source Text:\n{source_text}"
                        doc_bytes = generate_word_document(context_note, final_translation, title=f"Legal Translation ({target_lang})")
                        st.download_button(
                            label="📄 DOWNLOAD TRANSLATION AS WORD",
                            data=doc_bytes,
                            file_name=f"Translation_{target_lang}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            type="primary"
                        )

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
                            
                            col1, col2 = st.columns([0.2, 0.8])
                            with col1:
                                if st.button("DELETE RECORD", key=f"del_{item['id']}", type="secondary"):
                                    db.delete_space_item(item['id'])
                                    st.rerun()
                            with col2:
                                doc_bytes = generate_word_document(item['query'], item['response'])
                                st.download_button(
                                    label="📄 EXPORT TO WORD",
                                    data=doc_bytes,
                                    file_name=f"VidhiDesk_Research_{item['id']}.docx",
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    key=f"dl_{item['id']}"
                                )

if __name__ == "__main__":
    if st.session_state.user:
        main_app()
    else:
        login_page()
