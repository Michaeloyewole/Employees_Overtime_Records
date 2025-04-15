import streamlit as st  
import pandas as pd  
import sqlite3  
import plotly.express as px  
from datetime import datetime  
import io  
import base64  
import os  
  
# Page config  
st.set_page_config(  
    page_title="Employee Overtime Management",  
    page_icon="👥",  
    layout="wide",  
    initial_sidebar_state="expanded"  
)  
  
# Custom CSS  
st.markdown("""  
    <style>  
    .main {  
        padding: 0rem 1rem;  
    }  
    .stButton>button {  
        width: 100%;  
    }  
    </style>  
    """, unsafe_allow_html=True)  
  
# Database initialization  
def init_db():  
    conn = sqlite3.connect('overtime.db')  
    c = conn.cursor()  
    c.execute('''  
        CREATE TABLE IF NOT EXISTS overtime (  
            id INTEGER PRIMARY KEY AUTOINCREMENT,  
            date TEXT,  
            employee_id TEXT,  
            name TEXT,  
            designation TEXT,  
            status TEXT,  
            scheduling_ot REAL,  
            occ_ot REAL,  
            training_ot REAL,  
            ops_ot REAL,  
            approved_by TEXT,  
            total_ot REAL,  
            timestamp TEXT  
        )  
    ''')  
    conn.commit()  
    conn.close()  
  
# Initialize database  
init_db()  
  
# Data management functions  
def save_entry(data):  
    conn = sqlite3.connect('overtime.db')  
    c = conn.cursor()  
    c.execute('''  
        INSERT INTO overtime   
        (date, employee_id, name, designation, status,   
         scheduling_ot, occ_ot, training_ot, ops_ot,   
         approved_by, total_ot, timestamp)  
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)  
    ''', data)  
    conn.commit()  
    conn.close()  
  
def load_data():  
    conn = sqlite3.connect('overtime.db')  
    df = pd.read_sql_query("SELECT * FROM overtime", conn)  
    conn.close()  
    if not df.empty:  
        df['date'] = pd.to_datetime(df['date'])  
    return df  
  
def get_csv_download_link(df):  
    csv = df.to_csv(index=False)  
    b64 = base64.b64encode(csv.encode()).decode()  
    href = f'<a href="data:file/csv;base64,{b64}" download="overtime_data.csv" class="btn">Download CSV File</a>'  
    return href  
  
def overtime_entry_form(dept):  
    st.header(f"{dept} Overtime Entry")  
      
    with st.form(key=f"{dept}_form"):  
        col1, col2 = st.columns(2)  
        with col1:  
            date = st.date_input("Date", value=datetime.today())  
            emp_id = st.text_input("Employee ID")  
            name = st.text_input("Name")  
          
        with col2:  
            designation = st.text_input("Designation")  
            status = st.selectbox("Status", ["Active", "Inactive"])  
            ot_hours = st.number_input("Overtime Hours", min_value=0.0, step=0.5)  
          
        approved_by = st.text_input("Approved By")  
        submit = st.form_submit_button("Submit Entry")  
          
        if submit:  
            ot_data = [  
                date.strftime('%Y-%m-%d'),  
                emp_id,  
                name,  
                designation,  
                status,  
                ot_hours if dept == "Scheduling" else 0.0,  
                ot_hours if dept == "OCC" else 0.0,  
                ot_hours if dept == "Training" else 0.0,  
                ot_hours if dept == "Operations" else 0.0,  
                approved_by,  
                ot_hours,  
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')  
            ]  
            save_entry(ot_data)  
            st.success(f"✅ Overtime entry for {name} saved successfully!")  
  
def upload_csv():  
    st.header("Upload CSV Data")  
      
    # Template download  
    template_df = pd.DataFrame(columns=[  
        "date", "employee_id", "name", "designation", "status",  
        "scheduling_ot", "occ_ot", "training_ot", "ops_ot",  
        "approved_by", "total_ot"  
    ])  
    template_csv = template_df.to_csv(index=False)  
    template_b64 = base64.b64encode(template_csv.encode()).decode()  
    st.markdown(  
        f'<a href="data:file/csv;base64,{template_b64}" download="overtime_template.csv">📥 Download Template CSV</a>',  
        unsafe_allow_html=True  
    )  
      
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")  
    if uploaded_file is not None:  
        try:  
            df = pd.read_csv(uploaded_file)  
            st.write("Preview of uploaded data:")  
            st.dataframe(df.head())  
              
            if st.button("Import Data"):  
                df['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  
                conn = sqlite3.connect('overtime.db')  
                df.to_sql('overtime', conn, if_exists='append', index=False)  
                conn.close()  
                st.success("✅ Data imported successfully!")  
        except Exception as e:  
            st.error(f"Error: {str(e)}")  
  
def show_dashboard():  
    st.header("Overtime Dashboard")  
      
    df = load_data()  
    if not df.empty:  
        # Summary metrics  
        total_employees = df['employee_id'].nunique()  
        total_ot = df['total_ot'].sum()  
          
        col1, col2, col3, col4 = st.columns(4)  
        with col1:  
            st.metric("Total Employees", total_employees)  
        with col2:  
            st.metric("Total Scheduling OT", f"{df['scheduling_ot'].sum():.2f}h")  
        with col3:  
            st.metric("Total OCC OT", f"{df['occ_ot'].sum():.2f}h")  
        with col4:  
            st.metric("Total Training OT", f"{df['training_ot'].sum():.2f}h")  
  
        # Charts  
        st.subheader("Overtime Distribution")  
          
        # Department-wise distribution  
        df_melt = df.melt(  
            id_vars=['name'],  
            value_vars=['scheduling_ot', 'occ_ot', 'training_ot', 'ops_ot'],  
            var_name='Department',  
            value_name='Hours'  
        )  
          
        fig1 = px.bar(  
            df_melt,  
            x='name',  
            y='Hours',  
            color='Department',  
            title='Overtime by Department and Employee',  
            template='plotly_white'  
        )  
        st.plotly_chart(fig1, use_container_width=True)  
          
        # Time series  
        df_daily = df.groupby('date')[['total_ot']].sum().reset_index()  
        fig2 = px.line(  
            df_daily,  
            x='date',  
            y='total_ot',  
            title='Daily Overtime Trend',  
            template='plotly_white'  
        )  
        st.plotly_chart(fig2, use_container_width=True)  
  
        # Data table  
        st.subheader("Detailed Records")  
        st.dataframe(  
            df.sort_values('date', ascending=False),  
            use_container_width=True  
        )  
          
        # Download link  
        st.markdown(get_csv_download_link(df), unsafe_allow_html=True)  
    else:  
        st.info("No data available. Please add entries or upload data.")  
  
# Sidebar  
st.sidebar.title("Navigation")  
page = st.sidebar.radio(  
    "Select Module",  
    ["Dashboard", "Scheduling Overtime", "OCC Overtime",   
     "Training Overtime", "Operations Overtime", "Upload Data"]  
)  
  
# Main content  
if page == "Dashboard":  
    show_dashboard()  
elif page == "Upload Data":  
    upload_csv()  
else:  
    overtime_entry_form(page.split()[0])  
  
# Footer  
st.sidebar.markdown("---")  
st.sidebar.markdown("© 2023 Employee Overtime Management")  
