import streamlit as st
import requests
import datetime
import matplotlib.pyplot as plt
import pandas as pd
import os
from io import StringIO

# Set page config
st.set_page_config(page_title="Smart Irrigation Advisory", page_icon="🌾", layout="centered")
st.title("🌾 Smart Irrigation Advisory Dashboard")
st.write("Get irrigation advice based on real-time weather, soil conditions, and crop type.")

# --- Input Section ---
location = st.text_input("Enter your location (City/Village):", " ")
crop_type = st.selectbox("Select Crop Type:", ["Wheat", "Rice", "Cotton", "Sugarcane", "Maize", "Barley", "Soybean"])
soil_moisture = st.slider("Enter Soil Moisture Level (%):", 0, 100, 50)
language = st.selectbox("Select Language:", ["English", "Gujarati", "Hindi"])

# Language Dictionary (basic multilingual support)
translations = {
    "English": {
        "weather": "Weather Data",
        "temperature": "Temperature",
        "humidity": "Humidity",
        "rainfall": "Rainfall (last 1hr)",
        "condition": "Condition",
        "advice": "Irrigation Advice",
        "recommended": "Irrigation Recommended",
        "not_needed": "No Irrigation Needed",
        "saving_score": "Water Saving Score",
        "error_weather": "Unable to fetch weather data. Please check your location.",
        "error_api": "Weather service temporarily unavailable. Please try again later."
    },
    "Gujarati": {
        "weather": "હવામાન માહિતી",
        "temperature": "તાપમાન",
        "humidity": "ભેજ",
        "rainfall": "વર્ષા (છેલ્લા 1 કલાકમાં)",
        "condition": "હવામાન સ્થિતિ",
        "advice": "સિંચાઇ સલાહ",
        "recommended": "સિંચાઇ કરવાની ભલામણ છે",
        "not_needed": "સિંચાઇની જરૂર નથી",
        "saving_score": "પાણી બચાવ સ્કોર",
        "error_weather": "હવામાન માહિતી મેળવવામાં અસમર્થ. કૃપા કરીને તમારું સ્થાન તપાસો.",
        "error_api": "હવામાન સેવા અસ્થાયી રૂપે અનુપલબ્ધ છે. કૃપા કરીને ફરીથી પ્રયાસ કરો."
    },
    "Hindi": {
        "weather": "मौसम की जानकारी",
        "temperature": "तापमान",
        "humidity": "आर्द्रता",
        "rainfall": "वर्षा (पिछले 1 घंटे में)",
        "condition": "स्थिति",
        "advice": "सिंचाई सलाह",
        "recommended": "सिंचाई की सिफारिश की जाती है",
        "not_needed": "सिंचाई की आवश्यकता नहीं है",
        "saving_score": "जल बचत स्कोर",
        "error_weather": "मौसम डेटा प्राप्त करने में असमर्थ। कृपया अपना स्थान जांचें।",
        "error_api": "मौसम सेवा अस्थायी रूप से अनुपलब्ध है। कृपया बाद में पुनः प्रयास करें।"
    }
}

labels = translations[language]

# Enhanced crop-specific irrigation logic
crop_requirements = {
    "Wheat": {"min_moisture": 30, "temp_threshold": 25, "rain_threshold": 3},
    "Rice": {"min_moisture": 70, "temp_threshold": 30, "rain_threshold": 8},
    "Cotton": {"min_moisture": 35, "temp_threshold": 28, "rain_threshold": 5},
    "Sugarcane": {"min_moisture": 60, "temp_threshold": 32, "rain_threshold": 10},
    "Maize": {"min_moisture": 40, "temp_threshold": 26, "rain_threshold": 4},
    "Barley": {"min_moisture": 25, "temp_threshold": 24, "rain_threshold": 3},
    "Soybean": {"min_moisture": 45, "temp_threshold": 27, "rain_threshold": 6}
}

# OpenWeatherMap API Setup
api_key = st.secrets.get("OPENWEATHER_API_KEY", "c3189205c860439e4727a7a27fd77a7d")

# Initialize session state for logging
if 'irrigation_logs' not in st.session_state:
    st.session_state.irrigation_logs = []

def get_irrigation_advice(crop, soil_moisture, temp, humidity, rainfall):
    """Enhanced irrigation logic based on crop type and conditions"""
    req = crop_requirements.get(crop, crop_requirements["Wheat"])
    
    # Multiple factors for irrigation decision
    factors = {
        "low_moisture": soil_moisture < req["min_moisture"],
        "high_temp": temp > req["temp_threshold"],
        "low_rainfall": rainfall < req["rain_threshold"],
        "low_humidity": humidity < 40
    }
    
    # Decision logic
    irrigation_score = sum(factors.values())
    
    if irrigation_score >= 3:
        return True, "High Priority", 75
    elif irrigation_score >= 2:
        return True, "Medium Priority", 85
    else:
        return False, "Not Needed", 95

def log_irrigation_data(data):
    """Log irrigation data to session state"""
    st.session_state.irrigation_logs.append(data)

def export_logs():
    """Export logs as CSV"""
    if st.session_state.irrigation_logs:
        df = pd.DataFrame(st.session_state.irrigation_logs)
        return df.to_csv(index=False)
    return None

