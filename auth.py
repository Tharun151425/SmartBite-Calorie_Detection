import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import datetime
import extra_streamlit_components as stx
from streamlit_cookies_controller import CookieController
from globals import cookie_key

load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


st.session_state['key']=None

# Cookie manager for session handling
def get_cookie_manager():
    """Initialize and return a cookie manager with a unique key"""
    return stx.CookieManager(key=cookie_key)
# cookie_setter = CookieController(key=cookie_key)
cookie_deleter= get_cookie_manager()


def login_page(supabase: Client,  cookie_deleter: stx.CookieManager):
    
    col1,col2,col3=st.columns([0.15,0.60,0.15])

    
    with col2:
        st.markdown("### Login")
        
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            try:
                # Authenticate with Supabase
                response = supabase.auth.sign_in_with_password({"email": email, "password": password})
                
                if response.user:
                    # Set a persistent login cookie
                    # cookie_setter.set("user_token",response.session.access_token,expires=datetime.datetime.now() + datetime.timedelta(days=7))
                    cookie_deleter.set(cookie_key,response.session.access_token)
                    
                    st.session_state['user_id'] = response.user.id
                    st.session_state['user_email'] = response.user.email
                    st.session_state['logged_in'] = True
                    st.rerun()
                else:
                    st.error("Login failed. Please check your credentials.")
            except Exception as e:
                st.error(f"Login error: {str(e)}")
        
        st.markdown("### New User?")
        if st.button("Create Account"):
            st.session_state['page'] = 'signup'
            st.rerun()

    # Footer
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #00ccff; font-family: Orbitron;'>SmartBite AI © 2024</p>",
        unsafe_allow_html=True
    )

def signup_page(supabase: Client):

    col1,col2,col3=st.columns([0.15,0.60,0.15])
   
    with col2:
        st.markdown("### Create New Account")
        
        new_email = st.text_input("Email")
        new_password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        if st.button("Create Account"):
            if new_password != confirm_password:
                st.error("Passwords do not match!")
                return
            
            try:
                # Create user with Supabase Auth
                response = supabase.auth.sign_up({
                    "email": new_email,
                    "password": new_password
                })
                
                if response.user:
                    st.success("Account created successfully! Please log in.")
                    st.session_state['page'] = 'login'
                    st.rerun()
                else:
                    st.error("Account creation failed.")
            except Exception as e:
                st.error(f"Signup error: {str(e)}")
        
        if st.button("Back to Login"):
            st.session_state['page'] = 'login'
            st.rerun()


    # Footer
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #00ccff; font-family: Orbitron;'>SmartBite AI © 2024</p>",
        unsafe_allow_html=True
    )