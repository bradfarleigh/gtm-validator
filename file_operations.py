import json
import streamlit as st

def load_gtm_json(json_file):
    try:
        data = json.load(json_file)
        return data
    except json.JSONDecodeError:
        st.error("Invalid JSON file. Please upload a valid GTM JSON export.")
        return None

def extract_tags(data):
    if 'containerVersion' in data and 'tag' in data['containerVersion']:
        return data['containerVersion']['tag']
    else:
        st.warning("No tags found in the JSON file.")
        return []