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

# --- 2. SESSION STATE SETUP ---
if "user" not in st.session_state: st.session_state.user = None
if "auth_page" not in st.session_state: st.session_state.auth_page = "login"
if "generated_response" not in st.session_state: st.session_state.generated_response = False

# --- 3. DATABASE MANAGEMENT (SQLite) ---
# We use a single robust class to handle all data.
class DBHandler:
    def __init__(self, db_name="vidhidesk_v3.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        c = self.conn.cursor()
        # Users Table
        c.execute('''CREATE TABLE IF NOT EXISTS users 
                     (email TEXT PRIMARY KEY, password TEXT, name TEXT, institution TEXT, year TEXT)''')
        # Chat History
        c.execute('''CREATE TABLE IF NOT EXISTS chats 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, role TEXT, content TEXT, timestamp DATETIME)''')
        # Spaces (Saved Research)
        c.execute('''CREATE TABLE IF NOT EXISTS spaces 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, category TEXT, query TEXT, response TEXT, timestamp DATETIME)''')
        self.conn.commit()

    def register(self, email, password, name, institution, year):
        try:
            hashed_pw = hashlib.sha256(password.encode()).hexdigest()
            self.conn.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)", 
                              (email, hashed_pw, name, institution, year))
            self.conn.commit()
            return True, "Registration successful! Please log in."
        except sqlite3.IntegrityError:
            return False, "Email already registered."

    def login(self, email, password):
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        cur = self.conn.execute("SELECT name, institution, year FROM users WHERE email=? AND password=?", (email, hashed_pw))
        user = cur.fetchone()
        if user:
            return {"email": email, "name": user[0], "institution": user[1], "year": user[2]}
        return None

    def save_message(self, email, role, content):
        self.conn.execute("INSERT INTO chats (email, role, content, timestamp) VALUES (?, ?, ?, ?)", 
                          (email, role, content, datetime.now()))
        self.conn.commit()

    def get_history(self, email):
        cur = self.conn.execute("SELECT role, content FROM chats WHERE email=? ORDER BY id ASC", (email,))
        return [{"role": row[0], "content": row[1]} for row in cur.fetchall()]

    def clear_history(self, email):
        self.conn.execute("DELETE FROM chats WHERE email=?", (email,))
        self.conn.commit()

    def save_to_space(self, email, category, query, response):
        self.conn.execute("INSERT INTO spaces (email, category, query, response, timestamp) VALUES (?, ?, ?, ?, ?)", 
                          (email, category, query, response, datetime.now()))
        self.conn.commit()

    def get_space_items(self, email, category):
        cur = self.conn.execute("SELECT id, query, response, timestamp FROM spaces WHERE email=? AND category=? ORDER BY id DESC", (email, category))
        return [{"id": r[0], "query": r[1], "response": r[2], "timestamp": r[3]} for r in cur.fetchall()]

    def delete_space_item(self, item_id):
        self.conn.execute("DELETE FROM spaces WHERE id=?", (item_id,))
        self.conn.commit()

db = DBHandler()

# --- 4. AI ENGINE ---
def get_gemini_response(query, tone, difficulty, api_key):
    if not api_key:
        return "⚠️ **System Error:** API Key is missing. Please add it in the sidebar."

    genai.configure(api_key=api_key)
    
    # SYSTEM PROMPT
    sys_instruction = f"""
    You are VidhiDesk, an expert Indian legal research assistant.
    TONE: {tone}
    COMPLEXITY: {difficulty}
    
    GUIDELINES:
    1. STRICTLY reference Indian Laws (IPC, BNS, Constitution, CrPC, BNSS).
    2. Cite relevant Supreme Court or High Court judgements if applicable.
    3. Use formatting (Bold sections, Bullet points) for readability.
    4. If the query is non-legal, politely steer it back to law.
    """

    # We ONLY use the stable 1.5 models. No experimental/deprecated aliases.
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(f"{sys_instruction}\n\nUSER QUERY: {query}")
        return response.text
    except Exception as e:
        # Fallback to Pro if Flash fails
        try:
            model = genai.GenerativeModel('gemini-1.5-pro')
            response = model.generate_content(f"{sys_instruction}\n\nUSER QUERY: {query}")
            return response.text
        except Exception as e2:
            return f"❌ **Connection Error:** Could not reach Google AI. \nError Details: {str(e2)}"

# --- 5. UI COMPONENTS ---

