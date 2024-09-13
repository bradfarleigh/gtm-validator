import streamlit as st
import json
import os
from openai import OpenAI
from dotenv import load_dotenv
from intro_text import INTRO_TEXT

load_dotenv()

DEFAULT_API_KEY = os.getenv("CHATGPT_API_KEY")

def load_gtm_config(file):
    try:
        config = json.load(file)
        # Check for essential GTM export structure
        if 'containerVersion' not in config or 'tag' not in config['containerVersion']:
            raise ValueError("Invalid GTM export format")
        return config
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON file")

def summarize_config(config):
    container_version = config['containerVersion']
    tags = container_version.get('tag', [])
    summary = {
        'container_name': container_version.get('container', {}).get('name', 'Unknown'),
        'tag_manager_url': container_version.get('tagManagerUrl', 'Unknown'),
        'tag_count': len(tags),
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

def analyze_with_gpt(config_summary, tags, client):
    # Sanitize input to prevent prompt injection
    sanitized_summary = json.dumps(config_summary, indent=2)
    sanitized_tags = json.dumps([{k: v for k, v in tag.items() if k in ['name', 'type', 'parameter']} for tag in tags], indent=2)

    prompt = f"""
    This tool is being used by marketing professionals who will be in charge of reviewing and publishing GTM changes made by 3rd parties and will help them audit and find issues.

    Analyse the following Google Tag Manager (GTM) configuration summary and tags:

    Container Name: {config_summary['container_name']}
    Tag Manager URL: {config_summary['tag_manager_url']}

    Configuration Summary:
    {sanitized_summary}

    Tags:
    {sanitized_tags}

    Focus on:
    1. Naming Conventions:
       - Use the format: [Platform] | [Type] - [Description]
       - For Google Analytics 4: Use "GA4" as the platform
       - For Floodlight (DCM) tags: Use "DCM" or "FLOODLIGHT" as the platform
       - For The Trade Desk (TTD) tags: Use "TTD" as the platform
       - For custom templates: Apply platform-specific naming conventions (e.g., "FB | Event | Lead" for a Facebook custom template)
    2. Configuration Consistency: Output the IDs being used (e.g., GA4 Measurement ID, Floodlight Advertiser ID) and check if they're consistent across tags
    3. Event Tracking configuration
    4. Identify paused and redundant tags
    5. Folder Structure: Check if tags are placed in appropriate folders (Analytics, Advertising, Conversion Tracking, Utilities)
    6. Conversion Linker: Verify if it's set to fire on all pages and check enableCrossDomain and enableUrlPassthrough settings
    
    Rules to follow:
    1. If a Universal Analytics tag is found, only suggest that it should be deleted. Do not provide any other suggestions for Universal Analytics tags.
    2. If we mention that we should check an ID or tag - make sure we display what the ID or tag is (so we know what to check for)
    3. I repeat - if we see a Universal Analytics tag we should only ever recommend it be deleted because UA was turned off in 2024, provide no other output.
    4. Provide concise feedback on issues and suggest improvements for each tag.
    5. Output the analysis for each tag with feedback on improvements.
    6. Use Australian English.
    7. Do not say "conclusion" or "mate".
    8. Try not to be too verbose when explaining action points.

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
        return f"An error occurred: {str(e)}"

def main():

    st.set_page_config(page_title="GTM Auditor by Brad Farleigh", page_icon=None, layout="centered", initial_sidebar_state="auto", menu_items=None)

    st.title("GTM Auditor")

    st.markdown(INTRO_TEXT)

    api_key = DEFAULT_API_KEY

    if not api_key:
        st.warning("Please set your OpenAI API key in the .env file to proceed.")
        return

    client = OpenAI(api_key=api_key)

    st.subheader("Choose your GTM export file")

    uploaded_file = st.file_uploader("Choose a GTM configuration JSON file", type="json")

    if uploaded_file is not None:
        try:
            config = load_gtm_config(uploaded_file)
            analyze_config(config, client)
        except ValueError as e:
            st.error(f"Error: {str(e)}. Please upload a valid GTM export JSON file.")

    st.divider()

    st.markdown("Bradgic by [Brad Farleigh](https://www.linkedin.com/in/brad-farleigh)")

def analyze_config(config, client):
    config_summary = summarize_config(config)
    
    st.markdown(f"**Container Name:** {config_summary['container_name']}")
    st.markdown(f"**Tag Manager URL:** {config_summary['tag_manager_url']}")
    
    tags = config['containerVersion'].get('tag', [])
    
    with st.spinner("Processing..."):
        analysis = analyze_with_gpt(config_summary, tags, client)

    st.markdown(analysis)

    # Add collapsible section for tag details
    st.divider()
    st.header("Tag Inspector")
    for i, tag in enumerate(tags, 1):
        with st.expander(f"Tag {i}: {tag.get('name', 'Unnamed Tag')}"):
            st.json(tag)

if __name__ == "__main__":
    main()