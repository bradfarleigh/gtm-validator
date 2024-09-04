# streamlit_app.py

import streamlit as st
from file_operations import load_gtm_json, extract_tags
from id_extraction import (
    extract_facebook_id, extract_ga4_id, extract_google_ads_id, extract_ua_id, extract_tiktok_id
)
from display import (
    display_tracking_id_summary, display_inconsistencies, display_grouped_tags, display_action_points
)
from utils import get_trigger_names, group_tags_by_type, check_id_consistency, generate_action_points

def main():
    st.title("GTM Tag Explorer and Validator")
    
    uploaded_file = st.file_uploader("Upload GTM JSON file", type="json")
    
    # Initialize action points variable
    action_points = []

    if uploaded_file is not None:
        gtm_data = load_gtm_json(uploaded_file)
        
        if gtm_data:
            tags = extract_tags(gtm_data)
            trigger_names = get_trigger_names(gtm_data)
            
            if tags:
                facebook_ids, ga4_ids, google_ads_ids, ua_tags, tiktok_ids, paused_tags, inconsistencies = check_id_consistency(tags)
                
                action_points = generate_action_points(facebook_ids, ga4_ids, google_ads_ids, ua_tags, tiktok_ids, paused_tags)
                
                # Display action points right after file upload and before other summaries
                display_action_points(action_points)
                
                display_tracking_id_summary(facebook_ids, ga4_ids, google_ads_ids, ua_tags, tiktok_ids)
                display_inconsistencies(inconsistencies)
                
                grouped_tags = group_tags_by_type(tags)
                display_grouped_tags(grouped_tags, trigger_names)
                
            else:
                st.warning("No tags found in the GTM JSON file.")
        else:
            st.warning("Failed to load GTM data from the JSON file.")

if __name__ == "__main__":
    main()
