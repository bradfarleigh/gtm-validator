import streamlit as st
import pandas as pd
from file_operations import load_gtm_json, extract_tags
from id_extraction import extract_facebook_id, extract_ga4_id, extract_google_ads_id, extract_ua_id, extract_tiktok_id
from display import (
    display_tracking_id_summary,
    display_grouped_tags,
    display_action_points,
    display_google_ads_tags,
    display_ga4_tags,
    display_fb_event_tags,
    display_tiktok_tags,
    display_floodlight_tags,
    display_tag_naming_conventions
)
from utils import get_trigger_names, group_tags_by_type
from tag_extraction import (
    check_id_consistency,
    group_google_ads_tags,
    group_ga4_tags,
    group_fb_event_tags
)
from naming_conventions import gather_tag_naming_info
from tiktok_helpers import group_tiktok_tags
from floodlight_helpers import group_floodlight_tags
from action_points import generate_action_points
from intro_text import INTRO_TEXT
from coming_features import COMING_FEATURES

# Set the page configuration to full width
st.set_page_config(page_title="GTM Tag Explorer and Validator", layout="wide")

def main():
    st.title("🎯 Validate and Analyse Your Google Tag Manager Setup")

    st.markdown(INTRO_TEXT, unsafe_allow_html=True)

    # File uploader for the GTM JSON file
    uploaded_file = st.file_uploader("Upload your GTM JSON file", type="json")
    
    if uploaded_file is not None:
        # Load and parse the GTM JSON data
        gtm_data = load_gtm_json(uploaded_file)
        
        if gtm_data:
            tags = extract_tags(gtm_data)
            trigger_names = get_trigger_names(gtm_data)
            variables = gtm_data.get('containerVersion', {}).get('variable', [])
            
            if tags:
                # Check for inconsistencies and collect tracking IDs
                facebook_ids, ga4_ids, google_ads_ids, ua_tags, tiktok_ids, paused_tags, inconsistencies = check_id_consistency(tags, variables, gtm_data)
                
                # Google Ads Conversion Tags and Issues
                grouped_google_ads_tags, google_ads_issues = group_google_ads_tags(tags, trigger_names)
                grouped_ga4_tags = group_ga4_tags(tags, trigger_names)
                grouped_fb_event_tags, grouped_fb_event_issues = group_fb_event_tags(tags, trigger_names, gtm_data)
                grouped_tiktok_tags = group_tiktok_tags(tags, trigger_names, gtm_data)
                grouped_floodlight_tags = group_floodlight_tags(tags, trigger_names)

                # Generate action points (including Google Ads issues)
                action_points = generate_action_points(facebook_ids, ga4_ids, google_ads_ids, ua_tags, tiktok_ids, paused_tags, google_ads_issues, grouped_fb_event_issues)
                
                # New section for tag naming conventions
                tag_naming_info = gather_tag_naming_info(tags, trigger_names)

                st.divider()

                # Add checkboxes for toggling analyses
                st.subheader("Select analyses to display:")
                show_tracking_summary = st.checkbox("Tracking ID Summary", value=False)
                show_google_ads = st.checkbox("Google Ads Conversion Tags", value=False)
                show_ga4 = st.checkbox("GA4 Event Tags", value=False)
                show_facebook = st.checkbox("Facebook Event Tags", value=False)
                show_tiktok = st.checkbox("TikTok Event Tags", value=False)
                show_floodlight = st.checkbox("Floodlight Tags", value=False)
                show_naming_conventions = st.checkbox("Tag Naming Conventions", value=False)
                show_tag_summary = st.checkbox("Tag Summary", value=False)

                # Create two columns for layout
                col1, col2 = st.columns([1, 2])

                # Column 1: Findings (always displayed)
                with col1:
                    display_action_points(action_points)
                    st.markdown(
                    """
                    <p style='text-align:center; color: #3f3f'>Built by <a href="https://www.linkedin.com/in/brad-farleigh" target="_blank">Brad Farleigh</a></p>.
                    """, unsafe_allow_html=True
                    )

                # Column 2: Details (display sections based on checkbox selections)
                with col2:
                    # Display Tracking ID Summary if selected and any inconsistencies or IDs exist
                    if show_tracking_summary and any([facebook_ids, ga4_ids, google_ads_ids, ua_tags, tiktok_ids]):
                        display_tracking_id_summary(facebook_ids, ga4_ids, google_ads_ids, ua_tags, tiktok_ids, inconsistencies)
                    
                    # Display Google Ads Conversion Tags if selected and available
                    if show_google_ads and grouped_google_ads_tags:
                        display_google_ads_tags(grouped_google_ads_tags)

                    # Display GA4 Tags if selected and available
                    if show_ga4 and grouped_ga4_tags:
                        display_ga4_tags(grouped_ga4_tags)

                    # Display Facebook Tags if selected and available
                    if show_facebook and grouped_fb_event_tags:
                        display_fb_event_tags(grouped_fb_event_tags)

                    # Display TikTok Tags if selected and available
                    if show_tiktok and grouped_tiktok_tags:
                        display_tiktok_tags(grouped_tiktok_tags)

                    # Display Floodlight Tags if selected and available
                    if show_floodlight and grouped_floodlight_tags:
                        display_floodlight_tags(grouped_floodlight_tags)

                    # Display Tag Naming Conventions if selected
                    if show_naming_conventions:
                        display_tag_naming_conventions(tag_naming_info)

                    # Display Tag Summary if selected and available
                    if show_tag_summary:
                        grouped_tags = group_tags_by_type(tags)
                        if grouped_tags:
                            display_grouped_tags(grouped_tags, trigger_names)
            else:
                st.warning("No tags found in the GTM JSON file.")
        else:
            st.warning("Failed to load GTM data from the JSON file.")
    
    st.divider()

    st.header("🔧 Features coming soon")
    st.markdown(COMING_FEATURES, unsafe_allow_html=True)

if __name__ == "__main__":
    main()