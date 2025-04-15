import os  
import streamlit as st  
import pandas as pd  
import plotly.express as px  
import datetime  
import base64  
import sqlite3  
  
# -------------------------------  
# 1. Page Config & Data Directory  
# -------------------------------  
st.set_page_config(  
    page_title="Employee Overtime Tool",  
    page_icon="👥",  
    layout="wide",  
    initial_sidebar_state="expanded"  
)  
  
DATA_DIR = 'data'  
if not os.path.exists(DATA_DIR):  
    os.makedirs(DATA_DIR)  
  
# -------------------------------  
# SQLite Database Initialization  
# -------------------------------  
def init_sqlite_db():  
    conn = sqlite3.connect('overtime_database.db')  
    cursor = conn.cursor()  
      
    cursor.execute("""  
    CREATE TABLE IF NOT EXISTS overtime (  
        overtime_id TEXT PRIMARY KEY,  
        employee_id TEXT,  
        name TEXT,  
        department TEXT,  
        date TEXT,  
        hours REAL,  
        type TEXT,  
        approved_by TEXT,  
        status TEXT,  
        notes TEXT  
    )  
    """)  
      
    cursor.execute("""  
    CREATE TABLE IF NOT EXISTS employees (  
        employee_id TEXT PRIMARY KEY,  
        name TEXT,  
        department TEXT,  
        position TEXT,  
        status TEXT  
    )  
    """)  
      
    conn.commit()  
    conn.close()  
  
init_sqlite_db()  
  
# -------------------------------  
# Helper Functions  
# -------------------------------  
def load_data():  
    conn = sqlite3.connect('overtime_database.db')  
    df = pd.read_sql_query("SELECT * FROM overtime", conn)  
    conn.close()  
    return df  
  
def save_overtime(data):  
    conn = sqlite3.connect('overtime_database.db')  
    cursor = conn.cursor()  
    cursor.execute("""  
    INSERT INTO overtime   
    (overtime_id, employee_id, name, department, date, hours, type, approved_by, status, notes)  
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)  
    """, data)  
    conn.commit()  
    conn.close()  
  
def get_download_link(df):  
    csv = df.to_csv(index=False)  
    b64 = base64.b64encode(csv.encode()).decode()  
    href = f'<a href="data:file/csv;base64,{b64}" download="overtime_data.csv">Download Data</a>'  
    return href  
  
# -------------------------------  
# Page Functions  
# -------------------------------  
def overtime_entry():  
    st.header("Overtime Entry")  
      
    col1, col2 = st.columns(2)  
    with col1:  
        emp_id = st.text_input("Employee ID")  
        name = st.text_input("Name")  
        department = st.selectbox("Department", ["Scheduling", "OCC", "Training", "Operations"])  
      
    with col2:  
        date = st.date_input("Date")  
        hours = st.number_input("Hours", min_value=0.0, step=0.5)  
        ot_type = st.selectbox("Type", ["Regular", "Holiday", "Special"])  
      
    approved_by = st.text_input("Approved By")  
    status = st.selectbox("Status", ["Pending", "Approved", "Rejected"])  
    notes = st.text_area("Notes")  
      
    if st.button("Submit"):  
        overtime_id = f"OT{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"  
        data = (overtime_id, emp_id, name, department, str(date),   
                hours, ot_type, approved_by, status, notes)  
        save_overtime(data)  
        st.success("Overtime entry saved successfully!")  
  
def upload_data():  
    st.header("Upload Data")  
    uploaded_file = st.file_uploader("Choose CSV file", type="csv")  
      
    if uploaded_file is not None:  
        df = pd.read_csv(uploaded_file)  
        if st.button("Import"):  
            conn = sqlite3.connect('overtime_database.db')  
            df.to_sql('overtime', conn, if_exists='append', index=False)  
            conn.close()  
            st.success("Data imported successfully!")  
  
def view_reports():  
    st.header("Overtime Reports")  
      
    df = load_data()  
    if not df.empty:  
        # Summary metrics  
        total_hours = df['hours'].sum()  
        total_entries = len(df)  
        pending = len(df[df['status'] == 'Pending'])  
          
        col1, col2, col3 = st.columns(3)  
        col1.metric("Total Hours", f"{total_hours:.1f}")  
        col2.metric("Total Entries", total_entries)  
        col3.metric("Pending Approvals", pending)  
          
        # Charts  
        st.subheader("Department Distribution")  
        fig = px.pie(df, names='department', values='hours',   
                    title='Overtime Hours by Department')  
        st.plotly_chart(fig, use_container_width=True)  
          
        st.subheader("Daily Trend")  
        df['date'] = pd.to_datetime(df['date'])  
        daily_hours = df.groupby('date')['hours'].sum().reset_index()  
        fig2 = px.line(daily_hours, x='date', y='hours',   
                      title='Daily Overtime Hours')  
        st.plotly_chart(fig2, use_container_width=True)  
          
        # Data table  
        st.subheader("Detailed Records")  
        st.dataframe(df)  
          
        # Download link  
        st.markdown(get_download_link(df), unsafe_allow_html=True)  
    else:  
        st.info("No data available")  
  
# -------------------------------  
# Main App  
# -------------------------------  
st.title("Employee Overtime Management System")  
  
# Sidebar navigation  
page = st.sidebar.radio(  
    "Navigation",  
    ["Overtime Entry", "Upload Data", "Reports"]  
)  
  
if page == "Overtime Entry":  
    overtime_entry()  
elif page == "Upload Data":  
    upload_data()  
else:  
    view_reports()  
  
# Footer  
st.sidebar.markdown("---")  
st.sidebar.markdown("© 2023 Employee Overtime Management")  
