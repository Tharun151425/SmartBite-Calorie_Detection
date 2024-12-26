from supabase import create_client
from datetime import datetime, timezone
import pytz
import os
from dotenv import load_dotenv
from supabase import Client


def timestampz():
    ist = pytz.timezone("Asia/Kolkata")
    return datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S.%f')[:-1] + '+00'

def todays_date():
    return datetime.today().strftime("%Y-%m-%d")


def get_data(supabase:Client,table_name: str) -> list:
    try:
        response = supabase.table(table_name).select("*").execute()
        return response
    except Exception as e:
        raise ValueError(f"Error fetching data from {table_name}: {str(e)}")

def get_cal_consumed(supabase:Client,user_id: str, today_date: str) -> int:
    try:
        calories_data = (
            supabase.table("Daily")
            .select("cal_consumed")
            .eq("user_id", user_id)
            .eq("date", today_date)
            .execute()
        )
        print(f"Raw response: {calories_data.data}")
        if calories_data.data and len(calories_data.data) > 0:
            cal_value = calories_data.data[0]["cal_consumed"]
            print(f"Found calorie value: {cal_value}")
            return cal_value
        return 0
    except Exception as e:
        print(f"Error in get_cal_consumed: {str(e)}")
        raise ValueError(f"Error fetching cal_consumed: {str(e)}")

def ensure_daily_entry(supabase:Client,user_id: str, today_date: str):
    try:
        response = supabase.table("Daily").select("*").eq("user_id", user_id).eq("date", today_date).execute()
        if not response.data:
            supabase.table("Daily").insert({
                "user_id": user_id,
                "date": today_date,
                "cal_consumed": 0,
                "cal_burnt": 0,
                "steps": 0,
                "distance": 0.0
            }).execute()
            print(f"Inserted new row in Daily for user_id={user_id} and date={today_date}")
    except Exception as e:
        raise ValueError(f"Error ensuring Daily entry: {str(e)}")

def new_meal_insert(supabase:Client,user_id, today_date, meal_cal, foods_detected):
    try:
        # Ensure Daily entry exists
        ensure_daily_entry(supabase,user_id, today_date)

        # Insert into Meals
        response = supabase.table("Meals").insert({
            "user_id": user_id,
            "date": today_date,
            "timestamp": timestampz(),
            "meal_cal": meal_cal,
            "foods_detected": foods_detected
        }).execute()

        print(f"Response from Meals insert: {response}")

        # Update cal_consumed in Daily
        if response: # Ensure Meals insert succeeded
            daily_data = (
                supabase.table("Daily")
                .select("cal_consumed")
                .eq("user_id", user_id)
                .eq("date", today_date)
                .execute()
            )
            
            if daily_data.data:
                current_calories = daily_data.data[0]["cal_consumed"]
                updated_calories = current_calories + meal_cal
                
                # Update cal_consumed in Daily table
                supabase.table("Daily").update({
                    "cal_consumed": updated_calories
                }).eq("user_id", user_id).eq("date", todays_date()).execute()
            else:
                raise ValueError("Failed to fetch current cal_consumed from Daily table.")
    except Exception as e:
        raise ValueError(f"Error inserting new meal: {str(e)}")

    
def get_user_data(supabase:Client,user_id: str) -> dict:

    try:
        response = (
            supabase.table("Daily")
            .select("*").eq("user_id", user_id)
            .execute()
        )
        if response.data and len(response.data) > 0:
            return response.data[0]
        return {}
    except Exception as e:
        raise ValueError(f"Error fetching user data: {str(e)}")

def get_latest_daily_data(supabase:Client,user_id):
    today = todays_date()
    result = (
        supabase.table("Daily")
        .select("*")
        .eq("user_id", user_id)
        .eq("date", today)
        .execute()
    )
    if result.data:
        return result.data[0]  # Return the first record (there should only be one)
    else:
        # If no record for today, return default data
        return {
            "cal_consumed": 0,
            "cal_burnt": 0,
            "steps": 0,
            "distance": 0.0,
        }