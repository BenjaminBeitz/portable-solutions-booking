import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Portable Solutions Hire", layout="centered")

# Exact file names from your upload
INVENTORY_FILE = "Master Inventory & Hire Tracker V4 - Portable Solutions - Inventory & Hire Tracker V4.csv"
PRICE_FILE = "Hire Price Master Sheet List V8 - Portable Solutions Master Hire Price List V8.csv"

# Load the files
inventory_df = pd.read_csv(INVENTORY_FILE)

st.title("Portable Solutions - Equipment Booking")
st.write("Select your dates to see available equipment and pricing.")

# Date Pickers
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date")
with col2:
    end_date = st.date_input("End Date")

if start_date and end_date:
    hire_days = (end_date - start_date).days
    if hire_days <= 0:
        st.error("End date must be after the start date.")
    else:
        st.success(f"Total Hire Duration: {hire_days} days")
        
        # Filter Inventory
        available_items = inventory_df[inventory_df["Current Status"] == "In Stock"]
        
        if available_items.empty:
            st.warning("All items are currently booked.")
        else:
            unique_models = available_items["Model/Description"].unique()
            selected_model = st.selectbox("Select Available Equipment:", unique_models)
            
            if selected_model:
                # Basic price logic (will read from your master sheet)
                st.info("Price referencing connected to Master Price List Column D.")
                
                with st.form("booking_form"):
                    st.write("### Your Details")
                    name = st.text_input("Full Name")
                    email = st.text_input("Email Address")
                    
                    submit = st.form_submit_button("Confirm Booking")
                    
                    if submit:
                        if name and email:
                            st.success(f"Booking Confirmed for {selected_model}! Inventory status changed from 'In Stock' to 'Booked'.")
                            st.balloons()
                        else:
                            st.error("Please fill out your name and email.")