def login_screen():
    c1, c2, c3 = st.columns([1, 0.8, 1])
    with c2:
        st.markdown("### ⚖️ VidhiDesk Login")
        
        if st.session_state.auth_page == "login":
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_pass")
            
            if st.button("Log In", type="primary", use_container_width=True):
                user = db.login(email, password)
                if user:
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
            
            st.markdown("---")
            if st.button("Create Account"):
                st.session_state.auth_page = "register"
                st.rerun()

        else: # Register Page
            st.markdown("#### New Researcher Profile")
            r_name = st.text_input("Full Name")
            r_email = st.text_input("Email")
            r_pass = st.text_input("Password", type="password")
            
            # Top Indian Law Schools list
            institutes = [
                "NLSIU Bangalore", "NLU Delhi", "NALSAR Hyderabad", "WBNUJS Kolkata", 
                "NLU Jodhpur", "GNLU Gandhinagar", "Symbiosis Law School", "Christ University",
                "Faculty of Law, DU", "GLC Mumbai", "TNNLU Tiruchirappalli", "Other"
            ]
            r_inst = st.selectbox("Institution", institutes)
            r_year = st.selectbox("Year", ["1st Year", "2nd Year", "3rd Year", "4th Year", "5th Year", "Graduate"])
            
            if st.button("Register", type="primary", use_container_width=True):
                success, msg = db.register(r_email, r_pass, r_name, r_inst, r_year)
                if success:
                    st.success(msg)
                    time.sleep(1)
                    st.session_state.auth_page = "login"
                    st.rerun()
                else:
                    st.error(msg)
            
            if st.button("Back to Login"):
                st.session_state.auth_page = "login"
                st.rerun()

def main_app():
    # --- SIDEBAR ---
    with st.sidebar:
        st.header(f"Welcome, {st.session_state.user['name'].split()[0]}")
        st.caption(f"🎓 {st.session_state.user['institution']}")
        st.markdown("---")
        
        nav = st.radio("Navigation", ["Research Hub", "My Spaces", "Settings"], label_visibility="collapsed")
        
        st.markdown("### 🔑 API Access")
        api_key = st.text_input("Gemini API Key", type="password", help="Get key from aistudio.google.com")
        
        st.markdown("---")
        if st.button("Log Out"):
            st.session_state.user = None
            st.rerun()

    # --- PAGE ROUTING ---
    if nav == "Research Hub":
        st.title("🏛️ Legal Research Assistant")
        
        # Controls
        with st.expander("⚙️ Search Configuration", expanded=True):
            c1, c2, c3 = st.columns(3)
            tone = c1.select_slider("Tone", options=["Casual", "Informative", "Academic"], value="Academic")
            diff = c2.select_slider("Complexity", options=["Simple", "Intermediate", "Bare Act"], value="Intermediate")
            space = c3.selectbox("Auto-save to Space", ["None", "Research", "Paper", "Study"])

        # Chat Interface (Native Streamlit)
        history = db.get_history(st.session_state.user['email'])
        
        # 1. Render History
        for msg in history:
            avatar = "🧑‍⚖️" if msg['role'] == "user" else "🤖"
            with st.chat_message(msg['role'], avatar=avatar):
                st.markdown(msg['content'])

        # 2. Input
        if query := st.chat_input("Ask about Indian Law (e.g., 'Analyze Article 21')..."):
            # Display User Message
            with st.chat_message("user", avatar="🧑‍⚖️"):
                st.markdown(query)
            db.save_message(st.session_state.user['email'], "user", query)

            # Generate AI Response
            with st.chat_message("assistant", avatar="🤖"):
                message_placeholder = st.empty()
                message_placeholder.markdown("Checking Case Laws... ⏳")
                
                response = get_gemini_response(query, tone, diff, api_key)
                
                message_placeholder.markdown(response)
                db.save_message(st.session_state.user['email'], "assistant", response)

                if space != "None":
                    db.save_to_space(st.session_state.user['email'], space, query, response)
                    st.toast(f"Saved to {space} Space", icon="📂")

        # Clear Chat
        if st.button("Start New Chat", type="secondary"):
            db.clear_history(st.session_state.user['email'])
            st.rerun()

    elif nav == "My Spaces":
        st.title("🗂️ Knowledge Spaces")
        
        tab1, tab2, tab3 = st.tabs(["📚 Research", "📝 Paper", "🎓 Study"])
        categories = ["Research", "Paper", "Study"]
        
        for tab, cat in zip([tab1, tab2, tab3], categories):
            with tab:
                items = db.get_space_items(st.session_state.user['email'], cat)
                if not items:
                    st.info(f"No research saved in {cat} yet.")
                else:
                    for item in items:
                        with st.expander(f"📄 {item['query'][:60]}..."):
                            st.markdown(item['response'])
                            st.caption(f"Saved: {item['timestamp']}")
                            if st.button("Delete Note", key=f"del_{item['id']}"):
                                db.delete_space_item(item['id'])
                                st.rerun()

    elif nav == "Settings":
        st.title("Settings")
        st.write("User Profile Management coming soon.")

# --- 6. MAIN EXECUTION ---
if __name__ == "__main__":
    if st.session_state.user:
        main_app()
    else:
        login_screen()
