import streamlit as st
import openai
import requests
import pandas as pd
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Retrieve sensitive keys from .env
openai.api_key = os.getenv("OPENAI_API_KEY")
FB_ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")
FB_AD_ACCOUNT_ID = os.getenv("FB_AD_ACCOUNT_ID")

# App Title
st.title("Facebook Target Audience Generator")
st.write("Provide brand details below to generate audience insights.")

# Input Fields
brand_info = st.text_input("Brand Information")
target_audience = st.text_area("Target Audience Description")
services = st.text_area("Type of Services Offered")
budget = st.number_input("Budget in THB", min_value=0)
location = st.text_input("Location / Country")
age_group = st.text_input("Age Group (e.g., 18-35)")
goals = st.text_area("Business Goals")

# Press Generate
if st.button("Generate"):
    with st.spinner("Analyzing inputs..."):
        # Combine inputs for LLM processing
        user_input = f"""
        Brand Information: {brand_info}
        Target Audience: {target_audience}
        Services: {services}
        Budget: {budget} THB
        Location: {location}
        Age Group: {age_group}
        Goals: {goals}
        """
        
        try:
            # Use OpenAI API to generate a marketing query
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a marketing assistant that generates queries for Facebook audience targeting."},
                    {"role": "user", "content": user_input}
                ]
            )
            llm_query = response['choices'][0]['message']['content']
            st.write("Generated Query:", llm_query)

            # Fetch data from Facebook Graph API
            st.write("Fetching data from Facebook Graph API...")
            url = f"https://graph.facebook.com/v14.0/{FB_AD_ACCOUNT_ID}/reachestimate"
            params = {
                "access_token": FB_ACCESS_TOKEN,
                "q": llm_query
            }
            fb_response = requests.get(url, params=params)

            if fb_response.status_code == 200:
                fb_data = fb_response.json()
                st.write("Data fetched successfully!")

                # Process Facebook API data
                csv_data = []
                for item in fb_data.get("data", []):
                    csv_data.append({
                        "name": item.get("name"),
                        "id": item.get("id"),
                        "type": item.get("type"),
                        "path": item.get("path"),
                        "audience_size": item.get("audience_size")
                    })
                df = pd.DataFrame(csv_data)
                st.write("Results:")
                st.dataframe(df)

                # Download CSV
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="audience_data.csv",
                    mime="text/csv",
                )
            else:
                st.error("Failed to fetch data from Facebook Graph API!")
                st.error(f"Error: {fb_response.json()}")

        except openai.error.OpenAIError as e:
            st.error(f"OpenAI API Error: {e}")
        except requests.exceptions.RequestException as e:
            st.error(f"Facebook API Request Error: {e}")
        except Exception as e: 
            st.error(f"An unexpected error occurred: {e}")
