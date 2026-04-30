import streamlit as st
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURATION ---
st.set_page_config(page_title="Portable Solutions Equipment Booking", layout="centered")

# PASTE YOUR GOOGLE SHEET LINK HERE:
SHEET_URL = "https://docs.google.com/spreadsheets/d/1lbOEvMT-5TjrMNqWiP_4qHAeL_zM0ghtNKngoTNEDVs/edit?usp=sharing"

# --- BRAND STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=League+Spartan:wght@300;400;600&family=Oswald:wght@600&display=swap');

    /* Deep Orange Background */
    .stApp, html, body {
        background-color: #FF5722 !important; 
    }
    
    /* Deep Navy Blue for ALL standard text */
    html, body, [class*="css"], p, span, div, label, li {
        font-family: 'League Spartan', sans-serif !important;
        color: #0A192F !important; 
    }
    
    /* Norwester Headings */
    .norwester-heading {
        font-family: 'Norwester', 'Oswald', sans-serif !important;
        text-transform: uppercase;
        color: #0A192F !important; 
        margin-bottom: 0.5rem;
        margin-top: 1rem;
    }
    
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
        color: #0A192F !important;
    }
    
    /* White Buttons with Navy Text */
    .stButton>button {
        font-family: 'League Spartan', sans-serif !important;
        font-weight: 800;
        background-color: #FFFFFF !important; 
        color: #0A192F !important; 
        border: 2px solid #0A192F !important;
        border-radius: 5px;
    }
    
    .stButton>button:hover {
        background-color: #0A192F !important;
        color: #FFFFFF !important;
        border-color: #FFFFFF !important;
    }

    /* White Features (Input Boxes and Dropdowns) */
    .stTextInput>div>div>input, 
    .stDateInput>div>div>input,
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] {
        background-color: #FFFFFF !important; 
        color: #0A192F !important;
        border: 1px solid #0A192F !important;
        border-radius: 5px;
    }

    /* Selected Gear Bubbles: Deep Navy with White Text */
    span[data-baseweb="tag"] {
        background-color: #0A192F !important;
        color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)

# --- LOGO DISPLAY ---
# This centers the image beautifully at the top
colA, colB, colC = st.columns([1, 4, 1])
with colB:
    try:
        st.image("logo.png", use_container_width=True) 
    except:
        pass

# --- LIVE GOOGLE SHEETS CONNECTION ---
def get_live_sheet():
    creds_dict = json.loads(st.secrets["GCP_JSON"])
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(SHEET_URL).sheet1
    return sheet

@st.cache_data(ttl=30) 
def load_inventory():
    sheet = get_live_sheet()
    data = sheet.get_all_values()
    df = pd.DataFrame(data[3:], columns=data[2])
    return df

try:
    inventory_df = load_inventory()
except Exception as e:
    st.error(f"Could not connect to Google Sheets. Please ensure your SHEET_URL is correct. Error: {e}")
    st.stop()

# --- PACKAGE MAPPING ---
PACKAGE_MAP = {
    "800W Power Station & 200W Solar Blanket Package": ["PS800 Power station", "200w Solar Blanket"],
    "1800W Power Station & 360W Solar Blanket Package": ["PS1800PRO Power station", "360w solar blanket"],
    "1800W Expanded & 360W Solar Blanket Package (Double Capacity)": ["PS1800PRO Power station", "EB1536 Expansion pack", "360w solar blanket"],
    "2000W Power Station & 360W Solar Blanket Package": ["PS2000w Power station", "360w solar blanket"],
    "75L Fridge/Freezer (Kings)": ["K 75L FF"],
    "75L Fridge/Freezer (Brass Monkey)": ["BM 75L FF"],
    "40L Fridge/Freezer": ["K40LFF"],
    "Air Compressor": ["ItechAC"],
    "Magnetic Light Bar": ["300Lm Magnetic Light bar"]
}

# --- EMAIL FUNCTION ---
def send_confirmation_email(customer_name, customer_email):
    if "EMAIL_USER" not in st.secrets or "EMAIL_PASS" not in st.secrets:
        return
    sender_email = st.secrets["EMAIL_USER"]
    sender_password = st.secrets["EMAIL_PASS"]
    msg = MIMEMultipart()
    msg['From'] = f"Portable Solutions <{sender_email}>"
    msg['To'] = customer_email
    msg['Subject'] = "Booking Request - Portable Solutions"
    body = f"""Hi {customer_name},

Thank you for your booking with Portable Solutions! Your items have been placed on temporary hold for you. You will be sent a payment link in the next 24hrs to confirm the booking. 

Please email us or message us on Facebook for any questions you may still have about the equipment or the hire, we are always happy to help.

Stay charged,
The Portable Solutions Team
"""
    msg.attach(MIMEText(body, 'plain'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587) 
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, customer_email, text)
        server.quit()
    except Exception as e:
        pass

