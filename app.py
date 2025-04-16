import streamlit as st  
import pandas as pd  
import matplotlib.pyplot as plt  
from datetime import datetime, timedelta  
import sqlite3  
import uuid  
import base64  
  
# Page configuration  
st.set_page_config(  
    page_title="Employee Overtime & Uncovered Duties Tool",  
    page_icon="👥",  
    layout="wide",  
    initial_sidebar_state="expanded"  
)  
  
# Database initialization with schema update  
def init_sqlite_db():  
    conn = sqlite3.connect('overtime_database.db')  
    cursor = conn.cursor()  
      
    # First, check if we need to migrate the 'type' column to 'depot'  
    try:  
        cursor.execute("SELECT type FROM overtime LIMIT 1")  
        # If the above succeeds, we need to migrate  
        cursor.execute("ALTER TABLE overtime RENAME COLUMN type TO depot")  
        conn.commit()  
    except sqlite3.OperationalError:  
        # Either the table doesn't exist or the migration is already done  
        pass  
      
    cursor.execute("""  
    CREATE TABLE IF NOT EXISTS overtime (  
        overtime_id TEXT PRIMARY KEY,  
        employee_id TEXT,  
        name TEXT,  
        department TEXT,  
        date TEXT,  
        hours REAL,  
        depot TEXT,  
        approved_by TEXT,  
        status TEXT,  
        notes TEXT  
    )""")  
      
    cursor.execute("""  
    CREATE TABLE IF NOT EXISTS uncovered_duties (  
        duty_id TEXT PRIMARY KEY,  
        date TEXT,  
        department TEXT,  
        shift TEXT,  
        hours_uncovered REAL,  
        reason TEXT,  
        status TEXT  
    )""")  
    conn.commit()  
    conn.close()  
  
def load_data(table_name="overtime"):  
    conn = sqlite3.connect('overtime_database.db')  
    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)  
    conn.close()  
    if 'date' in df.columns:  
        df['date'] = pd.to_datetime(df['date'])  
    # Ensure depot column exists  
    if table_name == "overtime" and 'depot' not in df.columns:  
        df['depot'] = "West"  # Default value  
    return df  
  
def get_download_link(df, text):  
    csv = df.to_csv(index=False)  
    b64 = base64.b64encode(csv.encode()).decode()  
    href = f'<a href="data:file/csv;base64,{b64}" download="data.csv">{text}</a>'  
    return href  
  
def overtime_entry():  
    st.header("Overtime Entry Form")  
      
    # Create two columns for side-by-side layout  
    col1, col2 = st.columns(2)  
      
    with col1:  
        with st.form("overtime_form_left"):  
            employee_id = st.text_input("Employee ID")  
            name = st.text_input("Name")  
            department = st.text_input("Department")  
            depot = st.selectbox("Depot", ["West", "East"])  
            date = st.date_input("Date")  
              
            if st.form_submit_button("Submit Left Form"):  
                overtime_id = str(uuid.uuid4())  
                data = (overtime_id, employee_id, name, department,   
                       date.strftime('%Y-%m-%d'), 0, depot,  # hours will be set in right form  
                       "", "Pending", "")  # default values  
                save_overtime(data)  
                st.success("Left form data saved!")  
      
    with col2:  
        with st.form("overtime_form_right"):  
            hours = st.number_input("Hours", min_value=0.0, step=0.5)  
            approved_by = st.text_input("Approved By")  
            status = st.selectbox("Status", ["Pending", "Approved", "Rejected"])  
            notes = st.text_area("Notes")  
              
            if st.form_submit_button("Submit Right Form"):  
                overtime_id = str(uuid.uuid4())  
                data = (overtime_id, employee_id, name, department,   
                       date.strftime('%Y-%m-%d'), hours, depot,  
                       approved_by, status, notes)  
                save_overtime(data)  
                st.success("Right form data saved!")  
  
def uncovered_duties_entry():  
    st.header("Uncovered Duties Entry Form")  
      
    col1, col2 = st.columns(2)  
      
    with col1:  
        with st.form("duties_form_left"):  
            date = st.date_input("Date")  
            department = st.text_input("Department")  
            shift = st.selectbox("Shift", ["Morning", "Afternoon", "Night"])  
              
            if st.form_submit_button("Submit Left Form"):  
                duty_id = str(uuid.uuid4())  
                data = (duty_id, date.strftime('%Y-%m-%d'), department, shift,  
                       0, "", "Pending")  # default values  
                save_uncovered_duty(data)  
                st.success("Left form data saved!")  
      
    with col2:  
        with st.form("duties_form_right"):  
            hours_uncovered = st.number_input("Hours Uncovered", min_value=0.0, step=0.5)  
            reason = st.text_area("Reason")  
            status = st.selectbox("Status", ["Open", "Covered", "Cancelled"])  
              
            if st.form_submit_button("Submit Right Form"):  
                duty_id = str(uuid.uuid4())  
                data = (duty_id, date.strftime('%Y-%m-%d'), department, shift,  
                       hours_uncovered, reason, status)  
                save_uncovered_duty(data)  
                st.success("Right form data saved!")  
  
def save_overtime(data):  
    conn = sqlite3.connect('overtime_database.db')  
    cursor = conn.cursor()  
    cursor.execute("""  
    INSERT INTO overtime   
    (overtime_id, employee_id, name, department, date, hours, depot, approved_by, status, notes)  
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)  
    """, data)  
    conn.commit()  
    conn.close()  
  
