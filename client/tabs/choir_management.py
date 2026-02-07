import streamlit as st
import pandas as pd
from datetime import datetime, date
from client.utils.supabase_client import get_supabase


def get_all_persons():
    """Fetch all persons from the database"""
    try:
        supabase = get_supabase()
        response = supabase.table("persons").select("*").order("surname", desc=False).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error fetching persons: {e}")
        return []


def get_choir_register(year):
    """Fetch choir register for a specific year"""
    try:
        supabase = get_supabase()
        response = supabase.table("choir_register").select("id, personId, year, created_at, removed, persons(name, surname, grade)").eq("year", year).eq("removed", False).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error fetching choir register: {e}")
        return []


def add_person_to_choir(person_id, year):
    """Add a person to the choir register"""
    try:
        supabase = get_supabase()
        
        # Check if already exists
        existing = supabase.table("choir_register").select("*").eq("personId", person_id).eq("year", year).execute()
        
        if existing.data and len(existing.data) > 0:
            # If exists but removed, update to not removed
            if existing.data[0].get("removed", False):
                supabase.table("choir_register").update({"removed": False}).eq("id", existing.data[0]["id"]).execute()
                return True, "Person re-added to choir register."
            else:
                return False, "Person already in choir register for this year."
        else:
            # Insert new record
            supabase.table("choir_register").insert({
                "personId": person_id,
                "year": year,
                "removed": False
            }).execute()
            return True, "Person added to choir register."
    except Exception as e:
        return False, f"Error adding person: {e}"


def remove_person_from_choir(register_id):
    """Remove a person from choir register (soft delete by setting removed=True)"""
    try:
        supabase = get_supabase()
        supabase.table("choir_register").update({
            "removed": True
        }).eq("id", register_id).execute()
        return True, "Person removed from choir register."
    except Exception as e:
        return False, f"Error removing person: {e}"


