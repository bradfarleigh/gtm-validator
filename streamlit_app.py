import streamlit as st
import json
import os
import logging
import hashlib
from openai import OpenAI
from dotenv import load_dotenv
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import traceback

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration constants
DEFAULT_API_KEY = os.getenv("CHATGPT_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BRAD_LINKEDIN_URL = "https://www.linkedin.com/in/brad-farleigh"

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_supabase_client():
    if 'session' in st.session_state and st.session_state['session'] is not None:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        client.auth.set_session(
            access_token=st.session_state['session'].access_token,
            refresh_token=st.session_state['session'].refresh_token
        )
        return client
    else:
        return create_client(SUPABASE_URL, SUPABASE_KEY)

def handle_error(e):
    error_message = f"An error occurred: {str(e)}"
    stack_trace = traceback.format_exc()
    
    st.error(error_message)
    st.code(stack_trace, language="python")
    
    logger.error(f"Error: {error_message}\n{stack_trace}")
    st.markdown(f"If you're experiencing issues, please reach out to Brad on [LinkedIn]({BRAD_LINKEDIN_URL}) and provide the error details above.")

def load_gtm_config(file):
    """Load and validate GTM configuration from a JSON file."""
    try:
        config = json.load(file)
        if 'containerVersion' not in config or 'tag' not in config['containerVersion']:
            raise ValueError("Invalid GTM export format")
        return config
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON file")

def summarize_config(config):
    """Summarize the GTM configuration."""
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
    """Analyze the GTM configuration using OpenAI's GPT."""
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
    """Sign up a new user using Supabase authentication."""
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        logger.info(f"User signed up: {email}")
        return response
    except Exception as e:
        handle_error(e)
        return None

def login(email, password):
    """Log in an existing user using Supabase authentication."""
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if response.user and response.session:
            st.session_state['user'] = response.user
            st.session_state['session'] = response.session
        logger.info(f"User logged in: {email}")
        return response
    except Exception as e:
        handle_error(e)
        return None

def get_projects(user_id, limit=None):
    """Retrieve projects for a specific user."""
    try:
        logger.info(f"Fetching projects for user: {user_id}")
        client = get_supabase_client()
        query = client.table('projects').select("*").eq('user_id', str(user_id)).order('created_at', desc=True)
        if limit:
            query = query.limit(limit)
        result = query.execute()
        projects = result.data if result else []
        logger.info(f"Projects fetched: {len(projects)}")
        return projects
    except Exception as e:
        logger.error(f"Error fetching projects for user {user_id}: {str(e)}")
        handle_error(e)
        return []

def get_project(project_id):
    """Retrieve a specific project by its ID."""
    try:
        logger.info(f"Fetching project with ID: {project_id}")
        client = get_supabase_client()
        result = client.table('projects').select("*").eq('id', project_id).execute()
        
        if result and result.data:
            project = result.data[0]
            logger.info(f"Project fetched successfully: {project['name']}")
            return project
        else:
            logger.warning(f"No project found with ID: {project_id}")
            return None
    except Exception as e:
        logger.error(f"Error fetching project with ID {project_id}: {str(e)}")
        handle_error(e)
        return None

def is_logged_in():
    """Check if a user is logged in."""
    return 'user' in st.session_state and 'session' in st.session_state and st.session_state['user'] is not None and st.session_state['session'] is not None

def get_user_id():
    """Get the current logged-in user's ID."""
    return st.session_state['user'].id if is_logged_in() else None

def on_project_select():
    if st.session_state.selected_project != "Select a project":
        project = next((p for p in st.session_state.projects if p['name'] == st.session_state.selected_project), None)
        if project:
            st.session_state['selected_project_id'] = project['id']
            st.session_state['page'] = 'project_details'

def sidebar_menu():
    st.sidebar.title("GTM Auditor")

    if is_logged_in():
        st.sidebar.write(f"G'day, {st.session_state['user'].email}")
        
        st.sidebar.subheader("Recent Projects")
        
        projects = get_projects(get_user_id(), limit=5)
        st.session_state.projects = projects  # Store projects in session state
        project_names = ["Select a project"] + [project['name'] for project in projects]
        
        if 'selected_project' not in st.session_state:
            st.session_state.selected_project = "Select a project"
        
        st.sidebar.selectbox("", project_names, key="selected_project", on_change=on_project_select)

        if st.sidebar.button("See All Projects"):
            st.session_state['page'] = 'all_projects'

    else:
        st.sidebar.markdown("### Login or signup")
        email = st.sidebar.text_input("Email", key="email")
        password = st.sidebar.text_input("Password", type="password", key="password")
        if st.sidebar.button("Login", type="primary", key="login_button"):
            if email and password:
                response = login(email, password)
                if response and response.user:
                    st.sidebar.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.sidebar.error("Invalid email or password")
                    logger.warning(f"Failed login attempt: {email}")
            else:
                st.sidebar.error("Please enter both email and password.")

        if st.sidebar.button("Sign Up", key="signup_button"):
            if email and password:
                response = signup(email, password)
                if response:
                    st.sidebar.success("User created successfully! Please log in.")
                    logger.info(f"New user signed up: {email}")
                else:
                    st.sidebar.error("Error creating user")
                    logger.error(f"Failed to create user: {email}")
            else:
                st.sidebar.error("Please enter both email and password.")

    st.sidebar.divider()
            
    if is_logged_in():
        if st.sidebar.button("Logout"):
            del st.session_state['user']
            del st.session_state['session']
            st.sidebar.success("Logged out successfully!")
            st.rerun()
            logger.info("User logged out")
            
    st.sidebar.caption("Bradgic by [Brad Farleigh](https://www.linkedin.com/in/brad-farleigh)")

def list_json_examples():
    """List all JSON files in the /json-examples directory."""
    json_dir = "./json-examples"
    json_files = [f for f in os.listdir(json_dir) if f.endswith('.json')]
    return json_files

def load_json_example(filename):
    """Load a JSON example file from the /json-examples directory."""
    with open(os.path.join("./json-examples", filename), 'r') as file:
        return json.load(file)

def hash_json(json_content):
    """Create a hash of the JSON content."""
    return hashlib.md5(json.dumps(json_content, sort_keys=True).encode()).hexdigest()

def get_cached_analysis(hash_value):
    """Retrieve cached analysis from Supabase."""
    try:
        client = get_supabase_client()
        result = client.table('analysis_cache').select("*").eq('hash', hash_value).execute()
        return result.data[0] if result and result.data else None
    except Exception as e:
        logger.error(f"Error retrieving cached analysis for hash {hash_value}: {str(e)}")
        handle_error(e)
        return None

def save_cached_analysis(hash_value, analysis):
    """Save analysis to Supabase cache."""
    try:
        client = get_supabase_client()
        data = client.table('analysis_cache').insert({
            "hash": hash_value,
            "analysis": analysis,
            "created_at": datetime.now().isoformat()
        }).execute()
        logger.info(f"Analysis cached for hash: {hash_value}")
        return data.data[0] if data and data.data else None
    except Exception as e:
        logger.error(f"Error saving cached analysis for hash {hash_value}: {str(e)}")
        handle_error(e)
        return None

def analyze_config(config):
    """Analyze the GTM configuration and return the analysis, using cache if available."""
    hash_value = hash_json(config)
    cached_analysis = get_cached_analysis(hash_value)

    if cached_analysis:
        st.info("This configuration has been analysed before. Showing cached results.")
        return cached_analysis['analysis']

    client = OpenAI(api_key=DEFAULT_API_KEY)
    config_summary = summarize_config(config)
    tags = config['containerVersion'].get('tag', [])
    variables = config['containerVersion'].get('variable', [])
    triggers = config['containerVersion'].get('trigger', [])

    with st.spinner("Analysing GTM configuration..."):
        analysis = analyze_with_gpt(config_summary, tags, variables, triggers, client)

    save_cached_analysis(hash_value, analysis)
    return analysis

def new_analysis_page():
    st.title("New GTM Analysis")
    
    if st.button("Upload New JSON"):
        st.session_state['analysis_option'] = 'upload'
    
    analysis_option = st.session_state.get('analysis_option', 'choose')
    
    if analysis_option == 'choose':
        analysis_option = st.radio(
            "Choose analysis source:",
            ("Upload JSON file", "Select from examples")
        )
    
    if analysis_option == "Upload JSON file":
        uploaded_file = st.file_uploader("Choose a GTM configuration JSON file", type="json")
        if uploaded_file is not None:
            config = load_gtm_config(uploaded_file)
    elif analysis_option == "Select from examples":
        json_examples = list_json_examples()
        selected_example = st.selectbox("Select a JSON example", json_examples)
        if selected_example:
            config = load_json_example(selected_example)
    
    if 'config' in locals():
        try:
            analysis = analyze_config(config)
            display_analysis(config, analysis, full_access=is_logged_in())

            if is_logged_in():
                # Automatically save the project
                container_name = config['containerVersion']['container']['name']
                save_project(get_user_id(), container_name, config, analysis)
                st.success(f"Project '{container_name}' saved automatically!")
            else:
                st.warning("Sign up or log in to save your project and see the full analysis")
        except ValueError as e:
            handle_error(e)

def all_projects_page():
    st.title("All Projects")
    projects = get_projects(get_user_id())
    
    for project in projects:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader(f"**{project['name']}**")
            st.caption(f"Created: {project['created_at']}")
        with col2:
            if st.button("View", key=f"view_project_{project['id']}"):
                st.session_state['selected_project'] = project['id']
                st.session_state['page'] = 'project_details'
                st.rerun()
    

def save_project(user_id, name, config, analysis):
    """Save a new project to the Supabase 'projects' table."""
    try:
        logger.info(f"Attempting to save project for user: {user_id}, name: {name}")
        client = get_supabase_client()
        
        # Check if a project with the same name already exists for this user
        result = client.table('projects').select("*").eq('user_id', str(user_id)).eq('name', name).execute()
        
        existing_projects = result.data if result else []
        
        logger.info(f"Existing projects: {existing_projects}")

        if existing_projects:
            # Update existing project
            project_id = existing_projects[0]['id']
            logger.info(f"Updating existing project with id: {project_id}")
            data = client.table('projects').update({
                "config": json.dumps(config),
                "analysis": analysis,
                "updated_at": datetime.now().isoformat()
            }).eq('id', project_id).execute()
            logger.info(f"Project updated for user: {user_id}, name: {name}")
        else:
            # Insert new project
            logger.info(f"Inserting new project for user: {user_id}, name: {name}")
            data = client.table('projects').insert({
                "user_id": user_id,
                "name": name,
                "config": json.dumps(config),
                "analysis": analysis,
                "created_at": datetime.now().isoformat()
            }).execute()
            logger.info(f"New project saved for user: {user_id}, name: {name}")
        
        return data.data[0] if data and data.data else None
    except Exception as e:
        logger.error(f"Error saving project for user {user_id}, name {name}: {str(e)}")
        handle_error(e)
        return None

def display_analysis(config, analysis, full_access=True):
    """Display the analysis of the GTM configuration."""
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
        if st.button("Generate export of findings",type='primary'):
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
    """Export the analysis findings as a CSV file."""
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
        label="Download the findings",
        data=csv,
        file_name="gtm_audit_findings.csv",
        mime="text/csv",
    )
    logger.info("Findings exported as CSV")

def main():
    st.set_page_config(
        page_title="GTM Auditor by Brad Farleigh",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items=None
    )

    if not supabase:
        st.error("Supabase client is not initialized")
        return

    sidebar_menu()

    if 'page' not in st.session_state:
        st.session_state['page'] = 'home'

    if st.session_state['page'] == 'home':
        new_analysis_page()
    elif st.session_state['page'] == 'all_projects':
        all_projects_page()
    elif st.session_state['page'] == 'project_details':
        if 'selected_project_id' in st.session_state:
            project = get_project(st.session_state['selected_project_id'])
            if project:
                st.title(f"Project: {project['name']}")
                config = json.loads(project['config'])
                analysis = project['analysis']
                display_analysis(config, analysis, full_access=True)
                if st.button("Back to All Projects"):
                    st.session_state['page'] = 'all_projects'
            else:
                st.error("Project not found")
        else:
            st.error("No project selected")
    
    st.divider()
    if st.session_state['page'] != 'home':
        if st.button("Back to Home",type="secondary"):
            st.session_state['page'] = 'home'

if __name__ == "__main__":
    main()