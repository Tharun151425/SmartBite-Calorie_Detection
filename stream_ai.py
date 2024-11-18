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


#  page configuration
st.set_page_config(
    page_title="SmartBite AI",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)
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

@st.cache_data()


# Helper function for creating animated metrics
def create_metric_card(title, value, prefix="", suffix=""):
    st.markdown(f"""
        <div class="metric-card">
            <h3 style="margin:0; font-size:0.8em; color:#00ccff;">{title}</h3>
            <p style="margin:0; font-size:1.5em; color:#00ff88;">{prefix}{value}{suffix}</p>
        </div>
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

# Sidebar for settings
with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>⚙️ Controls</h2>", unsafe_allow_html=True)
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
        "Show data for:",
        ["Last 24 Hours", "Last Week", "Last Month", "All Time"]
    )

# Main content
col1, col2 = st.columns([1, 1])

with col1:
    # st.markdown("<div class='result-box'>", unsafe_allow_html=True)
    st.markdown("<h2>📸 Image Analysis</h2>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload food image", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_container_width=True)
        
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

                    # Loop through the parsed JSON data
                    for i in range(len(json_data)):
                        food_name = json_data[i]['food_name']  # Get the food name
                        confidence = json_data[i]['confidence']  # Get the confidence score

                        #TODO: Add calorie lookup based on food name
                        calories = 100
                        meal_calories += calories

                        # Add the food item to the result list 
                        result.append({
                            "food": food_name,
                            "calories": calories,  
                            "portion": "1 serving",  # Dummy portion value for now
                            "confidence": confidence  # Confidence percentage
                        })


                    # Append to session history 
                    st.session_state.history.append({
                        "timestamp": datetime.now(),
                        "foods": result,
                        'total_calories': st.session_state.history[-1]['total_calories']+meal_calories if st.session_state.history else meal_calories,
                        'meal_calories': meal_calories
                    })

                    st.success("✨ Analysis Complete!")
                    st.image(output_image, caption="Output Image", use_container_width=True)
                    os.remove(temp_image_path)
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    # st.markdown("<div class='result-box'>", unsafe_allow_html=True)
    st.markdown("<h2>📊 Latest Analysis</h2>", unsafe_allow_html=True)
    
    if st.session_state.history:
        latest = st.session_state.history[-1]
        
        # Create metrics row
        metrics_cols = st.columns(2)
        with metrics_cols[0]:
            create_metric_card("Total Calories", latest["total_calories"], suffix=" kcal")
        with metrics_cols[1]:
            remaining = st.session_state.daily_goal - latest["total_calories"]
            if remaining < 0:
                create_metric_card("Extra Calories Today", abs(remaining), suffix=" kcal")
            else:
                create_metric_card("Remaining Today", remaining, suffix=" kcal")
        
        # Detected foods with confidence
        st.markdown("### 🍽️ Detected Items")
        for food in latest["foods"]:
            confidence_color = f"rgb({int(255*(1-food['confidence']))}, {int(255*food['confidence'])}, 0)"
            st.markdown(f"""
                <div style="padding: 10px; margin: 5px 0; background: rgba(0,255,136,0.1); border-radius: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="color: #00ff88;">{food['food']}</span>
                        <span style="color: {confidence_color};">{int(food['confidence']*100)}% confident</span>
                    </div>
                    <div style="color: #00ccff; font-size: 0.9em;">
                        {food['calories']} kcal per {food['portion']}
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("👆 Upload an image to start analysis")
    st.markdown("</div>", unsafe_allow_html=True)

# Visualizations
st.markdown("---")
st.markdown("<h2>📈 Analytics Dashboard</h2>", unsafe_allow_html=True)

if st.session_state.history:
    # Create sample data for last 7 days
    vis_cols = st.columns([2, 1])
    
    with vis_cols[0]:
        # st.markdown("<div class='result-box'>", unsafe_allow_html=True)
        
        # Calorie Trend Chart
        df_history = pd.DataFrame([
            {
                "Time": entry["timestamp"],
                "Calories": entry["total_calories"]
            }
            for entry in st.session_state.history
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
        if st.session_state.history:
            labels = []
            values = []
            for latest in st.session_state.history:
                for food in latest["foods"]:
                    labels.append(food["food"])
                    values.append(food["calories"])


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

# Function to filter history based on the selected time filter
def filter_history_by_time(history, time_filter):
    current_time = datetime.now()
    
    if time_filter == "Last 24 Hours":
        # Filter entries from the last 24 hours
        time_threshold = current_time - timedelta(days=1)
    elif time_filter == "Last Week":
        # Filter entries from the last 7 days
        time_threshold = current_time - timedelta(weeks=1)
    elif time_filter == "Last Month":
        # Filter entries from the last 30 days
        time_threshold = current_time - timedelta(days=30)
    else:
        # "All Time" option - no filtering needed
        return history
    
    # Filter the history based on the timestamp
    filtered_history = [entry for entry in history if entry["timestamp"] >= time_threshold]
    return filtered_history

# History Table
st.markdown("---")
st.markdown("<h2>📜 Analysis History</h2>", unsafe_allow_html=True)

# Filter history based on the selected time filter
filtered_history = filter_history_by_time(st.session_state.history, time_filter)

if filtered_history:
    history_df = pd.DataFrame([
        {
            "Time": entry["timestamp"].strftime("%Y-%m-%d %H:%M"),
            "Meal Calories": entry["meal_calories"],
            "Foods Detected": ", ".join([f"{food['food']} ({food['calories']} kcal)" for food in entry["foods"]])
        }
        for entry in filtered_history[::-1]  # Reverse to display most recent first
    ])
    st.dataframe(history_df, use_container_width=True)
else:
    st.info("No analysis history available for the selected filter. Upload an image to get started!")


# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #00ccff; font-family: Orbitron;'>SmartBite AI © 2024</p>",
    unsafe_allow_html=True
)