def get_all_practice_dates():
    """Fetch all choir practice dates"""
    try:
        supabase = get_supabase()
        response = supabase.table("choir_practice_dates").select("*").order("date", desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error fetching practice dates: {e}")
        return []


def delete_practice_date(date_id):
    """Delete a practice date"""
    try:
        supabase = get_supabase()
        supabase.table("choir_practice_dates").delete().eq("id", date_id).execute()
        return True, "Practice date deleted."
    except Exception as e:
        return False, f"Error deleting practice date: {e}"


def add_practice_date(practice_date):
    """Add a new practice date"""
    try:
        supabase = get_supabase()
        date_str = practice_date.strftime("%Y-%m-%d")
        
        # Check if exists
        existing = supabase.table("choir_practice_dates").select("*").eq("date", date_str).execute()
        if existing.data and len(existing.data) > 0:
            return False, "Practice date already exists."
        
        supabase.table("choir_practice_dates").insert({"date": date_str}).execute()
        return True, "Practice date added."
    except Exception as e:
        return False, f"Error adding practice date: {e}"


def update_person(person_id, name=None, surname=None, grade=None):
    """Update person's name, surname, and/or grade"""
    try:
        supabase = get_supabase()
        
        data = {}
        if name is not None:
            data["name"] = name
        if surname is not None:
            data["surname"] = surname
        if grade is not None:
            data["grade"] = grade
        
        if not data:
            return False, "No data to update."
        
        supabase.table("persons").update(data).eq("id", person_id).execute()
        return True, "Person updated successfully."
    except Exception as e:
        return False, f"Error updating person: {e}"


def add_new_person(name, surname, grade=None, card_uid=None):
    """Add a new person to the database"""
    try:
        supabase = get_supabase()
        
        data = {
            "name": name,
            "surname": surname
        }
        
        if grade is not None:
            data["grade"] = grade
        if card_uid:
            data["card_uid"] = card_uid
        
        supabase.table("persons").insert(data).execute()
        return True, "Person added successfully."
    except Exception as e:
        return False, f"Error adding person: {e}"


def delete_person(person_id):
    """Delete a person from the database"""
    try:
        supabase = get_supabase()
        supabase.table("persons").delete().eq("id", person_id).execute()
        return True, "Person deleted successfully."
    except Exception as e:
        return False, f"Error deleting person: {e}"


def render_choir_register_management():
    """Render the choir register management interface"""
    st.subheader("🎵 Choir Register Management")
    
    current_year = datetime.now().year
    selected_year = st.number_input("Select Year", min_value=2020, max_value=2030, value=current_year, step=1, key="register_year")
    
    # Display current choir members
    st.write("### Current Choir Members")
    choir_register = get_choir_register(selected_year)
    
    if choir_register:
        # Prepare data for display
        display_data = []
        for record in choir_register:
            person = record.get("persons", {})
            display_data.append({
                "ID": record["id"],
                "Name": person.get("name", "N/A"),
                "Surname": person.get("surname", "N/A"),
                "Grade": person.get("grade", "N/A"),
                "Added": record.get("created_at", "N/A")[:10] if record.get("created_at") else "N/A"
            })
        
        df = pd.DataFrame(display_data)
        
        # Display with data editor for removal
        st.write(f"**Total Members: {len(df)}**")
        
        # Use columns for layout
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.dataframe(df.drop(columns=["ID"]), width='stretch', hide_index=True)
        
        with col2:
            st.write("**Remove Member**")
            st.caption("Select a member ID to remove")
            
            member_options = {f"{row['Name']} {row['Surname']} (Grade {row['Grade']})": row['ID'] for _, row in df.iterrows()}
            
            if member_options:
                selected_member = st.selectbox("Select Member", options=list(member_options.keys()), key="remove_member_select")
                
                if st.button("Remove from Choir", type="secondary", key="remove_member_btn"):
                    member_id = member_options[selected_member]
                    success, msg = remove_person_from_choir(member_id)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
    else:
        st.info(f"No choir members found for {selected_year}.")
    
    st.divider()
    
    # Add new member
    st.write("### Add New Member to Choir")
    
    all_persons = get_all_persons()
    
    if all_persons:
        # Filter out persons already in choir
        choir_person_ids = {record["personId"] for record in choir_register} if choir_register else set()
        available_persons = [p for p in all_persons if p["id"] not in choir_person_ids]
        
        if available_persons:
            person_options = {f"{p['name']} {p['surname']} (Grade {p.get('grade', 'N/A')})": p['id'] for p in available_persons}
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                selected_person = st.selectbox("Select Person to Add", options=list(person_options.keys()), key="add_person_select")
            
            with col2:
                st.write("")  # Spacer
                st.write("")  # Spacer
                if st.button("Add to Choir", type="primary", key="add_person_btn"):
                    person_id = person_options[selected_person]
                    success, msg = add_person_to_choir(person_id, selected_year)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
        else:
            st.info("All available persons are already in the choir register for this year.")
    else:
        st.warning("No persons found in the database.")


def render_practice_dates_management():
    """Render the practice dates management interface"""
    st.subheader("📅 Practice Dates Management")
    
    # Display existing practice dates
    st.write("### Existing Practice Dates")
    practice_dates = get_all_practice_dates()
    
    if practice_dates:
        # Prepare data for display
        display_data = []
        for record in practice_dates:
            display_data.append({
                "ID": record["id"],
                "Date": record.get("date", "N/A"),
                "Created": record.get("created_at", "N/A")[:10] if record.get("created_at") else "N/A"
            })
        
        df = pd.DataFrame(display_data)
        
        st.write(f"**Total Practice Dates: {len(df)}**")
        
        # Use columns for layout
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.dataframe(df.drop(columns=["ID"]), width='stretch', hide_index=True)
        
        with col2:
            st.write("**Delete Date**")
            st.caption("Select a date to delete")
            
            date_options = {row['Date']: row['ID'] for _, row in df.iterrows()}
            
            if date_options:
                selected_date = st.selectbox("Select Date", options=list(date_options.keys()), key="delete_date_select")
                
                if st.button("Delete Date", type="secondary", key="delete_date_btn"):
                    date_id = date_options[selected_date]
                    
                    # Confirmation
                    if st.session_state.get("confirm_delete") != date_id:
                        st.session_state.confirm_delete = date_id
                        st.warning("⚠️ Click again to confirm deletion")
                        st.rerun()
                    else:
                        success, msg = delete_practice_date(date_id)
                        if success:
                            st.success(msg)
                            st.session_state.confirm_delete = None
                            st.rerun()
                        else:
                            st.error(msg)
    else:
        st.info("No practice dates found.")
    
    st.divider()
    
    # Add new practice date
    st.write("### Add New Practice Date")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        new_date = st.date_input("Select Date", value=date.today(), key="new_practice_date")
    
    with col2:
        st.write("")  # Spacer
        st.write("")  # Spacer
        if st.button("Add Practice Date", type="primary", key="add_date_btn"):
            success, msg = add_practice_date(new_date)
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)