def save_uncovered_duty(data):  
    conn = sqlite3.connect('overtime_database.db')  
    cursor = conn.cursor()  
    cursor.execute("""  
    INSERT INTO uncovered_duties   
    (duty_id, date, department, shift, hours_uncovered, reason, status)  
    VALUES (?, ?, ?, ?, ?, ?, ?)  
    """, data)  
    conn.commit()  
    conn.close()  
  
def view_reports():  
    st.header("Reports Dashboard")  
    df_overtime = load_data("overtime")  
    df_duties = load_data("uncovered_duties")  
      
    if df_overtime.empty and df_duties.empty:  
        st.warning("No data available in the database")  
        return  
  
    # Create three columns for filters  
    col1, col2, col3 = st.columns(3)  
      
    with col1:  
        start_date = st.date_input("From Date", datetime.now() - timedelta(days=30))  
    with col2:  
        end_date = st.date_input("To Date", datetime.now())  
    with col3:  
        depot_options = ["Both"] + sorted(df_overtime['depot'].unique().tolist())  
        selected_depot = st.selectbox("Depot", depot_options)  
  
    # Apply filters  
    mask_overtime = (df_overtime['date'].dt.date >= start_date) & (df_overtime['date'].dt.date <= end_date)  
    mask_duties = (df_duties['date'].dt.date >= start_date) & (df_duties['date'].dt.date <= end_date)  
      
    if selected_depot != "Both":  
        mask_overtime &= (df_overtime['depot'] == selected_depot)  
      
    df_overtime_filtered = df_overtime[mask_overtime].copy()  
    df_duties_filtered = df_duties[mask_duties].copy()  
  
    # Display metrics  
    col1, col2, col3 = st.columns(3)  
    with col1:  
        st.metric("Total Overtime Hours", f"{df_overtime_filtered['hours'].sum():.1f}")  
    with col2:  
        st.metric("Total Uncovered Hours", f"{df_duties_filtered['hours_uncovered'].sum():.1f}")  
    with col3:  
        st.metric("Total Records", len(df_overtime_filtered) + len(df_duties_filtered))  
  
    # Visualizations  
    if not df_overtime_filtered.empty:  
        # Overtime by Depot Pie Chart  
        fig1, ax1 = plt.subplots(figsize=(8, 6))  
        depot_data = df_overtime_filtered.groupby('depot')['hours'].sum()  
        depot_data.plot(kind='pie', autopct='%1.1f%%', ax=ax1)  
        plt.title('Overtime Hours by Depot')  
        st.pyplot(fig1)  
        plt.close()  
  
        # Overtime by Department and Depot  
        fig2, ax2 = plt.subplots(figsize=(12, 6))  
        dept_depot_data = df_overtime_filtered.pivot_table(  
            values='hours',  
            index='department',  
            columns='depot',  
            aggfunc='sum',  
            fill_value=0  
        )  
        dept_depot_data.plot(kind='bar', ax=ax2)  
        plt.title('Overtime Hours by Department and Depot')  
        plt.xlabel('Department')  
        plt.ylabel('Hours')  
        plt.xticks(rotation=45)  
        plt.legend(title='Depot')  
        st.pyplot(fig2)  
        plt.close()  
  
    # Display filtered data  
    st.subheader("Filtered Overtime Records")  
    st.dataframe(df_overtime_filtered)  
      
    st.subheader("Filtered Uncovered Duties Records")  
    st.dataframe(df_duties_filtered)  
  
    # Download buttons  
    col1, col2 = st.columns(2)  
    with col1:  
        st.markdown(get_download_link(df_overtime_filtered, "Download Overtime Data"), unsafe_allow_html=True)  
    with col2:  
        st.markdown(get_download_link(df_duties_filtered, "Download Uncovered Duties Data"), unsafe_allow_html=True)  
  
def upload_module():  
    st.header("Upload Data")  
      
    upload_type = st.radio("Select Upload Type", ["Overtime", "Uncovered Duties"])  
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")  
      
    if uploaded_file is not None:  
        try:  
            df = pd.read_csv(uploaded_file)  
            if upload_type == "Overtime":  
                for _, row in df.iterrows():  
                    overtime_id = str(uuid.uuid4())  
                    data = (overtime_id,) + tuple(row)  
                    save_overtime(data)  
            else:  
                for _, row in df.iterrows():  
                    duty_id = str(uuid.uuid4())  
                    data = (duty_id,) + tuple(row)  
                    save_uncovered_duty(data)  
            st.success(f"{upload_type} data uploaded successfully!")  
        except Exception as e:  
            st.error(f"Error processing file: {e}")  
  
def main():  
    st.title("Employee Overtime & Uncovered Duties Management System")  
      
    # Navigation  
    page = st.sidebar.radio(  
        "Navigation",  
        ["Overtime Entry", "Uncovered Duties Entry", "Upload Data", "Reports"]  
    )  
      
    # Page routing  
    if page == "Overtime Entry":  
        overtime_entry()  
    elif page == "Uncovered Duties Entry":  
        uncovered_duties_entry()  
    elif page == "Upload Data":  
        upload_module()  
    else:  
        view_reports()  
  
if __name__ == "__main__":  
    init_sqlite_db()  
    main()  
