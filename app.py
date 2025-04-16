import streamlit as st  
import pandas as pd  
import sqlite3  
from datetime import datetime  
  
# --- CONFIGURATION ---  
st.set_page_config(page_title="Overtime Management App", page_icon="🕒", layout="wide")  
  
DB_NAME = "overtime_app.db"  
TABLE_NAME = "overtime_entries"  
  
# --- DATABASE FUNCTIONS ---  
def init_db():  
    conn = sqlite3.connect(DB_NAME)  
    c = conn.cursor()  
    c.execute(f"""  
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (  
            entry_id INTEGER PRIMARY KEY AUTOINCREMENT,  
            date TEXT,  
            week_start TEXT,  
            week_end TEXT,  
            employee_id TEXT,  
            name TEXT,  
            department TEXT,  
            roster_group TEXT,  
            overtime_type TEXT,  
            hours REAL,  
            depot TEXT,  
            notes TEXT,  
            reviewed_by TEXT,  
            audit_status TEXT,  
            discrepancy_comments TEXT  
        )  
    """)  
    conn.commit()  
    conn.close()  
  
def insert_entry(entry):  
    conn = sqlite3.connect(DB_NAME)  
    c = conn.cursor()  
    c.execute(f"""  
        INSERT INTO {TABLE_NAME} (  
            date, week_start, week_end, employee_id, name, department, roster_group,  
            overtime_type, hours, depot, notes, reviewed_by, audit_status, discrepancy_comments  
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)  
    """, (  
        entry['date'], entry['week_start'], entry['week_end'], entry['employee_id'], entry['name'],  
        entry['department'], entry['roster_group'], entry['overtime_type'], entry['hours'],  
        entry['depot'], entry['notes'], entry['reviewed_by'], entry['audit_status'], entry['discrepancy_comments']  
    ))  
    conn.commit()  
    conn.close()  
  
def fetch_entries(department=None):  
    conn = sqlite3.connect(DB_NAME)  
    c = conn.cursor()  
    if department:  
        c.execute(f"SELECT * FROM {TABLE_NAME} WHERE department = ?", (department,))  
    else:  
        c.execute(f"SELECT * FROM {TABLE_NAME}")  
    rows = c.fetchall()  
    conn.close()  
    columns = [  
        'Entry ID', 'Date', 'Week Start', 'Week End', 'Employee ID', 'Name', 'Department',  
        'Roster Group', 'Overtime Type', 'Hours', 'Depot', 'Notes', 'Reviewed By', 'Audit Status', 'Discrepancy/Comments'  
    ]  
    return pd.DataFrame(rows, columns=columns)  
  
def update_audit_status(entry_id, new_status):  
    conn = sqlite3.connect(DB_NAME)  
    c = conn.cursor()  
    c.execute(f"UPDATE {TABLE_NAME} SET audit_status = ? WHERE entry_id = ?", (new_status, entry_id))  
    conn.commit()  
    conn.close()  
  
# --- UI FUNCTIONS ---  
def entry_form(department=None):  
    with st.form("entry_form_" + (department or "all"), clear_on_submit=True):  
        date = st.date_input("Date", value=datetime.today())  
        week_start = st.date_input("Week Start", value=datetime.today())  
        week_end = st.date_input("Week End", value=datetime.today())  
        employee_id = st.text_input("Employee ID")  
        name = st.text_input("Name")  
        dept = department or st.selectbox("Department", ["Planning", "Ops", "OCC", "Training"])  
        roster_group = st.text_input("Roster Group")  
        overtime_type = st.text_input("Overtime Type")  
        hours = st.number_input("Hours", min_value=0.0, step=0.5)  
        depot = st.text_input("Depot")  
        notes = st.text_area("Notes")  
        reviewed_by = st.text_input("Reviewed By")  
        audit_status = st.selectbox("Audit Status", ["", "Pending", "Approved", "Rejected"])  
        discrepancy_comments = st.text_area("Discrepancy/Comments")  
        submitted = st.form_submit_button("Add Entry")  
        if submitted:  
            entry = {  
                "date": str(date),  
                "week_start": str(week_start),  
                "week_end": str(week_end),  
                "employee_id": employee_id,  
                "name": name,  
                "department": dept,  
                "roster_group": roster_group,  
                "overtime_type": overtime_type,  
                "hours": hours,  
                "depot": depot,  
                "notes": notes,  
                "reviewed_by": reviewed_by,  
                "audit_status": audit_status,  
                "discrepancy_comments": discrepancy_comments  
            }  
            insert_entry(entry)  
            st.success("Entry added!")  
  
def department_tab(dept):  
    st.subheader(dept + " Overtime Entries")  
    df = fetch_entries(dept)  
    st.dataframe(df.head(20))  
    st.markdown("---")  
    st.write("Add new entry for " + dept)  
    entry_form(department=dept)  
  
def summary_tab():  
    st.subheader("Summary Dashboard")  
    df = fetch_entries()  
    st.dataframe(df.head(20))  
    if not df.empty:  
        st.bar_chart(df.groupby("Department")["Hours"].sum())  
        st.line_chart(df.groupby("Date")["Hours"].sum())  
    # Optionally, allow audit status update  
    st.markdown("#### Update Audit Status")  
    entry_id = st.number_input("Entry ID to update", min_value=1, step=1)  
    new_status = st.selectbox("New Audit Status", ["Pending", "Approved", "Rejected"])  
    if st.button("Update Status"):  
        update_audit_status(entry_id, new_status)  
        st.success("Audit status updated.")  
  
# --- MAIN APP ---  
init_db()  
st.title("Employee Overtime & Uncovered Duties Tool")  
tabs = st.tabs(["Summary", "Planning", "Ops", "OCC", "Training"])  
  
with tabs[0]:  
    summary_tab()  
with tabs[1]:  
    department_tab("Planning")  
with tabs[2]:  
    department_tab("Ops")  
with tabs[3]:  
    department_tab("OCC")  
with tabs[4]:  
    department_tab("Training")  
