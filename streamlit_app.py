import streamlit as st
import json
import os
import logging
import hashlib
from intro_text import INTRO_TEXT
from openai import OpenAI
from dotenv import load_dotenv
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import traceback
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Preformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.units import cm
from io import BytesIO
import markdown2
from reportlab.lib.colors import grey
import re
from reportlab.pdfgen import canvas


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
    """Analyze the GTM configuration using OpenAI's GPT. """
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

    First - output a summary of the tracking ID's used for each of the platforms detected so we can sanity check vs our measurement plan. We should also check to see if there are any discrepancies between ID's used in tags - which could be cause for concern. Recommend the user checks the ID's vs their tracking plans. If you find discrepancies between ID usage flag these as errors.

    Output your analysis of each tag following the guidelines below:
    1. List tag that have problems  - one section for each tag, output tag name in format "Tag Name: 'XXXX'" in bold heading (not large)
    2. For each tag provide a dot-point analysis on improvements based on best practice
    3. We should anlyse tag names based on best practice naming convention -  [Platform] - [Type] - [Description] or [Platform] | [Type] - [Description] - if they are not, we should provide a suggestion for a rename
    4. Any UA tags should be deleted - for these do not mention any other output except for the fact they should be deleted because UA is no longer active
    5. Any paused tags should be reviewed and removed if unnessary
    6. Do not number headings
    7. When outputting tracking ID's or tag names in content wrap them in code tags for better readability
    8. Skip the UA output analysis if no UA tags were found - this applies with all tags (we should limit redundant output)
    9. If a tag type starts with CVT_ then it is a custom template tag - you should find the matching template ID in the JSON and find the "name" of the template to determine the tag type
    10. When outputting floodlight tags we should output the "activity tag" and "advertiser ID" - values for each tag. Do not disregard this step
    11. When we encounter a html type tag with "insight.adsrvr.org" in the output, it is a "TTD" tag and we should find the image src within the HTML content, extract the URL and display it for verification


    """
  

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a marketing expert responsible for reviewing and providing feedback on Google Tag Manager configurations. You should follow the instructions directly and not omit any steps. Do not guess any results. Do not output any vague suggestions - all action points should have clear and consice instructions that will lead to the problem being solved."},
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
        
        # st.sidebar.write(f"G'day, {st.session_state['user'].email}")
        
        # Retrieve the projects for the user and create the dropdown with "New Analysis" at the top
        projects = get_projects(get_user_id(), limit=5)
        project_names = ["Start New Analysis"] + [project['name'] for project in projects]
        
        selected_index = st.sidebar.selectbox(
            "Select a project",
            range(len(project_names)),
            format_func=lambda i: project_names[i],
            key="selected_project_index"
        )
        
        if selected_index == 0:  # If "Start New Analysis" is selected
            # Reset session state and navigate to the new analysis page
            st.session_state.pop('selected_project_index', None)
            st.session_state.pop('selected_project_id', None)
            st.session_state['page'] = 'home'
            # st.rerun()  # Rerun to apply the changes
        
        elif selected_index > 0:  # If a specific project is selected
            selected_project = projects[selected_index - 1]  # Adjust index due to "Start New Analysis"
            st.session_state['selected_project_id'] = selected_project['id']
            st.session_state['page'] = 'project_details'
    
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
                    st.sidebar.success("A profile has now been created - you can now log in.")
                    logger.info(f"New user signed up: {email}")
                else:
                    st.sidebar.error("Error creating user")
                    logger.error(f"Failed to create user: {email}")
            else:
                st.sidebar.error("Please enter both email and password.")

    st.sidebar.divider()

    if is_logged_in():
        # Logout button to clear session state
        if st.sidebar.button("Logout"):
            del st.session_state['user']
            del st.session_state['session']
            if 'selected_project_index' in st.session_state:
                del st.session_state['selected_project_index']
            if 'selected_project_id' in st.session_state:
                del st.session_state['selected_project_id']
            st.sidebar.success("Logged out successfully!")
            st.rerun()
            logger.info("User logged out")

    # Add the footer with your LinkedIn profile
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

def get_cached_analysis(hash_value, user_id):
    """Retrieve cached analysis from Supabase."""
    try:
        client = get_supabase_client()
        result = client.table('analysis_cache').select("*").eq('hash', hash_value).eq('user_id', user_id).execute()
        return result.data[0] if result and result.data else None
    except Exception as e:
        logger.error(f"Error retrieving cached analysis for hash {hash_value} and user {user_id}: {str(e)}")
        handle_error(e)
        return None

def save_cached_analysis(hash_value, analysis, user_id, project_id):
    """Save analysis to Supabase cache."""
    try:
        client = get_supabase_client()
        data = client.table('analysis_cache').insert({
            "hash": hash_value,
            "analysis": analysis,
            "user_id": user_id,
            "project_id": project_id,
            "created_at": datetime.now().isoformat()
        }).execute()
        logger.info(f"Analysis cached for hash: {hash_value}, user: {user_id}, project: {project_id}")
        return data.data[0] if data and data.data else None
    except Exception as e:
        logger.error(f"Error saving cached analysis for hash {hash_value}, user {user_id}, project {project_id}: {str(e)}")
        handle_error(e)
        return None
    
def analyze_config(config, user_id, project_id):
    """Analyze the GTM configuration and return the analysis, using cache if available."""
    
    # Add a checkbox to allow bypassing the cache (hash check)
    bypass_cache = st.checkbox("Bypass cache and re-run analysis")
    
    # Add a checkbox to skip the GPT analysis
    skip_gpt_analysis = st.checkbox("Skip analysis and output extraction only")
    
    hash_value = hash_json(config)
    cached_analysis = get_cached_analysis(hash_value, user_id)

    # If bypass is not checked and cached analysis exists, use the cached result
    if cached_analysis and not bypass_cache and not skip_gpt_analysis:
        st.info("ℹ️ This configuration has been analyzed before. Showing cached results.")
        return cached_analysis['analysis']
    
    config_summary = summarize_config(config)
    tags = config['containerVersion'].get('tag', [])
    variables = config['containerVersion'].get('variable', [])
    triggers = config['containerVersion'].get('trigger', [])

    # Skip GPT analysis and return JSON summary
    if skip_gpt_analysis:
        st.success("Skipped GPT analysis. Displaying JSON summary.")
        return json.dumps(config_summary, indent=4)  # Provide the JSON summary

    # If bypass is checked or no cached analysis exists, perform a new analysis
    client = OpenAI(api_key=DEFAULT_API_KEY)
    with st.spinner("Analyzing GTM configuration..."):
        analysis = analyze_with_gpt(config_summary, tags, variables, triggers, client)

    # Save the new analysis to cache if the hash was not bypassed
    if not bypass_cache:
        save_cached_analysis(hash_value, analysis, user_id, project_id)

    return analysis

def new_analysis_page():
    if not is_logged_in():
        st.markdown(INTRO_TEXT)
    else:

        st.title("New GTM audit")

        st.markdown("Generate your JSON file at [Google Tag Manager](https://tagmanager.google.com) > Admin > Export Container then upload below.")
        # analysis_option = st.session_state.get('analysis_option', 'choose')        
        #if analysis_option == 'choose':
        #    analysis_option = st.radio(
        #        "Choose analysis source:",
        #        ("Upload JSON file", "Select from examples")
        #    )
        
        analysis_option = "Upload JSON file"
        
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
                user_id = get_user_id()
                project_id = None  # We'll set this after saving the project
                analysis = analyze_config(config, user_id, project_id)
                display_analysis(config, analysis, full_access=is_logged_in())

                if is_logged_in():
                    # Automatically save the project
                    container_name = config['containerVersion']['container']['name']
                    saved_project = save_project(user_id, container_name, config, analysis)
                    if saved_project:
                        project_id = saved_project['id']
                        # Update the cached analysis with the project_id
                        hash_value = hash_json(config)
                        save_cached_analysis(hash_value, analysis, user_id, project_id)
                        st.success(f"Project '{container_name}' saved automatically!")
                    else:
                        st.error("Failed to save the project.")
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
            st.write(f"**{project['name']}**")
            st.caption(f"Created: {project['created_at']}")
        with col2:
            if st.button("View", key=f"view_project_{project['id']}"):
                st.session_state['selected_project_id'] = project['id']
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
                # Remove this line if the 'updated_at' column doesn't exist
                # "updated_at": datetime.now().isoformat()
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
    # st.markdown(f"**Tag Manager URL:** {config_summary['tag_manager_url']}")


    if full_access:

        tab1, tab2, tab3, tab4 = st.tabs(["Analysis",f"Tags ({config_summary['tag_count']})", f"Variables ({config_summary['variable_count']})", f"Triggers ({config_summary['trigger_count']})"])

        with tab1:
            st.markdown(analysis)

            st.divider()
            if st.button("Generate export of findings",type='primary'):
                export_findings(config_summary, analysis)

        with tab2:
            for i, tag in enumerate(config['containerVersion'].get('tag', []), 1):
                with st.expander(f"Tag {i}: {tag.get('name', 'Unnamed Tag')}"):
                    st.json(tag)

        with tab3:
            for i, variable in enumerate(config['containerVersion'].get('variable', []), 1):
                with st.expander(f"Variable {i}: {variable.get('name', 'Unnamed Variable')}"):
                    st.json(variable)

        with tab4:
            for i, trigger in enumerate(config['containerVersion'].get('trigger', []), 1):
                with st.expander(f"Trigger {i}: {trigger.get('name', 'Unnamed Trigger')}"):
                    st.json(trigger)

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.setFont("Helvetica", 9)
        self.drawRightString(20*cm, 1*cm, f"Page {self._pageNumber} of {page_count}")
        self.drawString(1*cm, 1*cm, "Generated by GTM Auditor by Brad Farleigh - bradfarleigh.com")


def export_findings(config_summary, analysis):
    """Export the analysis findings as a PDF file."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    elements = []

    # Define styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    heading_style = styles['Heading2']
    normal_style = ParagraphStyle('Normal', fontSize=10, leading=14, alignment=TA_JUSTIFY)
    value_style = ParagraphStyle('Value', fontSize=10, leading=14, textColor=grey)
    bullet_style = ParagraphStyle('Bullet', fontSize=10, leading=14, alignment=TA_JUSTIFY, bulletFontName='Helvetica', bulletIndent=0, bulletFontSize=10)
    code_style = ParagraphStyle('Code', fontName='Courier', fontSize=8, leading=10)

    # Add title
    elements.append(Paragraph("GTM Audit Findings", title_style))
    elements.append(Spacer(1, 24))

    # Add summary information
    summary_items = [
        ("Container Name", config_summary['container_name']),
        ("Tag Manager URL", config_summary['tag_manager_url']),
        ("Tag Count", str(config_summary['tag_count'])),
        ("Variable Count", str(config_summary['variable_count'])),
        ("Trigger Count", str(config_summary['trigger_count']))
    ]

    for heading, value in summary_items:
        elements.append(Paragraph(f"<b>{heading}:</b> {value}", normal_style))
        elements.append(Spacer(1, 6))

    elements.append(Spacer(1, 24))

    # Add analysis
    elements.append(Paragraph("Analysis", heading_style))
    elements.append(Spacer(1, 12))

    # Convert markdown to HTML and sanitize it
    try:
        html_analysis = markdown2.markdown(analysis, extras=["fenced-code-blocks", "footnotes", "toc", "cuddled-lists", "tables", "strike"])
    except Exception as e:
        st.error(f"Error converting markdown to HTML: {e}")
        return

    # Safely handle HTML, ensuring no unclosed tags are passed to Paragraph
    sanitized_html = re.sub(r'<(strong|em|b|i)>', '', html_analysis)  # Remove potential unclosed tags for simplicity
    sanitized_html = re.sub(r'</(strong|em|b|i)>', '', sanitized_html)

    # Convert the sanitized HTML into paragraphs, supporting bullet points
    for line in sanitized_html.split('\n'):
        if line.strip():
            if line.strip().startswith("<ul>") or line.strip().startswith("<ol>"):  # Detect bullet point lists
                elements.append(Spacer(1, 6))
            elif line.strip().startswith("<li>"):  # Handle list items
                bullet_text = line[4:-5].strip()  # Strip <li> and </li> tags
                elements.append(Paragraph(f"• {bullet_text}", bullet_style))  # Add bullet point
                elements.append(Spacer(1, 6))
            else:
                try:
                    elements.append(Paragraph(line, normal_style))
                    elements.append(Spacer(1, 6))
                except ValueError as e:
                    st.error(f"Error processing line for PDF export: {e}")
                    continue

    # Build PDF
    doc.build(elements, canvasmaker=NumberedCanvas)
    pdf = buffer.getvalue()
    buffer.close()

    # Generate filename from container name
    container_name = config_summary['container_name']
    clean_container_name = re.sub(r'[\s.]+', '-', container_name)  # Replace spaces and periods with hyphens

    # Provide download button with custom filename
    st.download_button(
        label="Download the findings (PDF)",
        data=pdf,
        file_name=f"{clean_container_name}.pdf",
        mime="application/pdf",
    )
    logger.info("Findings exported as PDF")

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

            else:
                st.error("Project not found")
        else:
            st.error("No project selected")
    
    if st.session_state['page'] != 'home':
        if st.button("Back to Home"):
            st.session_state['page'] = 'home'
            st.rerun()
            

    
    if 'selected_project_id' not in st.session_state:
        st.session_state['selected_project_id'] = None  #

    user_id = get_user_id()
    project_id = st.session_state['selected_project_id']
    # st.write("User ID:", user_id)
    # st.write("Project ID:", project_id)

if __name__ == "__main__":
    main()