# --- FRONT END APP ---
# Title simplified
st.markdown("<div class='norwester-heading main-title'>Equipment Booking</div>", unsafe_allow_html=True)
st.write("Confirm Availability and Place a hold on your gear! Availability is based on a first to pay basis. Please Complete the Customer Hire Agreement and Hire Terms below, your gear will then be placed on temporary hold for you for 24 hours. Shortly after completing the Hire Agreement you will be sent a Payment link to confirm the booking.")
st.divider()

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
        st.success(f"**Total Hire Duration:** {hire_days} days")
        
        selected_packages = st.multiselect("Select Equipment (Choose as many as you need):", list(PACKAGE_MAP.keys()))
        
        if selected_packages:
            has_solar = any("200W Solar Blanket" in pkg or "360W Solar Blanket" in pkg for pkg in selected_packages)
            remove_solar = False
            if has_solar:
                remove_solar = st.checkbox("Remove Solar Blanket(s) from my selected power stations", value=False)
            
            required_items = []
            for pkg in selected_packages:
                items = PACKAGE_MAP[pkg].copy()
                if remove_solar:
                    items = [i for i in items if i.lower() not in ["200w solar blanket", "360w solar blanket"]]
                required_items.extend(items)
            
            missing_items = []
            available_units = [] 
            booked_unit_ids = set() 
            
            for item in required_items:
                matches = inventory_df[
                    (inventory_df["Current Status"] == "In Stock") & 
                    (inventory_df["Model/Description"].str.lower() == item.lower()) &
                    (~inventory_df["Unit ID"].isin(booked_unit_ids))
                ]
                
                if matches.empty:
                    missing_items.append(item)
                else:
                    unit_id = matches.iloc[0]["Unit ID"]
                    booked_unit_ids.add(unit_id)
                    available_units.append((item, unit_id))
            
            if missing_items:
                st.warning(f"Sorry, your current combination is unavailable for these dates. We are out of stock for: {', '.join(missing_items)}")
            else:
                st.info("✓ All selected equipment is available!")
                
                with st.form("booking_form"):
                    st.markdown("<h3 class='norwester-heading'>Customer Details</h3>", unsafe_allow_html=True)
                    name = st.text_input("Full Name")
                    email = st.text_input("Email Address")
                    
                    st.divider()
                    st.markdown("<h3 class='norwester-heading'>Hire Agreement Verification</h3>", unsafe_allow_html=True)
                    st.markdown("Step 1. Click here to complete the **[Customer Hire Agreement](https://docs.google.com/forms/d/e/1FAIpQLSd2bfpED_4WQzpkR4BYuIfpc9V8V_GfKohniY83F-A3bSIMzw/viewform?usp=header)**.")
                    st.markdown("Step 2. After clicking submit on the agreement, copy the confirmation code shown on the screen and paste it below.")
                    
                    agreement_code = st.text_input("Confirmation Code")
                    submit = st.form_submit_button("Place on Hold")
                    
                    if submit:
                        if agreement_code.strip().upper() != "PS-HIRE-24":
                            st.error("Invalid Code. You must complete the Customer Hire Agreement to receive the correct confirmation code.")
                        elif name and email:
                            # --- WRITE TO GOOGLE SHEETS LIVE ---
                            try:
                                live_sheet = get_live_sheet()
                                for item, unit_id in available_units:
                                    cell = live_sheet.find(unit_id)
                                    live_sheet.update_cell(cell.row, 4, "Booked")
                                    live_sheet.update_cell(cell.row, 5, end_date.strftime("%d/%m/%Y"))
                                
                                st.cache_data.clear()
                                
                                st.success("Gear Placed on Hold!")
                                st.markdown("<p class='norwester-heading' style='font-size: 1.1rem;'>The following specific units have been temporarily reserved for you:</p>", unsafe_allow_html=True)
                                
                                for item, unit_id in available_units:
                                    st.write(f"- {item} (Unit ID: {unit_id})")
                                    
                                st.write("We will review your Hire Agreement and send a payment link to your email shortly.")
                                
                                # --- CUSTOM SUN GLOW ANIMATION ---
                                st.markdown("""
                                <style>
                                    .sun-glow-orb {
                                        position: fixed;
                                        top: -150px;
                                        left: 50%;
                                        margin-left: -150px;
                                        width: 300px;
                                        height: 300px;
                                        background: radial-gradient(circle, rgba(255,223,0,1) 0%, rgba(255,140,0,0.8) 40%, rgba(255,87,34,0) 70%);
                                        border-radius: 50%;
                                        z-index: 99999;
                                        pointer-events: none;
                                        animation: riseAndGlow 3.5s ease-in-out forwards;
                                    }
                                    @keyframes riseAndGlow {
                                        0% { top: -150px; opacity: 0; transform: scale(0.5); }
                                        30% { top: -50px; opacity: 1; transform: scale(1.5); box-shadow: 0 0 250px 150px rgba(255, 200, 0, 0.5); }
                                        70% { top: -50px; opacity: 1; transform: scale(1.5); box-shadow: 0 0 250px 150px rgba(255, 200, 0, 0.5); }
                                        100% { top: -250px; opacity: 0; transform: scale(2); }
                                    }
                                    .page-glow-overlay {
                                        position: fixed;
                                        top: 0; left: 0; right: 0; bottom: 0;
                                        background-color: rgba(255, 220, 100, 0.2);
                                        z-index: 99998;
                                        pointer-events: none;
                                        animation: flashGlow 3.5s ease-in-out forwards;
                                    }
                                    @keyframes flashGlow {
                                        0% { opacity: 0; }
                                        30% { opacity: 1; }
                                        70% { opacity: 1; }
                                        100% { opacity: 0; }
                                    }
                                </style>
                                <div class="sun-glow-orb"></div>
                                <div class="page-glow-overlay"></div>
                                """, unsafe_allow_html=True)
                                
                                send_confirmation_email(name, email)
                            
                            except Exception as e:
                                st.error(f"There was an issue communicating with Google Sheets. Error: {e}")
                                
                        else:
                            st.error("Please fill out your Name and Email Address to receive your booking confirmation.")
