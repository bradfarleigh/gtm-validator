import streamlit as st
import json
import os
from openai import OpenAI
from dotenv import load_dotenv
from intro_text import INTRO_TEXT
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

load_dotenv()

DEFAULT_API_KEY = os.getenv("CHATGPT_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

BRAD_LINKEDIN_URL = "https://www.linkedin.com/in/brad-farleigh"

def handle_error(e):
    error_code = hash(str(e)) % 10000  # Generate a 4-digit error code
    st.error(f"An error occurred. Error Code: {error_code}")
    st.markdown(f"If you're experiencing issues, please reach out to Brad on [LinkedIn]({BRAD_LINKEDIN_URL}).")

def load_gtm_config(file):
    try:
        config = json.load(file)
        if 'containerVersion' not in config or 'tag' not in config['containerVersion']:
            raise ValueError("Invalid GTM export format")
        return config
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON file")

def summarize_config(config):
    container_version = config['containerVersion']
    tags = container_version.get('tag', [])
    variables = container_version.get('variable', [])
    triggers = container_version.get('trigger', [])
    summary = {
        'container_name': container_version.get('container', {}).get('name', 'Unknown'),
        'tag_manager_url': container_version.get('tagManagerUrl', 'Unknown'),
        'tag_count': len(tags),
        'variable_count': len(variables),
        'trigger_count': len(triggers),
        'tag_types': {},
        'platforms': [],
        'folder_ids': []
    }
    for tag in tags:
        tag_type = tag['type']
        summary['tag_types'][tag_type] = summary['tag_types'].get(tag_type, 0) + 1
        platform = tag['name'].split('|')[0].strip() if '|' in tag['name'] else 'Unknown'
        if platform not in summary['platforms']:
            summary['platforms'].append(platform)
        if 'parentFolderId' in tag and tag['parentFolderId'] not in summary['folder_ids']:
            summary['folder_ids'].append(tag['parentFolderId'])
    return summary

def analyze_with_gpt(config_summary, tags, variables, triggers, client):
    sanitized_summary = json.dumps(config_summary, indent=2)
    sanitized_tags = json.dumps([{k: v for k, v in tag.items() if k in ['name', 'type', 'parameter']} for tag in tags], indent=2)
    sanitized_variables = json.dumps([{k: v for k, v in var.items() if k in ['name', 'type', 'parameter']} for var in variables], indent=2)
    sanitized_triggers = json.dumps([{k: v for k, v in trigger.items() if k in ['name', 'type', 'customEventFilter']} for trigger in triggers], indent=2)

    prompt = f"""
    Analyse the following Google Tag Manager (GTM) configuration:

    Container Name: {config_summary['container_name']}
    Tag Manager URL: {config_summary['tag_manager_url']}

    Configuration Summary:
    {sanitized_summary}

    Tags:
    {sanitized_tags}

    Variables:
    {sanitized_variables}

    Triggers:
    {sanitized_triggers}

    Focus on:
    1. Naming Conventions: [Platform] | [Type] - [Description]
    2. Configuration Consistency: Check IDs (GA4 Measurement ID, Floodlight Advertiser ID, etc.)
    3. Event Tracking configuration
    4. Identify paused and redundant tags
    5. Folder Structure: Check if tags are in appropriate folders
    6. Conversion Linker: Verify settings
    7. Variable usage and consistency
    8. Trigger setup and efficiency
    
    Rules:
    1. For Universal Analytics tags, only suggest deletion.
    2. Display IDs or tags mentioned for checking.
    3. Use Australian English.
    4. Provide concise, actionable feedback for each tag, variable, and trigger.
    5. Highlight potential issues or improvements in the overall setup.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a GTM expert providing concise, actionable feedback."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        handle_error(e)
        return "An error occurred during analysis. Please try again later."

def signup(email, password):
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        return response
    except Exception as e:
        handle_error(e)
        return None

def login(email, password):
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        return response
    except Exception as e:
        handle_error(e)
        return None

def save_project(user_id, name, config, analysis):
    try:
        data, count = supabase.table('projects').insert({
            "user_id": user_id,
            "name": name,
            "config": json.dumps(config),
            "analysis": analysis,
            "created_at": datetime.now().isoformat()
        }).execute()
        return data
    except Exception as e:
        handle_error(e)
        return None

def get_projects(user_id):
    try:
        data, count = supabase.table('projects').select("*").eq('user_id', user_id).order('created_at', desc=True).execute()
        return data[1]
    except Exception as e:
        handle_error(e)
        return []

def get_project(project_id):
    try:
        data, count = supabase.table('projects').select("*").eq('id', project_id).execute()
        return data[1][0] if data[1] else None
    except Exception as e:
        handle_error(e)
        return None

def login_signup():
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            response = login(email, password)
            if response:
                st.session_state['user'] = response.user
                st.success("Logged in successfully!")
                st.experimental_rerun()
            else:
                st.error("Invalid email or password")

    with tab2:
        new_email = st.text_input("New Email")
        new_password = st.text_input("New Password", type="password")
        if st.button("Sign Up"):
            response = signup(new_email, new_password)
            if response:
                st.success("User created successfully! Please log in.")
            else:
                st.error("Error creating user")
def is_logged_in():
    return 'user' in st.session_state and st.session_state['user'] is not None and hasattr(st.session_state['user'], 'id')

def get_user_id():
    return st.session_state['user'].id if is_logged_in() else None

def signup(email, password):
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        return response
    except Exception as e:
        handle_error(e)
        return None

def login(email, password):
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        return response
    except Exception as e:
        handle_error(e)
        return None

def save_project(user_id, name, config, analysis):
    try:
        data, count = supabase.table('projects').insert({
            "user_id": user_id,
            "name": name,
            "config": json.dumps(config),
            "analysis": analysis,
            "created_at": datetime.now().isoformat()
        }).execute()
        return data
    except Exception as e:
        handle_error(e)
        return None

def get_projects(user_id):
    try:
        data, count = supabase.table('projects').select("*").eq('user_id', user_id).order('created_at', desc=True).execute()
        return data[1]
    except Exception as e:
        handle_error(e)
        return []

def get_project(project_id):
    try:
        data, count = supabase.table('projects').select("*").eq('id', project_id).execute()
        return data[1][0] if data[1] else None
    except Exception as e:
        handle_error(e)
        return None

def login_modal():
    with st.modal("Login/Signup"):
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            if st.button("Login", key="login_button"):
                response = login(email, password)
                if response:
                    st.session_state['user'] = response.user
                    st.success("Logged in successfully!")
                    st.experimental_rerun()
                else:
                    st.error("Invalid email or password")

        with tab2:
            new_email = st.text_input("New Email", key="signup_email")
            new_password = st.text_input("New Password", type="password", key="signup_password")
            if st.button("Sign Up", key="signup_button"):
                response = signup(new_email, new_password)
                if response:
                    st.success("User created successfully! Please log in.")
                else:
                    st.error("Error creating user")

def sidebar_menu():
    st.sidebar.title("GTM Auditor")
    menu = ["New Analysis", "Projects"]
    choice = st.sidebar.selectbox("Menu", menu)
    
    if is_logged_in():
        if st.sidebar.button("Logout"):
            del st.session_state['user']
            st.experimental_rerun()
    else:
        if st.sidebar.button("Login/Signup"):
            st.session_state['show_login_modal'] = True
    
    return choice

def new_analysis_page():
    st.title("New GTM Analysis")
    uploaded_file = st.file_uploader("Choose a GTM configuration JSON file", type="json")

    if uploaded_file is not None:
        if 'config' not in st.session_state or 'analysis' not in st.session_state:
            try:
                config = load_gtm_config(uploaded_file)
                analysis = analyze_config(config)
                st.session_state['config'] = config
                st.session_state['analysis'] = analysis
            except ValueError as e:
                handle_error(e)
                return

        if is_logged_in():
            project_name = st.text_input("Project Name")
            if project_name and st.button("Save Project"):
                save_project(get_user_id(), project_name, st.session_state['config'], st.session_state['analysis'])
                st.success("Project saved successfully!")

        display_analysis(st.session_state['config'], st.session_state['analysis'], full_access=is_logged_in())

        if not is_logged_in():
            st.warning("Sign up or log in to save your project and see the full analysis")
            if st.button("Login/Signup"):
                st.session_state['show_login_modal'] = True
                st.experimental_rerun()

def projects_page():
    st.title("My Projects")
    if not is_logged_in():
        st.warning("Please log in to view your projects")
        return

    projects = get_projects(get_user_id())
    if not projects:
        st.info("You don't have any saved projects yet.")
        return

    for project in projects:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader(project['name'])
            st.text(f"Created at: {project['created_at']}")
        with col2:
            if st.button("View", key=f"view_{project['id']}"):
                st.session_state['selected_project'] = project['id']
                st.experimental_rerun()

    if 'selected_project' in st.session_state:
        project = get_project(st.session_state['selected_project'])
        if project:
            st.subheader(f"Project: {project['name']}")
            config = json.loads(project['config'])
            analysis = project['analysis']
            display_analysis(config, analysis, full_access=True)

def main():
    st.set_page_config(page_title="GTM Auditor by Brad Farleigh", page_icon=None, layout="wide", initial_sidebar_state="auto", menu_items=None)

    if 'show_login_modal' in st.session_state and st.session_state['show_login_modal']:
        login_modal()
        st.session_state['show_login_modal'] = False

    choice = sidebar_menu()

    if choice == "New Analysis":
        new_analysis_page()
    elif choice == "Projects":
        projects_page()

    st.sidebar.divider()
    st.sidebar.markdown("Bradgic by [Brad Farleigh](https://www.linkedin.com/in/brad-farleigh)")

def analyze_config(config):
    client = OpenAI(api_key=DEFAULT_API_KEY)
    config_summary = summarize_config(config)
    tags = config['containerVersion'].get('tag', [])
    variables = config['containerVersion'].get('variable', [])
    triggers = config['containerVersion'].get('trigger', [])
    
    with st.spinner("Analysing GTM configuration..."):
        analysis = analyze_with_gpt(config_summary, tags, variables, triggers, client)

    return analysis

def display_analysis(config, analysis, full_access=True):
    config_summary = summarize_config(config)
    
    st.markdown(f"**Container Name:** {config_summary['container_name']}")
    st.markdown(f"**Tag Manager URL:** {config_summary['tag_manager_url']}")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Tags", config_summary['tag_count'])
    with col2:
        st.metric("Variables", config_summary['variable_count'])
    with col3:
        st.metric("Triggers", config_summary['trigger_count'])
    
    st.subheader("Analysis")
    if full_access:
        st.markdown(analysis)
    else:
        paragraphs = analysis.split('\n\n')
        st.markdown('\n\n'.join(paragraphs[:3]))
        st.warning("Sign up or log in to see the full analysis")

    if full_access:
        if st.button("Export Findings"):
            export_findings(config_summary, analysis)

        st.divider()
        st.header("GTM Configuration Details")
        
        tab1, tab2, tab3 = st.tabs(["Tags", "Variables", "Triggers"])
        
        with tab1:
            for i, tag in enumerate(config['containerVersion'].get('tag', []), 1):
                with st.expander(f"Tag {i}: {tag.get('name', 'Unnamed Tag')}"):
                    st.json(tag)
        
        with tab2:
            for i, variable in enumerate(config['containerVersion'].get('variable', []), 1):
                with st.expander(f"Variable {i}: {variable.get('name', 'Unnamed Variable')}"):
                    st.json(variable)
        
        with tab3:
            for i, trigger in enumerate(config['containerVersion'].get('trigger', []), 1):
                with st.expander(f"Trigger {i}: {trigger.get('name', 'Unnamed Trigger')}"):
                    st.json(trigger)

def export_findings(config_summary, analysis):
    data = {
        "Container Name": [config_summary['container_name']],
        "Tag Manager URL": [config_summary['tag_manager_url']],
        "Tag Count": [config_summary['tag_count']],
        "Variable Count": [config_summary['variable_count']],
        "Trigger Count": [config_summary['trigger_count']],
        "Analysis": [analysis]
    }
    df = pd.DataFrame(data)
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="gtm_audit_findings.csv",
        mime="text/csv",
    )

if __name__ == "__main__":
    main()