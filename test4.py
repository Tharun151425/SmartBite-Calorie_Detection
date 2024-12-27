import streamlit as st
import requests
from PIL import Image
import io
import json
from datetime import datetime, timedelta
from dateutil import parser
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
import time
from dotenv import load_dotenv
from supabase import create_client, Client
import extra_streamlit_components as stx

from ai_model import food_detect
from api_info import *




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





if 'history' not in st.session_state:
    st.session_state.history = []

if 'daily_goal' not in st.session_state:
    st.session_state.daily_goal = 2000

# Initialize total calories from Daily table
if 'user_id' in st.session_state:
    try:
        today_date = todays_date()
        user_id = st.session_state['user_id']
        total_calories = get_cal_consumed(supabase,user_id, today_date)
        
        # Add initial entry to history if it's empty
        if not st.session_state.history:
            st.session_state.history.append({
                "timestamp": datetime.now(),
                "foods": [],
                "total_calories": total_calories,
                "meal_calories": 0
            })
    except Exception as e:
        st.error(f"Error initializing total calories: {str(e)}")


# Title and description 
st.markdown("""
    <div style="text-align: center; padding: 20px;">
        <h1 style='font-size: 3em; margin-bottom: 0;'>🔮 SmartBite AI</h1>
        <p style='color: #00ccff; font-family: Orbitron; margin-top: 10px;'>
            Advanced Calorie Detection System
        </p>
    </div>
""", unsafe_allow_html=True)




def login_page(supabase: Client):
    
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





# Helper function for creating animated metrics
def create_metric_card(title, value, prefix="", suffix=""):
    st.markdown(f"""
        <div class="metric-card">
            <h3 style="margin:0; font-size:0.8em; color:#00ccff;">{title}</h3>
            <p style="margin:0; font-size:1.5em; color:#00ff88;">{prefix}{value}{suffix}</p>
        </div>
    """, unsafe_allow_html=True)




