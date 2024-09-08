import streamlit as st
import os
import json
from typing import Dict, Any, List
from file_operations import load_gtm_json, extract_tags
from id_extraction import extract_facebook_id, extract_ga4_id, extract_google_ads_id, extract_ua_id, extract_tiktok_id
from tag_extraction import check_id_consistency, group_google_ads_tags, group_ga4_tags, group_fb_event_tags
from naming_conventions import gather_tag_naming_info
from trigger_helpers import get_trigger_names

# Function to load JSON files from a directory
def load_json_files(directory: str) -> Dict[str, Dict[str, Any]]:
    json_files = {}
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            file_path = os.path.join(directory, filename)
            with open(file_path, 'r') as file:
                json_files[filename] = json.load(file)
    return json_files

# Function to extract tracking IDs
def extract_tracking_ids(gtm_data: Dict[str, Any]) -> Dict[str, List[str]]:
    tags = extract_tags(gtm_data)
    variables = gtm_data.get('containerVersion', {}).get('variable', [])
    facebook_ids, ga4_ids, google_ads_ids, ua_tags, tiktok_ids, paused_tags, inconsistencies = check_id_consistency(tags, variables, gtm_data)
    return {
        'Facebook IDs': list(facebook_ids),
        'GA4 IDs': list(ga4_ids),
        'Google Ads IDs': list(google_ads_ids),
        'Universal Analytics IDs': list(ua_tags),
        'TikTok IDs': list(tiktok_ids)
    }

# Function to get Facebook events
def get_facebook_events(gtm_data: Dict[str, Any]) -> List[Dict[str, str]]:
    tags = extract_tags(gtm_data)
    trigger_names = get_trigger_names(gtm_data)
    facebook_events, _ = group_fb_event_tags(tags, trigger_names, gtm_data)
    return facebook_events

# Function to get GA4 events
def get_ga4_events(gtm_data: Dict[str, Any]) -> List[Dict[str, str]]:
    tags = extract_tags(gtm_data)
    trigger_names = get_trigger_names(gtm_data)
    ga4_events = group_ga4_tags(tags, trigger_names)
    return ga4_events

# Function to get tag naming recommendations
def get_tag_naming_recommendations(gtm_data: Dict[str, Any]) -> List[Dict[str, str]]:
    tags = extract_tags(gtm_data)
    trigger_names = get_trigger_names(gtm_data)
    return gather_tag_naming_info(tags, trigger_names)

# Main Streamlit app
def main():
    st.title("GTM Debug Tool")

    # Load JSON files
    json_files = load_json_files('json-examples')

    # Function selection
    function_options = {
        "Extract Tracking IDs": extract_tracking_ids,
        "Get Facebook Events": get_facebook_events,
        "Get GA4 Events": get_ga4_events,
        "Get Tag Naming Recommendations": get_tag_naming_recommendations
    }
    selected_function_name = st.selectbox("Select a function to test", list(function_options.keys()))

    if st.button("Run Tests"):
        selected_function = function_options[selected_function_name]
        
        for filename, gtm_data in json_files.items():
            st.header(f"File: {filename}")
            result = selected_function(gtm_data)
            if isinstance(result, dict):
                st.json(result)
            elif isinstance(result, list):
                if result:
                    st.dataframe(result, use_container_width=True,hide_index=True)
                else:
                    st.write("No results found.")
            st.markdown("---")

if __name__ == "__main__":
    main()