# --- Fetch Weather Data ---
if st.button("Get Irrigation Advice", type="primary"):
    if not location.strip():
        st.error("Please enter a valid location.")
    else:
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
        
        try:
            with st.spinner("Fetching weather data..."):
                response = requests.get(weather_url, timeout=10)
                response.raise_for_status()
                data = response.json()

            if data.get("cod") != 200:
                st.error(f"{labels['error_weather']}: {data.get('message', 'Unknown error')}")
            else:
                temp = data['main']['temp']
                humidity = data['main']['humidity']
                weather = data['weather'][0]['main']
                rainfall = data.get('rain', {}).get('1h', 0.0)

                # Weather display
                st.subheader(f"🌧️ {labels['weather']}")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(labels['temperature'], f"{temp}°C")
                    st.metric(labels['humidity'], f"{humidity}%")
                with col2:
                    st.metric(labels['rainfall'], f"{rainfall} mm")
                    st.metric(labels['condition'], weather)

                # Get irrigation advice
                irrigate, priority, water_score = get_irrigation_advice(
                    crop_type, soil_moisture, temp, humidity, rainfall
                )

                st.subheader(f"💧 {labels['advice']}")
                if irrigate:
                    st.success(f"{labels['recommended']} for {crop_type} - {priority}")
                    st.metric(labels['saving_score'], f"{water_score}%", 
                             delta=f"{priority}", delta_color="inverse")
                    result = labels['recommended']
                else:
                    st.info(f"{labels['not_needed']} for {crop_type}")
                    st.metric(labels['saving_score'], f"{water_score}%", 
                             delta="Optimal", delta_color="normal")
                    result = labels['not_needed']

                # Log data
                log_data = {
                    "datetime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "location": location,
                    "crop": crop_type,
                    "soil_moisture": soil_moisture,
                    "temperature": temp,
                    "humidity": humidity,
                    "rainfall": rainfall,
                    "weather": weather,
                    "irrigation": result,
                    "priority": priority if irrigate else "N/A"
                }
                log_irrigation_data(log_data)

                # Enhanced visualization
                st.subheader("📊 Analysis Dashboard")
                
                # Create tabs for different visualizations
                tab1, tab2, tab3 = st.tabs(["Conditions", "Forecast", "History"])
                
                with tab1:
                    # Current conditions chart
                    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
                    
                    # Moisture vs Requirement
                    req_moisture = crop_requirements[crop_type]["min_moisture"]
                    ax1.bar(['Current', 'Required'], [soil_moisture, req_moisture], 
                           color=['skyblue', 'lightcoral'])
                    ax1.set_ylabel('Soil Moisture (%)')
                    ax1.set_title('Soil Moisture Comparison')
                    ax1.axhline(y=req_moisture, color='red', linestyle='--', alpha=0.7)
                    
                    # Weather conditions
                    conditions = ['Temperature', 'Humidity', 'Rainfall']
                    values = [temp, humidity, rainfall * 10]  # Scale rainfall for visibility
                    ax2.bar(conditions, values, color=['orange', 'green', 'blue'])
                    ax2.set_ylabel('Values')
                    ax2.set_title('Current Weather Conditions')
                    
                    st.pyplot(fig)
                
                with tab2:
                    # Simulated forecast
                    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                    forecast_rain = [max(0, rainfall + (i-3)*0.5) for i in range(7)]
                    
                    fig, ax = plt.subplots(figsize=(10, 4))
                    bars = ax.bar(days, forecast_rain, color='skyblue', alpha=0.7)
                    ax.set_ylabel("Rainfall (mm)")
                    ax.set_title("7-Day Rainfall Forecast (Simulated)")
                    ax.axhline(y=crop_requirements[crop_type]["rain_threshold"], 
                              color='red', linestyle='--', alpha=0.7, 
                              label=f'{crop_type} Rain Threshold')
                    ax.legend()
                    
                    # Highlight today
                    bars[0].set_color('orange')
                    bars[0].set_alpha(1.0)
                    
                    st.pyplot(fig)
                
                with tab3:
                    # Show recent logs
                    if st.session_state.irrigation_logs:
                        recent_logs = st.session_state.irrigation_logs[-5:]  # Last 5 entries
                        df = pd.DataFrame(recent_logs)
                        st.dataframe(df, use_container_width=True)
                        
                        # Export functionality
                        csv_data = export_logs()
                        if csv_data:
                            st.download_button(
                                label="📥 Download Complete Log",
                                data=csv_data,
                                file_name=f"irrigation_log_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
                                mime="text/csv"
                            )
                    else:
                        st.info("No irrigation history available yet.")

        except requests.exceptions.Timeout:
            st.error(f"{labels['error_api']} (Timeout)")
        except requests.exceptions.ConnectionError:
            st.error(f"{labels['error_api']} (Connection Error)")
        except requests.exceptions.RequestException as e:
            st.error(f"{labels['error_api']}: {str(e)}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")

# Sidebar with additional information
with st.sidebar:
    st.header("📋 Crop Information")
    selected_crop = crop_requirements.get(crop_type, {})
    if selected_crop:
        st.write(f"**{crop_type} Requirements:**")
        st.write(f"• Min Soil Moisture: {selected_crop['min_moisture']}%")
        st.write(f"• Temperature Threshold: {selected_crop['temp_threshold']}°C")
        st.write(f"• Rain Threshold: {selected_crop['rain_threshold']}mm")
    
    st.header("🌍 About")
    st.write("This smart irrigation system helps optimize water usage for different crops based on real-time weather conditions.")
    
    if st.session_state.irrigation_logs:
        st.header("📊 Quick Stats")
        total_checks = len(st.session_state.irrigation_logs)
        irrigation_recommended = sum(1 for log in st.session_state.irrigation_logs 
                                   if log['irrigation'] != labels['not_needed'])
        st.metric("Total Checks", total_checks)
        st.metric("Irrigation Recommended", irrigation_recommended)
        if total_checks > 0:
            efficiency = ((total_checks - irrigation_recommended) / total_checks) * 100
            st.metric("Water Saving Efficiency", f"{efficiency:.1f}%")