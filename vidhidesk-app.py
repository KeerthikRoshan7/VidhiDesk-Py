import streamlit as st
import google.generativeai as genai
import sqlite3
import pandas as pd
from datetime import datetime
import time

# --- 1. APP CONFIGURATION ---
st.set_page_config(
    page_title="VidhiDesk | Legal Intelligence",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. EXTENSIVE INSTITUTION LIST (As Requested) ---
# A comprehensive list of NLUs, Central, State, and Top Private Law Universities in India
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

# --- 3. DATABASE HANDLER (No Auth, Single Session) ---
class DBHandler:
    def __init__(self, db_name="vidhidesk_v4.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        c = self.conn.cursor()
        # Chat History (No user ID needed, we use a single session scope)
        c.execute('''CREATE TABLE IF NOT EXISTS chats 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT, content TEXT, timestamp DATETIME)''')
        # Spaces
        c.execute('''CREATE TABLE IF NOT EXISTS spaces 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, query TEXT, response TEXT, timestamp DATETIME)''')
        self.conn.commit()

    def save_message(self, role, content):
        self.conn.execute("INSERT INTO chats (role, content, timestamp) VALUES (?, ?, ?)", 
                          (role, content, datetime.now()))
        self.conn.commit()

    def get_history(self):
        cur = self.conn.execute("SELECT role, content FROM chats ORDER BY id ASC")
        return [{"role": row[0], "content": row[1]} for row in cur.fetchall()]

    def clear_history(self):
        self.conn.execute("DELETE FROM chats")
        self.conn.commit()

    def save_to_space(self, category, query, response):
        self.conn.execute("INSERT INTO spaces (category, query, response, timestamp) VALUES (?, ?, ?, ?)", 
                          (category, query, response, datetime.now()))
        self.conn.commit()

    def get_space_items(self, category):
        cur = self.conn.execute("SELECT id, query, response, timestamp FROM spaces WHERE category=? ORDER BY id DESC", (category,))
        return [{"id": r[0], "query": r[1], "response": r[2], "timestamp": r[3]} for r in cur.fetchall()]

    def delete_space_item(self, item_id):
        self.conn.execute("DELETE FROM spaces WHERE id=?", (item_id,))
        self.conn.commit()

db = DBHandler()

# --- 4. AI ENGINE (Robust Model Hunter) ---
def get_gemini_response(query, tone, difficulty, institution, api_key):
    if not api_key:
        return "⚠️ **System Error:** API Key is missing. Please add it in the sidebar."

    genai.configure(api_key=api_key)
    
    # ULTRA-DETAILED SYSTEM PROMPT
    sys_instruction = f"""
    ROLE: You are VidhiDesk, a highly advanced legal research assistant tailored for Indian Law students at {institution}.
    
    CORE COMPETENCIES:
    1. Bharatiya Nyaya Sanhita (BNS) & IPC Comparative Analysis.
    2. Bharatiya Nagarik Suraksha Sanhita (BNSS) & CrPC Procedures.
    3. Bharatiya Sakshya Adhiniyam (BSA) & Indian Evidence Act.
    4. Constitution of India (Articles, Schedules, Amendments).
    5. Supreme Court of India Landmark Judgements (ratios, obiter dicta).
    
    PARAMETERS:
    - Tone: {tone} (e.g., if 'Academic', use citations and Bluebook style formatting).
    - Complexity: {difficulty} (e.g., if 'Bare Act', quote the statute verbatim).
    
    INSTRUCTIONS:
    - Structure your response using clear Markdown headers (##).
    - Use bullet points for case laws.
    - If a law has been recently amended or replaced (e.g., IPC to BNS), explicitly mention the transition and the new section number.
    - Provide a "Key Takeaway" or "Legal Principle" summary at the end.
    """

    # MODEL HUNTING: Try these models in order until one works.
    models_to_try = [
        'gemini-1.5-flash',
        'gemini-1.5-pro',
        'gemini-2.0-flash-exp',
        'gemini-1.0-pro'
    ]

    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            # Try to generate content
            response = model.generate_content(f"{sys_instruction}\n\nUSER QUERY: {query}")
            return f"**[Source: {model_name}]**\n\n" + response.text
        except Exception:
            continue # Try next model silently

    return "❌ **Connection Failure:** Unable to reach Google AI using any known model versions. Please check your API Key permissions."

# --- 5. UI LAYOUT ---

# Custom CSS for that "Beige-Purple" aesthetic user originally wanted, mixed with Dark Mode
st.markdown("""
<style>
    /* Dark Theme Base */
    .stApp { background-color: #0E0E0E; color: #E0E0E0; }
    
    /* Sidebar */
    section[data-testid="stSidebar"] { background-color: #151515; border-right: 1px solid #333; }
    
    /* Headers */
    h1, h2, h3 { color: #BB86FC !important; font-family: 'Segoe UI', sans-serif; }
    
    /* Buttons */
    .stButton > button {
        background: #6200EA; color: white; border-radius: 8px; border: none;
        transition: all 0.3s;
    }
    .stButton > button:hover { background: #7C4DFF; transform: scale(1.02); }
    
    /* Chat Messages */
    .stChatMessage { background-color: #1E1E1E; border-radius: 10px; border: 1px solid #333; }
    
    /* Inputs */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] div {
        background-color: #222; color: white; border-radius: 8px; border: 1px solid #444;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR SETTINGS ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/924/924915.png", width=50)
    st.title("VidhiDesk")
    st.caption("v2.5 | No Login Required")
    
    st.markdown("### 🎓 Researcher Profile")
    user_inst = st.selectbox("Institution", INSTITUTIONS, index=0)
    
    st.markdown("### 🔑 API Configuration")
    api_key = st.text_input("Gemini API Key", type="password", value=st.session_state.get("api_key", ""), help="Required for AI analysis")
    if api_key: st.session_state.api_key = api_key

    st.markdown("---")
    nav = st.radio("Navigate", ["Research Assistant", "Saved Spaces"], label_visibility="collapsed")
    
    st.markdown("---")
    if st.button("🗑️ Clear All History", type="secondary"):
        db.clear_history()
        st.rerun()

# --- MAIN PAGE: RESEARCH ---
if nav == "Research Assistant":
    st.markdown("## 🏛️ Legal Research Assistant")
    
    # Controls
    with st.expander("⚙️ Analysis Parameters", expanded=True):
        c1, c2, c3 = st.columns(3)
        tone = c1.select_slider("Tone", ["Casual", "Informative", "Academic"], value="Academic")
        diff = c2.select_slider("Depth", ["Simple", "Intermediate", "Bare Act"], value="Intermediate")
        space = c3.selectbox("Auto-save to Space", ["None", "Research", "Paper", "Study"])

    # Chat UI
    history = db.get_history()
    
    # Render History
    for msg in history:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])

    # Input
    if query := st.chat_input("Ask about BNS, Constitution, or Case Laws..."):
        # 1. User Message
        with st.chat_message("user"):
            st.markdown(query)
        db.save_message("user", query)

        # 2. AI Response
        with st.chat_message("assistant"):
            if not st.session_state.get("api_key"):
                st.error("Please enter your API Key in the sidebar.")
            else:
                placeholder = st.empty()
                placeholder.markdown("`Analyzing Statutes...`")
                
                response = get_gemini_response(query, tone, diff, user_inst, st.session_state.api_key)
                
                placeholder.markdown(response)
                db.save_message("assistant", response)

                # 3. Auto-Save
                if space != "None":
                    db.save_to_space(space, query, response)
                    st.toast(f"Saved to {space}!", icon="💾")

# --- MAIN PAGE: SPACES ---
elif nav == "Saved Spaces":
    st.markdown("## 🗂️ Knowledge Spaces")
    
    t1, t2, t3 = st.tabs(["📚 Research", "📝 Paper", "🎓 Study"])
    
    for tab, cat in zip([t1, t2, t3], ["Research", "Paper", "Study"]):
        with tab:
            items = db.get_space_items(cat)
            if not items:
                st.info(f"No items saved in {cat}.")
            else:
                for item in items:
                    with st.expander(f"📄 {item['query'][:80]}..."):
                        st.markdown(item['response'])
                        st.caption(f"Saved: {item['timestamp']}")
                        if st.button("Delete", key=f"del_{item['id']}"):
                            db.delete_space_item(item['id'])
                            st.rerun()
