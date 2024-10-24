import streamlit as st
import time
import hmac
import hashlib
import base64
from datetime import datetime, timedelta

class LoginManager:
    def __init__(self, timeout_minutes=30):
        self.timeout_minutes = timeout_minutes
        
        # Initialize session state variables if they don't exist
        if 'login_time' not in st.session_state:
            st.session_state.login_time = None
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
            
        # Demo user credentials - In production, use a secure database
        self.users = {
            "demo@example.com": self.hash_password("demo123"),
            "admin@example.com": self.hash_password("admin123")
        }
    
    @staticmethod
    def hash_password(password):
        """Create a secure hash of the password"""
        salt = "financial_analyzer_salt"  # In production, use unique salt per user
        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()
    
    def verify_password(self, email, password):
        """Verify if the provided password matches the stored hash"""
        if email not in self.users:
            return False
        hashed_input = self.hash_password(password)
        return hmac.compare_digest(hashed_input, self.users[email])
    
    def login(self, email, password):
        """Attempt to log in the user"""
        if self.verify_password(email, password):
            st.session_state.authenticated = True
            st.session_state.login_time = datetime.now()
            st.session_state.user_email = email
            return True
        return False
    
    def logout(self):
        """Log out the user"""
        st.session_state.authenticated = False
        st.session_state.login_time = None
        if 'user_email' in st.session_state:
            del st.session_state.user_email
    
    def check_session(self):
        """Check if the current session is valid"""
        if not st.session_state.authenticated:
            return False
            
        if st.session_state.login_time is None:
            return False
            
        # Check if session has timed out
        elapsed = datetime.now() - st.session_state.login_time
        if elapsed > timedelta(minutes=self.timeout_minutes):
            self.logout()
            return False
            
        # Update login time on activity
        st.session_state.login_time = datetime.now()
        return True

def render_login_page():
    """Render the login page with custom styling"""
    st.markdown("""
        <style>
            /* Login Container */
            .login-container {
                max-width: 400px;
                margin: 2rem auto;
                padding: 2rem;
                background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
                border-radius: 12px;
                border: 1px solid rgba(255,255,255,0.1);
            }
            
            /* Input Fields */
            .stTextInput > div > div {
                background-color: #374151 !important;
            }
            
            /* Login Button */
            .stButton > button {
                width: 100%;
                background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
                color: white;
                padding: 0.75rem 0;
                border-radius: 8px;
                border: none;
                font-weight: 600;
                margin-top: 1rem;
            }
            
            .stButton > button:hover {
                background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
                transform: translateY(-2px);
                box-shadow: 0 8px 16px rgba(0,0,0,0.2);
            }
            
            /* Logo */
            .logo-container {
                text-align: center;
                margin-bottom: 2rem;
            }
            
            .logo-container img {
                width: 120px;
                height: auto;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # Login form
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("""
            <div class="login-container">
                <div class="logo-container">
                    <h1 style='color: #FFF5E1; font-size: 1.8rem; margin-bottom: 0.5rem;'>
                        Financial Health Analyzer
                    </h1>
                    <p style='color: #9ca3af; margin-bottom: 2rem;'>Sign in to continue</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Sign In", key="login_button"):
            login_manager = LoginManager()
            if login_manager.login(email, password):
                st.success("Login successful! Redirecting...")
                time.sleep(1)
                st.experimental_rerun()
            else:
                st.error("Invalid email or password")

def initialize_login_system():
    """Initialize the login system and manage session state"""
    login_manager = LoginManager()
    
    # If not authenticated, show login page
    if not login_manager.check_session():
        render_login_page()
        st.stop()  # Stop execution here if not authenticated
    
    # Add logout button in sidebar if authenticated
    with st.sidebar:
        if st.button("Logout"):
            login_manager.logout()
            st.experimental_rerun()