def render_persons_management():
    """Render the persons management interface"""
    st.subheader("👤 Persons Management")
    
    # Display all persons
    st.write("### All Persons")
    all_persons = get_all_persons()
    
    if all_persons:
        # Prepare data for display
        display_data = []
        for person in all_persons:
            display_data.append({
                "ID": person["id"],
                "Name": person.get("name", "N/A"),
                "Surname": person.get("surname", "N/A"),
                "Grade": person.get("grade", "N/A"),
                "Card UID": person.get("card_uid", "N/A")
            })
        
        df = pd.DataFrame(display_data)
        
        st.write(f"**Total Persons: {len(df)}**")
        
        # Display the dataframe
        st.dataframe(df.drop(columns=["ID"]), width='stretch', hide_index=True)
        
        st.divider()
        
        # Edit person section
        st.write("### Edit Person")
        
        # Create a selectbox with person names
        person_options = {f"{row['Name']} {row['Surname']} (ID: {row['ID']})": row['ID'] for _, row in df.iterrows()}
        
        selected_person_key = st.selectbox("Select Person to Edit", options=list(person_options.keys()), key="edit_person_select")
        selected_person_id = person_options[selected_person_key]
        
        # Get the current person data
        selected_person_data = df[df['ID'] == selected_person_id].iloc[0]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            new_name = st.text_input("Name", value=selected_person_data['Name'], key="edit_name")
        
        with col2:
            new_surname = st.text_input("Surname", value=selected_person_data['Surname'], key="edit_surname")
        
        with col3:
            # Handle grade - could be N/A or a number
            current_grade = selected_person_data['Grade']
            if current_grade == "N/A" or pd.isna(current_grade):
                grade_value = None
            else:
                try:
                    grade_value = int(float(current_grade))
                except:
                    grade_value = None
            
            new_grade = st.number_input("Grade", min_value=1, max_value=12, value=grade_value, key="edit_grade")
        
        if st.button("Update Person", type="primary", key="update_person_btn"):
            # Only update if values changed
            name_changed = new_name != selected_person_data['Name']
            surname_changed = new_surname != selected_person_data['Surname']
            
            # Check if grade changed
            grade_changed = False
            if new_grade is not None:
                if grade_value is None or new_grade != grade_value:
                    grade_changed = True
            
            if name_changed or surname_changed or grade_changed:
                success, msg = update_person(
                    selected_person_id,
                    name=new_name if name_changed else None,
                    surname=new_surname if surname_changed else None,
                    grade=new_grade if grade_changed else None
                )
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
            else:
                st.info("No changes to save.")
        
        st.divider()
        
        # Add new person section
        st.write("### Add New Person")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            new_person_name = st.text_input("Name", key="new_person_name")
        
        with col2:
            new_person_surname = st.text_input("Surname", key="new_person_surname")
        
        with col3:
            new_person_grade = st.number_input("Grade (Optional)", min_value=1, max_value=12, value=None, key="new_person_grade")
        
        new_person_card_uid = st.text_input("Card UID (Optional)", key="new_person_card_uid")
        
        if st.button("Add Person", type="primary", key="add_new_person_btn"):
            if new_person_name and new_person_surname:
                success, msg = add_new_person(
                    new_person_name,
                    new_person_surname,
                    grade=new_person_grade if new_person_grade else None,
                    card_uid=new_person_card_uid if new_person_card_uid else None
                )
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
            else:
                st.error("Name and Surname are required.")
    else:
        st.info("No persons found in the database.")



def render():
    """Main render function for Choir Management tab"""
    st.header("⚙️ Choir Management Dashboard")
    st.caption("Manage choir members, practice dates, and persons")
    
    # Create tabs for different management sections
    tab1, tab2, tab3 = st.tabs(["👥 Choir Register", "📅 Practice Dates", "👤 Persons"])
    
    with tab1:
        render_choir_register_management()
    
    with tab2:
        render_practice_dates_management()
    
    with tab3:
        render_persons_management()