def home_page():

    # Sidebar for settings
    st.sidebar.title(f"Welcome, {st.session_state['user_email'].split('@')[0]}!")
    with st.sidebar:
        st.markdown("<h2 >⚙️ Controls</h2>", unsafe_allow_html=True)
        st.session_state.daily_goal = st.slider(
            "Daily Calorie Goal",
            min_value=1000,
            max_value=4000,
            value=st.session_state.daily_goal,
            step=100
        )
        
        # Add time filter for history
        st.markdown("### 📅 History Filter")
        time_filter = st.selectbox(
            "Show data from:",
            ["Last 24 Hours", "Last Week", "Last Month", "All Time"]
        )
    if st.sidebar.button("Logout"):
            # st.session_state['logged_in'] = False
            # st.session_state['page'] = 'login'
            # st.session_state['user_id'] = None
            # st.session_state['user_email'] = None
            st.session_state.clear()
            st.rerun()

    # Main content
    col1, col2 = st.columns([1, 1])

 
    with col1:
        # st.markdown("<div class='result-box'>", unsafe_allow_html=True)
        st.markdown("<h2>📸 Image Analysis</h2>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Upload food image", type=["jpg", "jpeg", "png","webp"])
        initital=st.info("👆 Upload an image to start analysis")
     

        if uploaded_file is not None:
            initital.empty()
            image = Image.open(uploaded_file)
            img=st.image(image, caption="Uploaded Image", use_container_width=True)
            
            if st.button("🔍 Analyze Food", key="analyze"):
                with st.spinner("🔮 AI Analysis in Progress..."):
                    try:
                        # Save the uploaded file temporarily
                        temp_image_path = "temp_image.jpg"
                        image.save(temp_image_path)

                        json_out,output_image = food_detect(temp_image_path)

                        json_data = json.loads(json_out)

                        result = []
                        meal_calories = 0
                        seen = []

                        # Loop through the parsed JSON data
                        for i in range(len(json_data)):
                            food_name = json_data[i]['food_name']  # Get the food name
                            confidence = json_data[i]['confidence']  # Get the confidence score
                            if food_name not in seen:
                                seen.append(food_name)
                                #TODO: Add calorie lookup based on food name
                                calories = 100
                                meal_calories += calories

                                # Add the food item to the result list 
                                result.append({
                                    "food": food_name,
                                    "calories": calories,  
                                    "portion": "1 serving",  # TODO:Dummy portion value for now
                                    "confidence": confidence  # Confidence percentage
                                })


                        # Append to session history 
                        st.session_state.history.append({
                            "timestamp": datetime.now(),
                            "foods": result,
                            'total_calories': st.session_state.history[-1]['total_calories']+meal_calories if st.session_state.history else meal_calories,
                            'meal_calories': meal_calories
                        })

                        
                        img.empty()
                        img.image(output_image, caption="Output Image", use_container_width=True)
                        st.success("✨ Analysis Complete!")
                        # st.image(output_image, caption="Output Image", use_container_width=True)
                        os.remove(temp_image_path)
                        
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        st.markdown("</div>", unsafe_allow_html=True)


    if 'meal_just_saved' not in st.session_state:
        st.session_state.meal_just_saved = False

    with col2:
        # st.markdown("<div class='result-box'>", unsafe_allow_html=True)
        st.markdown("<h2>📊 Latest Analytics</h2>", unsafe_allow_html=True)

        latest = get_latest_daily_data(supabase,st.session_state['user_id'])
        
        metrics_cols = st.columns(2)
        with metrics_cols[0]:
            create_metric_card("Total Calories Consumed", latest["cal_consumed"], suffix=" kcal")
            create_metric_card("Calories Burnt", latest["cal_burnt"], suffix=" kcal")

        with metrics_cols[1]:
            # Replace daily goal with a predefined constant or a user-specific value
            daily_goal = st.session_state.daily_goal
            remaining = daily_goal - latest["cal_consumed"]
            if remaining < 0:
                create_metric_card("Extra Calories Today", abs(remaining), suffix=" kcal")
            else:
                create_metric_card("Remaining Today", remaining, suffix=" kcal")
            
            # create_metric_card("Steps Today", latest["steps"])


        if (st.session_state.history and len(st.session_state.history[-1]['foods']) > 0 and not st.session_state.meal_just_saved):

            # Detected foods with confidence
            st.markdown("### 🍽️ Detected Items")

            latest = st.session_state.history[-1]
            
            for food in latest['foods']:
                confidence_color = f"rgb({int(255*(1-food['confidence']))}, {int(255*food['confidence'])}, 0)"
                st.markdown(f"""
                    <div style="padding: 10px; margin: 5px 0; background: rgba(0,255,136,0.1); border-radius: 10px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="color: #00ff88;">{food['food']}</span>
                            <select id="{food['food']}_unit" style="padding: 5px; border-radius: 5px; border: 1px solid #ccc;">
                                <option value="servings">Servings</option>
                                <option value="grams">Grams</option>
                                <option value="pieces">Pieces</option>
                            </select>
                            <input type="number" id="{food['food']}_quantity" style="margin-left: 10px;" />
                            <input type="checkbox" id="{food['food']}_checkbox" style="margin-left: 10px;" />
                    </div>
                        <div style="color: #00ccff; font-size: 0.9em;">
                            {food['calories']} kcal per {food['portion']}
                        </div>
                            <div style="color: {confidence_color};">{int(food['confidence']*100)}% confident</div>
                    </div>
            """, unsafe_allow_html=True)
            print("Meal saved successfully!")
            if st.button("📥 Save Meal", key="save_meal"):
                
                try:
                    # Ensure the user is logged in and has a valid user_id
                    user_id = st.session_state.get('user_id')
                    if not user_id:
                        st.error("You must be logged in to save meals.")
                        st.stop()

                    # Ensure there is a latest analysis to save
                    if not st.session_state.history:
                        st.error("No meal detected to save.")
                        st.stop()

                    latest = st.session_state.history[-1]
                    today_date = todays_date()

                    foods_detect=st.session_state.history[-1]["foods"]
                    foods_detected = [f"{item['food']}:{item['calories']}kcal" for item in foods_detect]

                    # Insert the meal into the database
                    new_meal_insert(
                        supabase=supabase,
                        user_id=user_id,
                        today_date=today_date,
                        meal_cal=latest['meal_calories'],
                        foods_detected=foods_detected
                    )

                    # Fetch the updated total calories for the day
                    updated_calories = get_cal_consumed(supabase,user_id, today_date)

                    # Update the Total Calories metric dynamically
                    latest['total_calories'] = updated_calories
                    st.session_state.history[-1] = latest

                    st.session_state.meal_just_saved = True

                    meal_saved=st.success("Meal saved successfully!")
                    time.sleep(2)
                    meal_saved.empty()
                    st.rerun()  # Refresh the UI to show updated values

                except Exception as e:
                    st.error(f"Error saving meal: {str(e)}")

            else:
                
                st.markdown("</div>", unsafe_allow_html=True)

            if 'analyze' in st.session_state and st.session_state.analyze:
                st.session_state.meal_just_saved = False

    # Visualizations
    st.markdown("---")
    st.markdown("<h2>📈 Analytics Dashboard</h2>", unsafe_allow_html=True)


    def fetch_meal_history_last_24_hours(user_id):
        last_24_hours = datetime.now() - timedelta(days=1)
        result = (
            supabase.table("Meals")
            .select("timestamp, meal_cal")
            .eq("user_id", user_id)
            .gte("timestamp", last_24_hours.isoformat())  # Filter for the last 24 hours
            .order("timestamp", desc=True)  # Order by latest first
            .execute()
        )
        return result.data
    


    meal_history = fetch_meal_history_last_24_hours(st.session_state['user_id'])
    

    if meal_history:
        # Create sample data for last 7 days
        vis_cols = st.columns([2, 1])
        
        with vis_cols[0]:
            # st.markdown("<div class='result-box'>", unsafe_allow_html=True)
            
            # Calorie Trend Chart
            df_history = pd.DataFrame([
                {
                "Time": pd.to_datetime(entry["timestamp"]),
                "Calories": entry["meal_cal"]
                }
                for entry in meal_history
            ])
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_history["Time"],
                y=df_history["Calories"],
                mode='lines+markers',
                name='Calories',
                line=dict(color='#00ff88', width=2),
                marker=dict(size=8, symbol='diamond')
            ))
            
            # Add daily goal line
            fig.add_trace(go.Scatter(
                x=df_history["Time"],
                y=[st.session_state.daily_goal] * len(df_history),
                mode='lines',
                name='Daily Goal',
                line=dict(color='#00ccff', width=2, dash='dash')
            ))
            
            fig.update_layout(
                title="Calorie Intake Trend",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#00ff88'),
                xaxis=dict(showgrid=True, gridcolor='rgba(0,255,136,0.1)'),
                yaxis=dict(showgrid=True, gridcolor='rgba(0,255,136,0.1)'),
                legend=dict(
                    bgcolor='rgba(0,0,0,0)',
                    bordercolor='#00ff88'
                )
            )
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with vis_cols[1]:
            # Calorie Distribution Pie Chart


            def fetch_meal_history_last_24_hours(user_id):
                last_24_hours = datetime.now() - timedelta(days=1)
                result = (
                    supabase.table("Meals")
                    .select("timestamp,foods_detected,meal_cal")
                    .eq("user_id", user_id)
                    .gte("timestamp", last_24_hours.isoformat())  # Filter for the last 24 hours
                    .order("timestamp", desc=True)  # Order by latest first
                    .execute()
                )
                return result.data
    


            meal_history = fetch_meal_history_last_24_hours(st.session_state['user_id'])
            food_chart=[foods["foods_detected"] for foods in meal_history]


            if food_chart:
                labels = []
                values = []
                for sublist in food_chart:
                    for item in sublist:
                        # Split each item by the colon to separate the food name and calorie count
                        food_name, calorie_str = item.split(':')
                        # Remove the 'kcal' part and convert the calorie value to an integer
                        calories = int(calorie_str.replace('kcal', ''))
                        # Append the food name and calorie value to the respective lists
                        labels.append(food_name)
                        values.append(calories)


                # latest = st.session_state.history
                # st.markdown(latest)
                # foods = latest["foods"]
                
                fig = go.Figure(data=[go.Pie(
                    labels=labels,
                    values=values,
                    hole=.3,
                    marker=dict(colors=['#00ff88', '#00ccff'])
                )])
                
                fig.update_layout(
                    title="Calorie Distribution",
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#00ff88'),
                    showlegend=True,
                    legend=dict(
                        bgcolor='rgba(0,0,0,0)',
                        bordercolor='#00ff88'
                    )
                )
                st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No meal history available for the last 24 hours.")

    # Function to filter history based on the selected time filter
    def get_meal_history(supabase, user_id, time_filter):
        current_time = datetime.now()
        
        if time_filter == "Last 24 Hours":
            time_threshold = current_time - timedelta(days=1)
        elif time_filter == "Last Week":
            time_threshold = current_time - timedelta(weeks=1)
        elif time_filter == "Last Month":
            time_threshold = current_time - timedelta(days=30)
        else:  # "All Time"
            time_threshold = datetime.min
        
        results = supabase.table('Meals') \
            .select('timestamp, meal_cal, foods_detected') \
            .eq('user_id', user_id) \
            .gte('timestamp', time_threshold.isoformat()) \
            .order('timestamp', desc=True) \
            .execute()
        
        return results.data

    # History Table
    st.markdown("---")
    st.markdown("<h2>📜 Analysis History</h2>", unsafe_allow_html=True)

    # Filter history based on the selected time filter
    filtered_history = get_meal_history(supabase, st.session_state["user_id"], time_filter)



    if filtered_history:
        history_df = pd.DataFrame([
            {
                "Time": parser.isoparse(entry["timestamp"]).strftime("%Y-%m-%d %H:%M:%S"),
                "Meal Calories": entry["meal_cal"],
                "Foods Detected": ", ".join(i for i in entry["foods_detected"] or [])
            }
            for entry in filtered_history[::-1]  # Reverse to display most recent first
        ])
        history_df.index = range(1, len(history_df) + 1)
        st.dataframe(history_df, use_container_width=True)
    else:
        st.info("No analysis history available for the selected filter. Upload an image to get started!")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #00ccff; font-family: Orbitron;'>SmartBite AI © 2024</p>",
        unsafe_allow_html=True
    )



def main():

    
    load_dotenv()
    supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'page' not in st.session_state:
        st.session_state['page'] = 'login'

    
    user_token = None
    #st.markdown(user_token)
    #st.write(st.session_state)
    
    
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
            
            

    # Routing
    if not st.session_state['logged_in']:
        if st.session_state['page'] == 'login':
            login_page(supabase)  
        elif st.session_state['page'] == 'signup':
            signup_page(supabase)
    else:
        home_page()


if __name__ == '__main__':
    
    main()