import streamlit as st
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIGURATION ---
st.set_page_config(page_title="Portable Solutions Equipment Booking", layout="centered")

INVENTORY_FILE = "inventory.csv"
PRICE_FILE = "price.csv"

# --- DATA LOADING ---
@st.cache_data
def load_inventory():
    return pd.read_csv(INVENTORY_FILE, encoding="latin1", skiprows=2)

try:
    inventory_df = load_inventory()
except FileNotFoundError:
    st.error("Error: Cannot find 'inventory.csv' in the system.")
    st.stop()

# --- PACKAGE MAPPING ---
PACKAGE_MAP = {
    "800W Power Station Package": ["PS800 Power station", "200w Solar Blanket"],
    "1800W Power Station Package": ["PS1800PRO Power station", "360w solar blanket"],
    "1800W Expanded (Double Capacity)": ["PS1800PRO Power station", "EB1536 Expansion pack", "360w solar blanket"],
    "2000W Power Station Package": ["PS2000w Power station", "360w solar blanket"],
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
        # NOTE: Change 'smtp.your-email-host.com' to your actual email provider's SMTP server
        # Examples: smtp.office365.com (Microsoft), smtp.zoho.com.au (Zoho), mail.yourdomain.com (cPanel)
        server = smtplib.SMTP('smtp.your-email-host.com', 587) 
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, customer_email, text)
        server.quit()
    except Exception as e:
        st.error(f"Failed to send email. Error: {e}")

# --- FRONT END APP ---
st.title("Portable Solutions - Equipment Booking")
st.write("Servicing Nollamara, Balcatta, and the wider Perth region.")
st.write("Select your dates below to build your off-grid package.")

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
        
        # --- MULTI-ITEM SELECTION ---
        selected_packages = st.multiselect("Select Equipment (Choose as many as you need):", list(PACKAGE_MAP.keys()))
        
        if selected_packages:
            has_solar = any("200w Solar Blanket" in PACKAGE_MAP[pkg] or "360w solar blanket" in PACKAGE_MAP[pkg] for pkg in selected_packages)
            
            remove_solar = False
            if has_solar:
                remove_solar = st.checkbox("Remove Solar Blanket(s) from my selected power stations", value=False)
            
            # --- AGGREGATE INVENTORY CHECK ---
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
                
                # --- BOOKING FORM ---
                with st.form("booking_form"):
                    st.write("### Customer Details")
                    name = st.text_input("Full Name")
                    email = st.text_input("Email Address")
                    phone = st.text_input("Phone Number")
                    
                    st.divider()
                    st.write("### Hire Agreement")
                    st.markdown("Please complete the [**Customer Hire Agreement (Click Here)**](https://docs.google.com/forms/d/e/1FAIpQLSd2bfpED_4WQzpkR4BYuIfpc9V8V_GfKohniY83F-A3bSIMzw/viewform?usp=header) before confirming your booking.")
                    agreement_ticked = st.checkbox("I have submitted the Customer Hire Agreement via the link above.")
                    
                    submit = st.form_submit_button("Confirm Booking")
                    
                    if submit:
                        if not agreement_ticked:
                            st.error("You must complete and tick the Customer Hire Agreement to submit your booking.")
                        elif name and email and phone:
                            st.success("Booking Request Submitted!")
                            
                            st.write("**The following specific units have been placed on hold for your hire:**")
                            for item, unit_id in available_units:
                                st.write(f"- {item} (Unit ID: {unit_id})")
                                
                            st.write(f"An instant confirmation has been sent to **{email}**.")
                            st.balloons()
                            
                            send_confirmation_email(name, email)
                            
                        else:
                            st.error("Please fill out all contact details to confirm.")
