import streamlit as st  
import pandas as pd  
import plotly.express as px  
from datetime import datetime  
  
# Page config  
st.set_page_config(page_title="Employee Overtime", layout="wide")  
  
# Initialize data  
if 'df' not in st.session_state:  
    st.session_state.df = pd.DataFrame(  
        columns=["Date", "ID", "Name", "Designation", "Status",   
                "Scheduling_OT", "OCC_OT", "Training_OT", "OPS_OT",   
                "Approved_By", "Total_OT"]  
    )  
  
def add_entry(dept, date, emp_id, name, designation, status, ot_hours, approved_by):  
    new_entry = {  
        "Date": date,  
        "ID": emp_id,  
        "Name": name,  
        "Designation": designation,  
        "Status": status,  
        "Scheduling_OT": ot_hours if dept == "Scheduling" else 0,  
        "OCC_OT": ot_hours if dept == "OCC" else 0,  
        "Training_OT": ot_hours if dept == "Training" else 0,  
        "OPS_OT": ot_hours if dept == "Operations" else 0,  
        "Approved_By": approved_by,  
        "Total_OT": ot_hours  
    }  
    st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_entry])], ignore_index=True)  
  
def overtime_form(dept):  
    st.header(f"{dept} Overtime Entry")  
    with st.form(key=f"{dept}_form"):  
        date = st.date_input("Date")  
        col1, col2 = st.columns(2)  
        with col1:  
            emp_id = st.text_input("Employee ID")  
            name = st.text_input("Name")  
        with col2:  
            designation = st.text_input("Designation")  
            status = st.selectbox("Status", ["Active", "Inactive"])  
        ot_hours = st.number_input("Overtime Hours", min_value=0.0, step=0.5)  
        approved_by = st.text_input("Approved By")  
          
        if st.form_submit_button("Submit"):  
            add_entry(dept, date, emp_id, name, designation, status, ot_hours, approved_by)  
            st.success("Entry added successfully!")  
  
def show_dashboard():  
    st.header("Overtime Dashboard")  
      
    if not st.session_state.df.empty:  
        col1, col2, col3, col4 = st.columns(4)  
        with col1:  
            st.metric("Total Scheduling OT", f"{st.session_state.df['Scheduling_OT'].sum():.2f}")  
        with col2:  
            st.metric("Total OCC OT", f"{st.session_state.df['OCC_OT'].sum():.2f}")  
        with col3:  
            st.metric("Total Training OT", f"{st.session_state.df['Training_OT'].sum():.2f}")  
        with col4:  
            st.metric("Total OPS OT", f"{st.session_state.df['OPS_OT'].sum():.2f}")  
  
        # Chart  
        df_melt = st.session_state.df.melt(  
            id_vars=['Name'],  
            value_vars=['Scheduling_OT', 'OCC_OT', 'Training_OT', 'OPS_OT'],  
            var_name='Department',  
            value_name='Hours'  
        )  
        fig = px.bar(df_melt, x='Name', y='Hours', color='Department', title='Overtime by Department')  
        st.plotly_chart(fig, use_container_width=True)  
          
        # Data table  
        st.dataframe(st.session_state.df)  
    else:  
        st.info("No data available. Please add entries.")  
  
# Sidebar navigation  
page = st.sidebar.radio("Select Module",   
    ["Dashboard", "Scheduling Overtime", "OCC Overtime", "Training Overtime", "Operations Overtime"])  
  
if page == "Dashboard":  
    show_dashboard()  
else:  
    overtime_form(page.split()[0])  
