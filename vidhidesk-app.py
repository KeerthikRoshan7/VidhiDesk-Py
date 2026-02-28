import streamlit as st
from google import genai
from google.genai import types
import hashlib
import time
import uuid
from datetime import datetime
import PyPDF2
from docx import Document
import io
from supabase import create_client, Client

# --- 1. APP CONFIGURATION & SESSION INIT ---
st.set_page_config(
    page_title="VidhiDesk | Legal Intelligence",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session States
if "user" not in st.session_state: st.session_state.user = None
if "current_workspace" not in st.session_state: st.session_state.current_workspace = {"id": 0, "name": "General Workspace"}

# --- 2. OBSIDIAN, LIQUID GOLD & CYBER PURPLE THEME ---
t_bg = "#050505"
t_container = "#0A0A0B"
t_text = "#E2E8F0"
t_subtext = "#94A3B8"
t_border = "rgba(212, 175, 55, 0.15)"
t_border_cyber = "rgba(139, 92, 246, 0.3)"
t_input_bg = "#0F0F11"
t_chat_bg = "rgba(255, 255, 255, 0.02)"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');

    /* =========================================
       1. CORE UI ANIMATIONS & STREAMLIT OVERRIDES
       ========================================= */
    @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    @keyframes pulseGlow {{ 0% {{ filter: drop-shadow(0 0 5px rgba(217, 70, 239, 0.2)); }} 50% {{ filter: drop-shadow(0 0 15px rgba(217, 70, 239, 0.6)); }} 100% {{ filter: drop-shadow(0 0 5px rgba(217, 70, 239, 0.2)); }} }}
    @keyframes activeGlow {{ 0% {{ box-shadow: inset 0 0 10px rgba(139, 92, 246, 0.05); }} 50% {{ box-shadow: inset 0 0 20px rgba(139, 92, 246, 0.15); }} 100% {{ box-shadow: inset 0 0 10px rgba(139, 92, 246, 0.05); }} }}

    /* LOGIN PAGE CINEMATIC SEQUENCE */
    @keyframes cyberAssemblyLeft {{ 0% {{ transform: translateX(-40px) translateY(-20px); opacity: 0; filter: blur(5px); }} 100% {{ transform: translateX(0) translateY(0); opacity: 1; filter: blur(0); }} }}
    @keyframes cyberAssemblyRight {{ 0% {{ transform: translateX(40px) translateY(20px); opacity: 0; filter: blur(5px); }} 100% {{ transform: translateX(0) translateY(0); opacity: 1; filter: blur(0); }} }}
    @keyframes cyberAssemblyCenter {{ 0% {{ transform: scale(0.5); opacity: 0; }} 60% {{ transform: scale(1.05); opacity: 1; filter: drop-shadow(0 0 20px #D946EF); }} 100% {{ transform: scale(1); opacity: 1; }} }}
    @keyframes formCascade {{ 0% {{ opacity: 0; transform: translateY(30px); }} 100% {{ opacity: 1; transform: translateY(0); }} }}

    .split-left {{ animation: cyberAssemblyLeft 1.2s cubic-bezier(0.2, 0.8, 0.2, 1) forwards; }}
    .split-right {{ animation: cyberAssemblyRight 1.2s cubic-bezier(0.2, 0.8, 0.2, 1) forwards; }}
    .split-center {{ animation: cyberAssemblyCenter 1s cubic-bezier(0.2, 0.8, 0.2, 1) forwards; }}
    .login-svg {{ animation: pulseGlow 4s infinite 1.5s; overflow: visible; }}

    /* Scope the delays ONLY to the login page to keep the main app fast */
    body:has(#login-page-marker) .vidhi-title {{ animation: formCascade 0.8s ease-out 1s forwards; opacity: 0; }}
    body:has(#login-page-marker) .temple-divider {{ animation: formCascade 0.8s ease-out 1.1s forwards; opacity: 0; }}
    body:has(#login-page-marker) .vidhi-subtitle {{ animation: formCascade 0.8s ease-out 1.2s forwards; opacity: 0; }}
    body:has(#login-page-marker) div[data-testid="stTabs"] {{ animation: formCascade 1s cubic-bezier(0.2, 0.8, 0.2, 1) 1.5s forwards; opacity: 0; }}

    .stApp {{ animation: fadeIn 0.6s cubic-bezier(0.4, 0, 0.2, 1); }}
    header[data-testid="stHeader"] {{ background: transparent !important; box-shadow: none !important; }}
    [data-testid="stHeaderActionElements"], #MainMenu, .stDeployButton, footer, div[data-testid="stDecoration"] {{ display: none !important; }}
    .block-container {{ padding-top: 2rem !important; padding-bottom: 6rem !important; }}
    section[data-testid="stSidebar"] > div {{ padding-top: 1.5rem !important; }}

    /* FORCE OBSIDIAN THEME ACROSS CONTAINERS */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stMainBlockContainer"] {{ background-color: {t_bg} !important; color: {t_text} !important; font-family: 'Inter', sans-serif; }}
    section[data-testid="stSidebar"] {{ background-color: {t_container} !important; border-right: 1px solid {t_border} !important; }}
    h1, h2, h3, h4, h5, h6 {{ font-family: 'Cinzel', serif !important; font-weight: 600 !important; color: {t_text} !important; transition: color 0.3s ease; }}
    div[data-testid="stBottom"], div[data-testid="stBottomBlockContainer"] {{ background-color: {t_bg} !important; background: {t_bg} !important; }}
    div[data-testid="stBottom"] > div {{ background-color: transparent !important; }}

    input::placeholder, textarea::placeholder, .stChatInput textarea::placeholder {{ color: {t_text} !important; opacity: 0.45 !important; transition: opacity 0.3s ease; }}
    input:focus::placeholder, textarea:focus::placeholder {{ opacity: 0.7 !important; }}
    
    /* =========================================
       2. SIDEBAR TABS - STRICT CENTERED EQUAL GRID
       ========================================= */
    div[role="radiogroup"] {{
        display: grid !important; grid-template-columns: 1fr 1fr !important; grid-auto-rows: 48px !important;
        gap: 8px !important; width: 100% !important; align-items: stretch !important;
    }}
    div[role="radiogroup"] label > div:first-child:not([data-testid="stMarkdownContainer"]), div[role="radiogroup"] label div[data-baseweb="radio"], div[role="radiogroup"] label input {{ 
        display: none !important; width: 0 !important; height: 0 !important; opacity: 0 !important; position: absolute !important;
    }}
    div[role="radiogroup"] label {{
        width: 100% !important; height: 100% !important; margin: 0 !important; padding: 0 !important; cursor: pointer !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
        background-color: {t_container} !important; border: 1px solid {t_border} !important; border-radius: 4px !important;
        box-sizing: border-box !important; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }}
    div[role="radiogroup"] label div[data-testid="stMarkdownContainer"] {{ width: 100% !important; height: 100% !important; display: flex !important; align-items: center !important; justify-content: center !important; }}
    div[role="radiogroup"] label div[data-testid="stMarkdownContainer"] p {{
        font-size: 0.85rem !important; font-weight: 600 !important; color: {t_subtext} !important; 
        margin: 0 !important; padding: 0 !important; line-height: 1 !important; text-align: center !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
        width: 100% !important; height: 100% !important; transition: color 0.3s ease !important;
    }}

    div[role="radiogroup"] label:hover {{ background-color: rgba(139, 92, 246, 0.05) !important; border-color: {t_border_cyber} !important; transform: translateY(-2px); }}
    div[role="radiogroup"] label:hover div[data-testid="stMarkdownContainer"] p {{ color: #FFF !important; }}
    div[role="radiogroup"] label:has(input[aria-checked="true"]) {{
        background-color: {t_bg} !important; border-color: {t_border_cyber} !important; 
        border-left: 4px solid #8B5CF6 !important; animation: activeGlow 3s infinite;
    }}
    div[role="radiogroup"] label:has(input[aria-checked="true"]) div[data-testid="stMarkdownContainer"] p {{ color: #D946EF !important; }}

    /* =========================================
       3. COMPONENT STYLING & SMOOTHING
       ========================================= */
    div[data-testid="stVerticalBlock"]:has(#sticky-header-marker):not(:has(div[data-testid="stVerticalBlock"]:has(#sticky-header-marker))) {{
        position: sticky !important; top: 0rem !important; z-index: 999 !important;
        background-color: {t_bg} !important; padding: 15px 0px 15px 0px !important;
        border-bottom: 1px solid {t_border} !important; margin-bottom: 20px !important;
    }}

    .vidhi-title-container {{ width: 100%; text-align: center; padding-top: 2vh; padding-bottom: 2rem; }}
    .vidhi-title {{
        font-size: clamp(2.5rem, 6vw, 4.5rem); margin: 0 auto;
        background: linear-gradient(135deg, #BF953F 0%, #FCF6BA 40%, #B38728 60%, #AA771C 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; color: transparent;
        letter-spacing: 0.15em; white-space: nowrap !important; font-weight: 700 !important;
    }}
    .temple-divider {{ height: 1px; width: 200px; background: linear-gradient(90deg, transparent, #8B5CF6, transparent); margin: 15px auto; }}
    .vidhi-subtitle {{ color: {t_subtext}; font-size: 0.8rem; letter-spacing: 4px; text-transform: uppercase; }}
    p, label, span, div {{ color: {t_text}; }}

    ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb {{ background: rgba(139, 92, 246, 0.4); border-radius: 4px; transition: background 0.3s; }}
    ::-webkit-scrollbar-thumb:hover {{ background: rgba(139, 92, 246, 0.8); }}

    div[data-baseweb="select"] > div {{ background-color: {t_input_bg} !important; border: 1px solid {t_border} !important; color: {t_text} !important; border-radius: 6px !important; transition: all 0.3s ease !important; }}
    div[data-baseweb="select"] > div:hover, div[data-baseweb="select"] > div:focus-within {{ border-color: #8B5CF6 !important; box-shadow: 0 0 10px rgba(139, 92, 246, 0.1) !important; }}
    div[data-baseweb="popover"] {{ background-color: {t_container} !important; border: 1px solid #8B5CF6 !important; transition: all 0.3s ease; }}
    div[data-baseweb="popover"] li:hover {{ background-color: rgba(139, 92, 246, 0.15) !important; color: #D946EF !important; }}
    div[data-testid="stPopover"] > button {{ min-height: 48px !important; border-radius: 8px !important; transition: all 0.3s ease !important; }}

    .stTextInput > div > div > input, .stChatInput textarea, .stTextArea textarea {{
        background-color: {t_input_bg} !important; border: 1px solid {t_border} !important; color: {t_text} !important; border-radius: 6px !important; padding: 10px !important; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }}
    .stTextInput > div > div > input:focus, .stChatInput textarea:focus, .stTextArea textarea:focus {{ border-color: #8B5CF6 !important; box-shadow: 0 0 15px rgba(139, 92, 246, 0.2) !important; }}

    .stButton > button {{
        background: linear-gradient(135deg, #0A0A0B 0%, #111 100%) !important; color: #D4AF37 !important; font-family: 'Cinzel', serif !important; font-weight: 600 !important;
        border: 1px solid rgba(212, 175, 55, 0.5) !important; border-radius: 4px !important; text-transform: uppercase; letter-spacing: 1.5px; width: 100%; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }}
    .stButton > button:hover {{
        background: linear-gradient(135deg, #111 0%, #1a1a1a 100%) !important; border-color: #D946EF !important; color: #FFF !important; box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3) !important; transform: translateY(-2px);
    }}
    button[kind="secondary"] {{ background: transparent !important; border: 1px solid {t_subtext} !important; color: {t_subtext} !important; }}
    button[kind="secondary"]:hover {{ border-color: #8B5CF6 !important; color: #D946EF !important; }}

    .stChatMessage {{
        background-color: {t_chat_bg} !important; border: 1px solid {t_border} !important; border-radius: 12px !important; padding: 1.2rem !important; margin-bottom: 1rem !important;
        animation: fadeIn 0.4s ease-out; transition: transform 0.2s ease, border-color 0.3s ease;
    }}
    .stChatMessage:hover {{ border-color: rgba(212, 175, 55, 0.3) !important; }}
    .stChatMessage[data-testid="stChatMessageAvatar"] {{ background-color: #0A0A0B !important; border: 1px solid #D4AF37 !important; color: #D4AF37 !important; }}
    div[data-testid="stContainer"] > div > div > div {{ background-color: {t_container}; border-radius: 8px; }}
    button[data-baseweb="tab"] {{ color: {t_subtext} !important; font-weight: 600 !important; transition: all 0.3s ease !important; }}
    button[aria-selected="true"] {{ color: #D946EF !important; border-bottom: 2px solid #D946EF !important; }}
</style>
""", unsafe_allow_html=True)

# --- 3. HARDCODED LISTS ---
INSTITUTIONS = sorted([
    "National Law School of India University (NLSIU)", "NALSAR University of Law",
    "National Law University, Delhi (NLUD)", "The West Bengal National University of Juridical Sciences (WBNUJS)",
    "National Law University, Jodhpur (NLUJ)", "Hidayatullah National Law University (HNLU)",
    "Tamil Nadu National Law University (TNNLU)", "Maharashtra National Law University (MNLU)",
    "Faculty of Law, University of Delhi (DU)", "Government Law College (GLC), Mumbai", 
    "Symbiosis Law School (SLS)", "School of Law, Christ University", "Jindal Global Law School", "Other"
]) 

# --- 4. DATABASE MANAGER (SUPABASE CLOUD) ---
class DBHandler:
    def __init__(self):
        try:
            url: str = st.secrets["SUPABASE_URL"]
            key: str = st.secrets["SUPABASE_KEY"]
            self.supabase: Client = create_client(url, key)
        except Exception as e:
            st.error("⚠️ Supabase Credentials missing from Streamlit Secrets!")

    def register_user(self, email, password, name, inst, year):
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        try:
            self.supabase.table("users").insert({
                "email": email, "password": hashed_pw, "name": name, 
                "institution": inst, "year": year, "auth_token": "", "tier": "free"
            }).execute()
            return True
        except Exception:
            return False

    def login(self, email, password, remember_me=False):
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        response = self.supabase.table("users").select("*").eq("email", email).eq("password", hashed_pw).execute()
        
        if response.data:
            user = response.data[0]
            token = ""
            if remember_me:
                token = str(uuid.uuid4())
                self.supabase.table("users").update({"auth_token": token}).eq("email", email).execute()
            
            return {
                "email": user["email"], "name": user["name"], 
                "institution": user["institution"], "year": user["year"], 
                "tier": user.get("tier", "free"), "token": token
            }
        return None

    def login_with_token(self, token):
        if not token: return None
        response = self.supabase.table("users").select("*").eq("auth_token", token).execute()
        if response.data:
            user = response.data[0]
            return {
                "email": user["email"], "name": user["name"], 
                "institution": user["institution"], "year": user["year"], 
                "tier": user.get("tier", "free"), "token": token
            }
        return None

    def logout(self, email):
        self.supabase.table("users").update({"auth_token": ""}).eq("email", email).execute()

    def save_message(self, email, role, content, workspace_id=0):
        self.supabase.table("chats").insert({
            "email": email, "role": role, "content": content, 
            "workspace_id": workspace_id, "timestamp": datetime.now().isoformat()
        }).execute()

    def get_history(self, email, workspace_id=0):
        response = self.supabase.table("chats").select("role, content").eq("email", email).eq("workspace_id", workspace_id).order("id", desc=False).execute()
        return response.data if response.data else []

    def clear_history(self, email, workspace_id=0):
        self.supabase.table("chats").delete().eq("email", email).eq("workspace_id", workspace_id).execute()

    def save_to_space(self, email, category, query, response, workspace_id=0):
        self.supabase.table("spaces").insert({
            "email": email, "category": category, "query": query, 
            "response": response, "workspace_id": workspace_id, 
            "timestamp": datetime.now().isoformat()
        }).execute()

    def get_space_items(self, email, category, workspace_id=0):
        response = self.supabase.table("spaces").select("id, query, response, timestamp").eq("email", email).eq("category", category).eq("workspace_id", workspace_id).order("id", desc=True).execute()
        return response.data if response.data else []

    def delete_space_item(self, item_id):
        self.supabase.table("spaces").delete().eq("id", item_id).execute()

    def create_workspace(self, email, name):
        response = self.supabase.table("workspaces").insert({
            "email": email, "name": name, "created_at": datetime.now().isoformat()
        }).execute()
        return response.data[0]["id"] if response.data else 0

    def get_workspaces(self, email):
        response = self.supabase.table("workspaces").select("id, name").eq("email", email).order("created_at", desc=True).execute()
        return response.data if response.data else []

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
    if pdf_text: contents.append(f"\n[DOCUMENT CONTEXT UPLOADED BY USER]:\n{pdf_text[:15000]}\n\n(Base your answer heavily on the document above if relevant).")
    if audio_bytes: contents.append(types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav"))
    if query: contents.append(f"\nUSER QUERY: {query}")

    config = types.GenerateContentConfig(temperature=0.1 if strict_citation else 0.3)
    if enable_search: config.tools = [{"google_search": {}}]

    models_to_try = ['gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-2.0-flash']
    for model_name in models_to_try:
        try:
            response_stream = client.models.generate_content_stream(model=model_name, contents=contents, config=config)
            for chunk in response_stream:
                if chunk.text: yield chunk.text
            return 
        except Exception as e:
            if "API_KEY_INVALID" in str(e) or "not found" in str(e).lower():
                yield "❌ **Authentication Failed:** API key invalid or revoked."
                return
            continue 
    yield "❌ **System Unavailable:** AI servers failed to respond."

def get_drafting_stream(doc_type, facts, institution, pdf_text=None):
    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    except Exception:
        yield "❌ **System Config Error.**"
        return
        
    sys_instruction = f"""
    ROLE: You are a Senior Legal Draftsman at {institution} in India.
    TASK: Draft a professional, court-ready '{doc_type}'.
    MANDATE: Use strict, formal Indian legal terminology. Format properly using clear headings and numbered paragraphs. Use placeholders like [CLIENT NAME], [DATE], [AMOUNT] for missing facts. Base the entire draft strictly on the facts and documents provided.
    """
    contents = [sys_instruction]
    if pdf_text: contents.append(f"\n[REFERENCE DOCUMENT UPLOADED]:\n{pdf_text[:15000]}")
    if facts: contents.append(f"\n[CLIENT FACTS]:\n{facts}")
        
    try:
        response_stream = client.models.generate_content_stream(model='gemini-2.5-flash', contents=contents)
        for chunk in response_stream:
            if chunk.text: yield chunk.text
    except Exception as e: yield f"❌ **Drafting Engine Error:** {str(e)}"

def get_translation_stream(text, target_lang, institution, pdf_text=None):
    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    except Exception:
        yield "❌ **System Config Error.**"
        return
        
    sys_instruction = f"ROLE: You are an expert Legal Translator at {institution}. TASK: Translate the provided legal document/text accurately into highly formal {target_lang}. Preserve all legal meanings perfectly. Keep Latin maxims in Latin with translated meanings in brackets."
    contents = [sys_instruction]
    if pdf_text: contents.append(f"\n[DOCUMENT TO TRANSLATE]:\n{pdf_text[:15000]}")
    if text: contents.append(f"\n[ADDITIONAL TEXT TO TRANSLATE]:\n{text}")
        
    try:
        response_stream = client.models.generate_content_stream(model='gemini-2.5-flash', contents=contents)
        for chunk in response_stream:
            if chunk.text: yield chunk.text
    except Exception as e: yield f"❌ **Translation Engine Error:** {str(e)}"

# --- 7. UI LOGIC ---
def login_page():
    # Hidden marker to trigger scoped CSS animations
    st.markdown("<div id='login-page-marker'></div>", unsafe_allow_html=True)
    
    st.markdown("""
        <div class='vidhi-title-container'>
            <div style="display: flex; justify-content: center; margin-bottom: 25px;">
                <svg viewBox="0 0 100 100" class="login-svg" style="width: 140px; height: 140px;">
                    <defs>
                        <linearGradient id="g1" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#BF953F"/><stop offset="40%" stop-color="#FCF6BA"/><stop offset="100%" stop-color="#AA771C"/></linearGradient>
                        <linearGradient id="cyber" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#D946EF" /><stop offset="50%" stop-color="#8B5CF6" /><stop offset="100%" stop-color="#4C1D95" /></linearGradient>
                    </defs>
                    <g class="split-center"><path d="M 30 20 L 50 80 L 70 20 L 60 20 L 50 55 L 40 20 Z" fill="url(#g1)"/></g>
                    <g class="split-left"><path d="M 10 10 L 25 30 L 15 50 L 45 95 L 50 85 L 30 50 L 40 30 L 20 10 Z" fill="url(#cyber)"/><polygon points="50,5 53,15 50,25 47,15" fill="url(#cyber)"/></g>
                    <g class="split-right"><path d="M 90 10 L 75 30 L 85 50 L 55 95 L 50 85 L 70 50 L 60 30 L 80 10 Z" fill="url(#cyber)"/><polygon points="50,90 52,95 50,100 48,95" fill="url(#cyber)"/></g>
                </svg>
            </div>
            <h1 class='vidhi-title'>VIDHIDESK</h1>
            <div class='temple-divider'></div>
            <div class='vidhi-subtitle' style='color: #D946EF;'>Intelligent Legal Infrastructure</div>
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
                        else: st.error("Authentication Failed: Invalid token or key.")
                            
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
                        if success: st.success("Registration Successful! Please navigate to Login.")
                        else: st.error("Error: Email already registered in the system.")
                    else: st.warning("Please fill out all required fields.")

            with tab_guest:
                st.markdown("<br><p style='text-align: center; font-size: 0.9rem;'>Temporary access mode. Data will be tied to a temporary session.</p><br>", unsafe_allow_html=True)
                if st.button("CONTINUE AS GUEST", type="secondary", use_container_width=True):
                    st.session_state.user = { "email": f"guest_{int(time.time())}@vidhidesk.local", "name": "Guest User", "institution": "Independent Researcher", "year": "N/A", "tier": "free" }
                    st.rerun()

def main_app():
    with st.sidebar:
        # THE CYBERSIGILISM LOGO (DRAFT 7) AND HEADER
        st.markdown(f"""
            <div style='display: flex; align-items: center; margin-bottom: 10px; animation: fadeIn 0.8s ease-out;'>
                <svg viewBox="0 0 100 100" style="width: 50px; height: 50px; margin-right: 15px; flex-shrink: 0; filter: drop-shadow(0 0 8px rgba(217, 70, 239, 0.4));">
                    <defs>
                        <linearGradient id="g1" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#BF953F"/><stop offset="40%" stop-color="#FCF6BA"/><stop offset="100%" stop-color="#AA771C"/></linearGradient>
                        <linearGradient id="cyber" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#D946EF" /><stop offset="50%" stop-color="#8B5CF6" /><stop offset="100%" stop-color="#4C1D95" /></linearGradient>
                    </defs>
                    <path d="M 30 20 L 50 80 L 70 20 L 60 20 L 50 55 L 40 20 Z" fill="url(#g1)"/>
                    <path d="M 10 10 L 25 30 L 15 50 L 45 95 L 50 85 L 30 50 L 40 30 L 20 10 Z" fill="url(#cyber)"/>
                    <path d="M 90 10 L 75 30 L 85 50 L 55 95 L 50 85 L 70 50 L 60 30 L 80 10 Z" fill="url(#cyber)"/>
                    <polygon points="50,5 53,15 50,25 47,15" fill="url(#cyber)"/>
                    <polygon points="50,90 52,95 50,100 48,95" fill="url(#cyber)"/>
                </svg>
                <div>
                    <h2 style="margin:0; font-size:1.6rem; letter-spacing:1px; line-height: 1.1; font-family: 'Cinzel', serif; color: #E2E8F0;">VIDHIDESK</h2>
                    <span style="font-size: 0.65rem; color: #D946EF; letter-spacing: 3px; font-weight: 600; text-transform: uppercase;">Intelligence</span>
                </div>
            </div>
            <div class='temple-divider' style='margin: 15px 0 20px 0; width: 100%; background: linear-gradient(90deg, transparent, #8B5CF6, transparent);'></div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"<h3 style='margin-bottom: 0; color: {t_text} !important; font-size: 1.1rem;'>{st.session_state.user['name'].upper()}</h3>", unsafe_allow_html=True)
        st.markdown(f"<span style='color: #8B5CF6; font-size: 0.8rem; font-weight: 500;'>{st.session_state.user['institution']}</span>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size: 0.75rem; color: {t_subtext}; margin-bottom: 5px; font-weight: 600; letter-spacing: 1px;'>ACTIVE CASE FOLDER</div>", unsafe_allow_html=True)
        
        workspaces = [{"id": 0, "name": "General Workspace"}] + db.get_workspaces(st.session_state.user['email'])
        ws_names = [w['name'] for w in workspaces]
        
        current_index = 0
        for i, w in enumerate(workspaces):
            if w['id'] == st.session_state.current_workspace['id']: current_index = i
                
        selected_ws_name = st.selectbox("Workspace", ws_names, index=current_index, label_visibility="collapsed")
        for w in workspaces:
            if w['name'] == selected_ws_name and st.session_state.current_workspace['id'] != w['id']:
                st.session_state.current_workspace = w
                st.rerun()
        
        with st.popover("➕ Create Case Folder", use_container_width=True):
            new_ws_name = st.text_input("Client/Case Name", placeholder="e.g., State vs Sharma")
            if st.button("Create Folder", use_container_width=True):
                if new_ws_name:
                    new_id = db.create_workspace(st.session_state.user['email'], new_ws_name)
                    st.session_state.current_workspace = {"id": new_id, "name": new_ws_name}
                    st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        nav = st.radio("MODULES", ["⚖️ Research", "✍️ Drafting", "🌍 Translate", "📚 Vault"], label_visibility="collapsed")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if "GEMINI_API_KEY" in st.secrets:
            st.markdown(f"""
            <div style='border: 1px solid {t_border_cyber}; padding: 12px; border-radius: 6px; background: rgba(139, 92, 246, 0.05); margin-top:10px; transition: all 0.3s ease;'>
                <div style='display:flex; align-items:center; margin-bottom:5px;'>
                    <span style='color: #4CAF50; font-size: 1.2rem; margin-right: 8px;'>●</span> 
                    <span style='color: #D946EF; font-weight:600;'>System Online</span>
                </div>
                <div style='font-size: 0.7rem; color: {t_subtext};'>Engine: GenAI 2.5 Streaming</div>
            </div>
            """, unsafe_allow_html=True)
        else: st.error("Config Error: API Key missing.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("TERMINATE UPLINK", type="secondary"):
            db.logout(st.session_state.user["email"])
            st.session_state.user = None
            if "auth_token" in st.query_params: del st.query_params["auth_token"]
            st.rerun()

    # --- RESEARCH CORE ---
    if nav == "⚖️ Research":
        sticky_header = st.container()
        with sticky_header:
            st.markdown("<span id='sticky-header-marker'></span>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='margin-bottom: 0; color: {t_text} !important;'>RESEARCH CORE</h2>", unsafe_allow_html=True)
            st.markdown("<div class='temple-divider' style='margin: 10px 0 20px 0; width: 80px; margin-left: 0; background: linear-gradient(90deg, #D4AF37, transparent);'></div>", unsafe_allow_html=True)

            param_col, mic_col = st.columns([0.85, 0.15], vertical_alignment="center")
            
            with param_col:
                with st.popover("⚙️ ADVANCED PARAMETERS & GROUNDING", use_container_width=True):
                    st.markdown("#### Output Configuration")
                    c1, c2, c3 = st.columns(3)
                    with c1: tone = st.selectbox("OUTPUT TONE", ["Casual", "Professional", "Academic"], index=2)
                    with c2: diff = st.selectbox("ANALYSIS DEPTH", ["Summary", "Detailed", "Bare Act"], index=1)
                    with c3: space = st.selectbox("AUTO-ARCHIVE TO", ["None", "Research", "Paper", "Study"])
                        
                    st.markdown("---")
                    st.markdown("#### Database Grounding")
                    sc1, sc2, sc3 = st.columns([1, 1, 1])
                    with sc1: st.markdown("<br>", unsafe_allow_html=True); enable_search = st.toggle("🌐 Live Web Search")
                    with sc2: st.markdown("<br>", unsafe_allow_html=True); strict_citation = st.toggle("🛡️ Strict Citations")
                    with sc3: uploaded_pdf = st.file_uploader("📄 Upload PDF Context", type=["pdf"], key="res_pdf")

            with mic_col:
                with st.popover("🎙️ VOICE", use_container_width=True):
                    st.markdown("<div style='text-align:center; font-size:0.9rem; color:#888; margin-bottom:10px;'>Speak your legal query</div>", unsafe_allow_html=True)
                    audio_data = st.audio_input("Record", label_visibility="collapsed")
                    submit_audio = st.button("SEND AUDIO", use_container_width=True, type="secondary")

        history = db.get_history(st.session_state.user['email'], workspace_id=st.session_state.current_workspace['id'])
        for msg in history:
            avatar = "🧑‍⚖️" if msg['role'] == "user" else "⚖️"
            with st.chat_message(msg['role'], avatar=avatar): st.markdown(msg['content'])

        query = st.chat_input("Enter legal query, section, or case citation...")
        is_audio_submission = audio_data is not None and submit_audio

        if query or is_audio_submission:
            with st.chat_message("user", avatar="🧑‍⚖️"):
                if query: st.markdown(query)
                if is_audio_submission:
                    st.audio(audio_data)
                    if not query: query = "Please analyze this audio recording."
            
            db.save_message(st.session_state.user['email'], "user", query, workspace_id=st.session_state.current_workspace['id'])

            with st.chat_message("assistant", avatar="⚖️"):
                pdf_extracted_text = None
                if uploaded_pdf:
                    with st.spinner("Reading Document..."): pdf_extracted_text = extract_pdf_text(uploaded_pdf)
                
                audio_bytes = audio_data.getvalue() if is_audio_submission else None
                stream = get_gemini_stream(query, tone, diff, st.session_state.user['institution'], pdf_text=pdf_extracted_text, audio_bytes=audio_bytes, enable_search=enable_search, strict_citation=strict_citation)
                
                full_response = st.write_stream(stream)
                db.save_message(st.session_state.user['email'], "assistant", full_response, workspace_id=st.session_state.current_workspace['id'])

                if space != "None" and "❌" not in full_response:
                    db.save_to_space(st.session_state.user['email'], space, query, full_response, workspace_id=st.session_state.current_workspace['id'])
                    st.toast(f"Archived to {space}", icon="📂")
            st.rerun()

        if history:
            c1, c2 = st.columns([0.85, 0.15])
            with c2:
                if st.button("CLEAR LOGS", type="secondary"):
                    db.clear_history(st.session_state.user['email'], workspace_id=st.session_state.current_workspace['id'])
                    st.rerun()

    # --- DRAFTING STUDIO ---
    elif nav == "✍️ Drafting":
        st.markdown(f"<h2 style='margin-bottom: 0; color: {t_text} !important;'>DRAFTING STUDIO</h2>", unsafe_allow_html=True)
        st.markdown("<div class='temple-divider' style='margin: 10px 0 30px 0; width: 80px; margin-left: 0; background: linear-gradient(90deg, #D4AF37, transparent);'></div>", unsafe_allow_html=True)
        st.markdown("Automated generation of court-ready legal documents based on standard Indian formats.", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        with st.container(border=True):
            doc_type = st.selectbox("Document Type", ["Legal Notice (General)", "Legal Notice (Sec 138 NI Act - Cheque Bounce)", "Non-Disclosure Agreement (NDA)", "Bail Application (Under BNSS)", "Lease / Rent Agreement", "Writ Petition (Draft Format)"])
            facts = st.text_area("Client Facts & Details (Optional if PDF provided)", height=150, placeholder="E.g., Client name is Rahul. Tenant hasn't paid rent of Rs 50,000...")
            uploaded_draft_pdf = st.file_uploader("📄 Upload Reference Document / Old Contract (PDF)", type=["pdf"], key="draft_pdf")
            
            if st.button("GENERATE DRAFT", use_container_width=True):
                if not facts and not uploaded_draft_pdf: st.warning("Please provide either text facts or upload a reference PDF to generate a draft.")
                else:
                    st.markdown("---")
                    st.markdown(f"### Generated Draft: {doc_type}")
                    pdf_extracted_text = None
                    if uploaded_draft_pdf:
                        with st.spinner("Extracting Reference Document..."): pdf_extracted_text = extract_pdf_text(uploaded_draft_pdf)
                            
                    stream = get_drafting_stream(doc_type, facts, st.session_state.user['institution'], pdf_text=pdf_extracted_text)
                    final_draft = st.write_stream(stream)
                    
                    if "❌" not in final_draft:
                        context_note = f"Facts provided:\n{facts}\n\n[Reference PDF was uploaded and used in this draft]" if uploaded_draft_pdf else f"Facts provided:\n{facts}"
                        doc_bytes = generate_word_document(context_note, final_draft, title=f"Draft: {doc_type}")
                        st.download_button(label="📄 DOWNLOAD DRAFT AS WORD", data=doc_bytes, file_name=f"Draft_{doc_type.replace(' ', '_')}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", type="primary")

    # --- TRANSLATION DESK ---
    elif nav == "🌍 Translate":
        st.markdown(f"<h2 style='margin-bottom: 0; color: {t_text} !important;'>TRANSLATION DESK</h2>", unsafe_allow_html=True)
        st.markdown("<div class='temple-divider' style='margin: 10px 0 30px 0; width: 80px; margin-left: 0; background: linear-gradient(90deg, #D4AF37, transparent);'></div>", unsafe_allow_html=True)
        st.markdown("High-fidelity legal translation preserving complex terminology and legal nuances.", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        with st.container(border=True):
            target_lang = st.selectbox("Translate To", ["Hindi", "Tamil", "Marathi", "Bengali", "Telugu", "Gujarati", "Malayalam", "English"])
            source_text = st.text_area("Source Text (Optional if PDF provided)", height=150, placeholder="Paste legal document text here...")
            uploaded_trans_pdf = st.file_uploader("📄 Upload Document to Translate (PDF)", type=["pdf"], key="trans_pdf")
            
            if st.button("TRANSLATE", use_container_width=True):
                if not source_text and not uploaded_trans_pdf: st.warning("Please paste text or upload a PDF to translate.")
                else:
                    st.markdown("---")
                    st.markdown(f"### {target_lang} Translation")
                    pdf_extracted_text = None
                    if uploaded_trans_pdf:
                        with st.spinner("Extracting PDF Text for Translation..."): pdf_extracted_text = extract_pdf_text(uploaded_trans_pdf)
                            
                    stream = get_translation_stream(source_text, target_lang, st.session_state.user['institution'], pdf_text=pdf_extracted_text)
                    final_translation = st.write_stream(stream)
                    
                    if "❌" not in final_translation:
                        context_note = f"Source Text:\n{source_text}\n\n[PDF Document Translated]" if uploaded_trans_pdf else f"Source Text:\n{source_text}"
                        doc_bytes = generate_word_document(context_note, final_translation, title=f"Legal Translation ({target_lang})")
                        st.download_button(label="📄 DOWNLOAD TRANSLATION AS WORD", data=doc_bytes, file_name=f"Translation_{target_lang}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", type="primary")

    # --- VAULT ---
    elif nav == "📚 Vault":
        st.markdown(f"<h2 style='margin-bottom: 0; color: {t_text} !important;'>KNOWLEDGE VAULT <span style='font-size:0.5em; color:{t_subtext};'>[{st.session_state.current_workspace['name']}]</span></h2>", unsafe_allow_html=True)
        st.markdown("<div class='temple-divider' style='margin: 10px 0 30px 0; width: 80px; margin-left: 0; background: linear-gradient(90deg, #D4AF37, transparent);'></div>", unsafe_allow_html=True)
        
        t1, t2, t3 = st.tabs(["📚 RESEARCH", "📝 PAPERS", "🎓 STUDY"])
        for tab, cat in zip([t1, t2, t3], ["Research", "Paper", "Study"]):
            with tab:
                st.markdown("<br>", unsafe_allow_html=True)
                items = db.get_space_items(st.session_state.user['email'], cat, workspace_id=st.session_state.current_workspace['id'])
                if not items: st.info(f"Sector '{cat}' is empty in this folder.", icon="ℹ️")
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
                                st.download_button(label="📄 EXPORT TO WORD", data=doc_bytes, file_name=f"VidhiDesk_Research_{item['id']}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", key=f"dl_{item['id']}")

if __name__ == "__main__":
    if st.session_state.user: main_app()
    else: login_page()
