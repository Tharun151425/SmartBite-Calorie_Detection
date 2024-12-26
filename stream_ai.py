import streamlit as st
import requests
from PIL import Image
import io
import json
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
from ai_model import food_detect
from dotenv import load_dotenv
from supabase import create_client, Client
from auth import login_page, signup_page,cookie_deleter#,cookie_setter
from streamlit_cookies_controller import CookieController
import extra_streamlit_components as stx
from pages import home_page 
from globals import cookie_key



# # Cookie manager for session handling
# def get_cookie_manager():
#     """Initialize and return a cookie manager with a unique key"""
#     return stx.CookieManager(key=cookie_key)

# if cookie_key!=st.session_state['key']:
#     cookie_setter = CookieController(key=cookie_key)
#     cookie_deleter= get_cookie_manager()


#  page configuration
st.set_page_config(
    page_title="SmartBite AI",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)


load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Custom CSS 
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;700&display=swap');
    
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    }
    
    .main {
        background: transparent;
    }
    
    h1, h2, h3, .big-font {
        font-family: 'Orbitron', sans-serif !important;
        color: #00ff88 !important;
        text-shadow: 0 0 10px rgba(0,255,136,0.5);
    }
    
    .uploadfile {
        border: 2px dashed #00ff88;
        padding: 20px;
        border-radius: 15px;
        background: rgba(0,255,136,0.05);
    }
    
    .stButton button {
        background: linear-gradient(45deg, #00ff88, #00ccff) !important;
        color: #1a1a2e !important;
        font-family: 'Orbitron', sans-serif !important;
        font-weight: bold !important;
        border: none !important;
        border-radius: 25px !important;
        padding: 15px 30px !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton button:hover {
        transform: scale(1.05);
        box-shadow: 0 0 20px rgba(0,255,136,0.5);
    }
    
    .result-box {
        background: rgba(22, 33, 62, 0.8);
        border: 1px solid #00ff88;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 0 20px rgba(0,255,136,0.2);
        backdrop-filter: blur(10px);
        margin: 10px 0;
    }
    
    .metric-card {
        background: rgba(0,255,136,0.1);
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border: 1px solid rgba(0,255,136,0.3);
    }
    
    .stDataFrame {
        background: rgba(22, 33, 62, 0.8) !important;
        border-radius: 15px !important;
        border: 1px solid #00ff88 !important;
    }
    
    .stAlert {
        background: rgba(22, 33, 62, 0.8) !important;
        border: 1px solid #00ff88 !important;
        color: #00ff88 !important;
    }
    
    div[data-testid="stDecoration"] {
        background-image: linear-gradient(90deg, #00ff88, #00ccff) !important;
    }
    </style>
    """, unsafe_allow_html=True)





# Initialize session state
if 'history' not in st.session_state:
    st.session_state.history = []
if 'daily_goal' not in st.session_state:
    st.session_state.daily_goal = 2000

# Title and description 
st.markdown("""
    <div style="text-align: center; padding: 20px;">
        <h1 style='font-size: 3em; margin-bottom: 0;'>🔮 SmartBite AI</h1>
        <p style='color: #00ccff; font-family: Orbitron; margin-top: 10px;'>
            Advanced Calorie Detection System
        </p>
    </div>
""", unsafe_allow_html=True)


def main():
    load_dotenv()
    supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'page' not in st.session_state:
        st.session_state['page'] = 'login'
        login_page(supabase,cookie_deleter)
        st.rerun()

    # Check for persistent login cookie
    user_token = cookie_deleter.get(cookie_key)
    st.write(cookie_deleter)
    st.markdown(user_token)
    st.write(st.session_state)
    
    if user_token:
        try:
            response = supabase.auth.get_user(user_token)
            if response.user:
                st.session_state['user_id'] = response.user.id
                st.session_state['user_email'] = response.user.email
                st.session_state['logged_in'] = True
            else:
                st.session_state['logged_in'] = False
        except Exception:
            st.session_state['logged_in'] = False
            # cookie_setter.remove('user_token')
            cookie_deleter.delete(cookie_key)

    # Routing
    if not st.session_state['logged_in']:
        if st.session_state['page'] == 'login':
            login_page(supabase,cookie_deleter)  # Pass single cookie manager
        elif st.session_state['page'] == 'signup':
            signup_page(supabase)
    else:
        home_page()


if __name__ == '__main__':
    
    main()