import streamlit as st
from project_utils import *
import time
import requests

# --- Set page config (call only once) ---
st.set_page_config(page_title="Harmony", layout="wide")

# --- CSS Styling ---
st.markdown("""
    <style>
    button[kind="secondary"] {
        font-size: 20px !important;
        padding: 12px 20px !important;
        border-radius: 10px !important;
    }
    .stButton>button {
        height: 48px;
        font-size: 16px;
        border-radius: 8px;
        width: 100%;
    }
    h1 {
        margin-top: 20px;
        margin-bottom: 20px;
        text-align: center;
        font-weight: 600;
    }
    .nav-button {
        display: block;
        width: 100%;
        padding: 0.75rem;
        margin-bottom: 0.5rem;
        background-color: #f0f2f6;
        border: none;
        border-radius: 8px;
        text-align: center;
        font-size: 16px;
        font-weight: 600;
        color: #333;
        cursor: pointer;
        transition: background-color 0.2s;
    }
    .nav-button:hover {
        background-color: #dbe4f0;
    }
    .nav-button-active {
        background-color: #4c83ff;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# Always-visible heading
st.markdown("<h1>PROJECT HARMONY</h1>", unsafe_allow_html=True)

# --- Session Init ---
defaults = {
    "view_note": None,
    "show_form": False,
    "show_analysis": False,
    "nav_choice": "Saved Notes"
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# --- Login Logic ---
if "email" not in st.session_state:
    login_screen()
    st.stop()

# --- Sidebar Navigation ---
with st.sidebar:
    st.markdown("## Navigation")

    # Navigation options
    nav_options = ["Saved Notes", "New Note", "Statistics"]
    selected_option = None

    for option in nav_options:
        btn_key = f"nav_{option.replace(' ', '_')}"
        active_class = "nav-button nav-button-active" if st.session_state.nav_choice == option else "nav-button"
        if st.button(option, key=btn_key):
            selected_option = option
        st.markdown(f"""
            <script>
            var btn = window.parent.document.querySelectorAll('button[data-testid="button-{btn_key}"]')[0];
            if (btn) {{
                btn.className = "{active_class}";
            }}
            </script>
        """, unsafe_allow_html=True)

    if selected_option:
        st.session_state.nav_choice = selected_option
        st.experimental_rerun()

    st.markdown("---")
    if st.button("Logout"):
        st.session_state.clear()
        st.experimental_rerun()

# --- View State from nav_choice ---
if st.session_state.nav_choice == "New Note":
    st.session_state.show_form = True
    st.session_state.view_note = None
    st.session_state.show_analysis = False
elif st.session_state.nav_choice == "Statistics":
    st.session_state.show_form = False
    st.session_state.view_note = None
    st.session_state.show_analysis = True
else:
    if st.session_state.view_note is None:
        st.session_state.show_form = False
        st.session_state.show_analysis = False


# --- Note Display ---
if st.session_state.view_note:
    try:
        df = get_notes_from_supabase()
        note_id = st.session_state.view_note
        result = df[df["id"] == int(note_id)]

        if not result.empty:
            note = result.iloc[0]
            note_title = note["title"]
            note_text = note["body"]
            prediction_message = note["prediction_message"]

            st.subheader(f"Editing: {note_title}")
            st.markdown(prediction_message)

            new_title = st.text_input("Edit Title (max char = 100)", value=note_title, max_chars=100)
            new_text = st.text_area("Edit Note", value=note_text, height=300)
            
            # === Equal-width button styling ===
            st.markdown("""
            <style>
                div.stButton > button {
                    width: 100% !important;
                    height: 3rem;
                    font-size: 16px;
                    font-weight: 600;
                    border-radius: 10px;
                }
            </style>
            """, unsafe_allow_html=True)

            # === 3 equal buttons aligned in a row ===
            col1, col2, col3 = st.columns(3)

            with col1: 
                if st.button("Update and Save Note"):
                    if new_title.strip() and new_text.strip():
                        prediction = predict_both(new_text)
                        delete_note_from_supabase(int(note_id))
                        save_note_to_supabase(
                            title= new_title, 
                            body = new_text, 
                            pred_depression=prediction[0], 
                            pred_schizophrenia=prediction[1], 
                            prediction_message=prediction[2]
                            )
                        st.success("Note updated successfully.")
                        time.sleep(4)
                        st.session_state.view_note = None
                        try:
                            st.rerun()
                        except AttributeError:
                            st.experimental_rerun()
            with col2:
                if st.button("Delete Note"):
                    res_del = delete_note_from_supabase(int(note_id))
                    if res_del.status_code == 204:
                        st.success("Note deleted.")
                    else:
                        st.error(f"Failed to delete note: {res.text}")
                    st.session_state.view_note = None
                    try:
                        st.rerun()
                    except AttributeError:
                        st.experimental_rerun()

            with col3:
                if st.button("Back To Saved Notes"):
                    st.session_state.view_note = None
                    try:
                        st.rerun()
                    except AttributeError:
                        st.experimental_rerun()
            st.stop()
                    
        else:
            st.error("Note not found.")
            st.session_state.view_note = None

    except Exception as e:
        st.error(f"Failed to load note: {e}")
        st.session_state.view_note = None

elif st.session_state.show_analysis:
    st.subheader("Statistics Dashboard")
    try:
        df = get_notes_from_supabase()

        if df.empty:
            st.error("No notes found.")
        else:
            with st.form("Choose Analysis:"):
                options = ["Depression", "Schizophrenia"]
                selected = st.selectbox("Choose an option:", options)
                submitted = st.form_submit_button("Show")

            if submitted:
                if selected == "Depression":
                    show_analysis_depression()
                elif selected == "Schizophrenia":
                    show_analysis_schizo()

    except Exception as e:
        st.error(f"Failed to fetch analysis data: {e}")        

elif st.session_state.show_form:
    st.subheader("Add a New Journal Entry")
    title = st.text_input("Title (max 100 chars)", max_chars=100)
    body = st.text_area("Write your Journal here", height=200)

    if "pending_prediction" not in st.session_state:
        st.session_state.pending_prediction = None

    if st.session_state.pending_prediction:
        st.info(f"Prediction: {st.session_state.pending_prediction}")

    if st.button("Predict and Save Note"):
        if title.strip() and body.strip():
            prediction = predict_both(body)
            res_save = save_note_to_supabase(
                title=title,
                body=body,
                pred_depression=prediction[0],
                pred_schizophrenia=prediction[1],
                prediction_message=prediction[2]
            )
            st.success(f"{prediction[2]}")
            
            if res_save.status_code == 201:
                st.success("Note saved to Supabase.")
            else:
                st.error(f"Failed to save note: {res.text}")
            
            time.sleep(4) # Show result for 5 seconds before redirecting
            # Reset states and reroute
            st.session_state.show_form = False
            st.session_state.prediction = None
            st.session_state.prediction_message = None
            st.session_state.view_note = None
            st.session_state.nav_choice = "Saved Notes"
            try:
                st.rerun()
            except AttributeError:
                st.experimental_rerun()
        else:
            st.warning("Title and body cannot be empty.")
    st.stop()

else:
    st.subheader("Saved Notes")
    notes = get_notes_from_supabase()
    if notes.empty:
        st.info("No notes saved yet!")
    else:
        num_cols = 4
        cols = st.columns(num_cols)
        for idx, (_, note) in enumerate(notes.iterrows()):
            with cols[idx % num_cols]:
                with st.container():
                    title_short = note["title"][:13] + ("..." if len(note["title"]) > 13 else "")

                st.markdown("#### " + title_short)
                st.text_area(
                    label="Preview",
                    value=preview(note["body"]),
                    height=180,
                    disabled=True,
                    label_visibility="collapsed",
                    key=f"note_preview_{note['id']}"
                )
                if st.button("Open", key=f"open_note_{note['id']}"):
                    st.session_state.view_note = note["id"]
                    try:
                        st.rerun()
                    except AttributeError:
                        st.experimental_rerun()
