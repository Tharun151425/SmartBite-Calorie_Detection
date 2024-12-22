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
from auth import login_page, signup_page
from streamlit_cookies_controller import CookieController
import extra_streamlit_components as stx


# Cookie manager for session handling
def get_cookie_manager():
    """Initialize and return a cookie manager with a unique key"""
    return stx.CookieManager()

cookie_setter = CookieController(key="user_token")
cookie_deleter= get_cookie_manager()



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
    st.sidebar.title(f"Welcome, {st.session_state['user_email']}!")
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
            "Show data for:",
            ["Last 24 Hours", "Last Week", "Last Month", "All Time"]
        )
    if st.sidebar.button("Logout"):
            st.session_state['logged_in'] = False
            st.session_state['page'] = 'login'
            cookie_deleter.delete('user_token')
            cookie_setter.remove('user_token')
            cookie_deleter.delete('user_token')
            st.rerun()

    # Main content
    col1, col2 = st.columns([1, 1])

    with col1:
        # st.markdown("<div class='result-box'>", unsafe_allow_html=True)
        st.markdown("<h2>📸 Image Analysis</h2>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Upload food image", type=["jpg", "jpeg", "png","webp"])
        
        if uploaded_file is not None:
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
                        img.empty()
                        img.image(output_image, caption="Output Image", use_container_width=True)
                        st.success("✨ Analysis Complete!")
                        # st.image(output_image, caption="Output Image", use_container_width=True)
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
            st.button("📥 Save Meal", key="save_meal")


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

