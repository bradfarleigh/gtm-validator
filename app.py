import streamlit as st
import pandas as pd
from file_operations import load_gtm_json, extract_tags
from id_extraction import extract_facebook_id, extract_ga4_id, extract_google_ads_id, extract_ua_id, extract_tiktok_id
from display import display_tracking_id_summary, display_grouped_tags, display_action_points
from utils import get_trigger_names, group_tags_by_type, check_id_consistency, generate_action_points, group_google_ads_tags, group_floodlight_tags, group_ga4_tags, group_tiktok_tags, group_fb_event_tags

# Set the page configuration to full width
st.set_page_config(page_title="GTM Tag Explorer and Validator", layout="wide")

def main():

    st.title("🎯 Validate and Analyse Your Google Tag Manager Setup")

    st.markdown(
        """
        Our tool simplifies the process of reviewing and validating your Google Tag Manager (GTM) configuration. 
        
        ### Use it to:

        - 🔍 **Get a summary** of the tags firing in your GTM container.
        - 📊 **Check platform tracking IDs** (e.g., Facebook Pixel, GA4, TikTok Pixel) to ensure alignment with your measurement plan and quickly catch any misconfigurations.
        - 🚨 **Detect multiple IDs** being used across tags (e.g., multiple Facebook accounts used incorrectly).
        - 🔄 **Identify redundant Universal Analytics (UA) tags**.
        - ❗ **Flag duplicate Google Conversion Tags**, which might indicate incorrect ID usage.
        - 🌐 **Examine Floodlight tag usage** and detect duplicates.
        
        # 🚀 **Getting Started**

        1. **Export** your GTM configuration (Google Tag Manager > Admin > Export Container).
        2. **Upload** the `.json` file here.
        
        Tip: We can **analyse** both published and draft workspaces to help you spot-check and verify your setup before publishing.
        """, unsafe_allow_html=True
    )

    # File uploader for the GTM JSON file
    uploaded_file = st.file_uploader("Upload your GTM JSON file", type="json")
    
    if uploaded_file is not None:
        # Load and parse the GTM JSON data
        gtm_data = load_gtm_json(uploaded_file)
        
        if gtm_data:
            tags = extract_tags(gtm_data)
            trigger_names = get_trigger_names(gtm_data)
            
            if tags:
                # Check for inconsistencies and collect tracking IDs
                facebook_ids, ga4_ids, google_ads_ids, ua_tags, tiktok_ids, paused_tags, inconsistencies = check_id_consistency(tags)
                
                # Google Ads Conversion Tags and Issues
                grouped_google_ads_tags, google_ads_issues = group_google_ads_tags(tags, trigger_names)
                grouped_ga4_tags = group_ga4_tags(tags, trigger_names)
                grouped_fb_event_tags, grouped_fb_event_issues = group_fb_event_tags(tags, trigger_names)
                grouped_tiktok_tags = group_tiktok_tags(tags, trigger_names)
                grouped_floodlight_tags = group_floodlight_tags(tags, trigger_names)

                # Generate action points (including Google Ads issues)
                action_points = generate_action_points(facebook_ids, ga4_ids, google_ads_ids, ua_tags, tiktok_ids, paused_tags, google_ads_issues, grouped_fb_event_issues)
                
                st.divider()

                # Create two columns for layout
                col1, col2 = st.columns([1, 2])

                # Column 1: Findings
                with col1:
                    # Display action points (always displayed under the file uploader)
                    display_action_points(action_points)
                    st.markdown(
                    """
                    <p style='text-align:center; color: #3f3f'>Built by <a href="https://www.linkedin.com/in/brad-farleigh" target="_blank">Brad Farleigh</a></p>.
                    """, unsafe_allow_html=True
                    )

                # Column 2: Details (display sections sequentially without tabs)
                with col2:
                    # Display Tracking ID Summary if any inconsistencies or IDs exist
                    if any([facebook_ids, ga4_ids, google_ads_ids, ua_tags, tiktok_ids]):
                        display_tracking_id_summary(facebook_ids, ga4_ids, google_ads_ids, ua_tags, tiktok_ids, inconsistencies)
                    
                    # Display Google Ads Conversion Tags if available
                    if grouped_google_ads_tags:
                        display_google_ads_tags(grouped_google_ads_tags)

                    # Display GA4 Tags if available
                    if grouped_ga4_tags:
                        display_ga4_tags(grouped_ga4_tags)

                    # Display Facebook Tags if available
                    if grouped_fb_event_tags:
                        display_fb_event_tags(grouped_fb_event_tags)

                    # Display TikTok Tags if available
                    if grouped_tiktok_tags:
                        display_tiktok_tags(grouped_tiktok_tags)

                    # Display Floodlight Tags if available
                    if grouped_floodlight_tags:
                        display_floodlight_tags(grouped_floodlight_tags)

                    # Display Tag Summary if available
                    if grouped_tags := group_tags_by_type(tags):
                        display_grouped_tags(grouped_tags, trigger_names)
            else:
                st.warning("No tags found in the GTM JSON file.")
        else:
            st.warning("Failed to load GTM data from the JSON file.")
    
    st.divider()

    st.header("🔧 Features coming soon")

    st.markdown(
        """
        - 🏷️ **Best practice checks** for tag naming conventions.
        - 🛠️ **Variable naming convention** validation.
        - 📈 **GA4 event naming validation** against best practices.
        - 🗑️ **Duplicate or redundant tag detection**.
        - 🛑 **GA4 custom dimensions flagging**.
        - 🛠️ **Natural language analysis of tag, variable and trigger names**.
        - **Validation vs measurement plan**.

        Want to see a feature added? <a href="https://www.linkedin.com/in/brad-farleigh" target="_blank">Hit me up</a>.
        """, unsafe_allow_html=True
    )


def style_dataframe(df):
    # Define a function to highlight rows with issues
    def highlight_issues(row):
        return ['background-color: #ffcccb' if row.get('Issue', '') else '' for _ in row]
    
    # Check if "Issue" column exists and if there are any issues
    if 'Issue' in df.columns:
        if df['Issue'].str.strip().any():  # If there are any issues
            styled_df = df.style.apply(highlight_issues, axis=1)
        else:
            # If there are no issues, drop the "Issue" column
            styled_df = df.drop(columns=['Issue']).style
    else:
        # If no "Issue" column exists, return the styled DataFrame as is
        styled_df = df.style
    
    return styled_df
    
def display_google_ads_tags(grouped_google_ads_tags):
    st.header("Google Ads Conversion Tags")
    st.markdown(
        """    
        We analyse your Google Ads Conversion Tags and extract the tracking ID and Labels.
        Be sure to validate the ID's against your Google Ads conversion configurations, and measurement plan.
        """
    )
    df_ads = pd.DataFrame(grouped_google_ads_tags).reset_index(drop=True)
    styled_df = style_dataframe(df_ads)
    st.dataframe(styled_df, use_container_width=True,hide_index=True)


def display_fb_event_tags(grouped_fb_tags):
    st.header("Facebook - Event Tags")
    df_fb = pd.DataFrame(grouped_fb_tags).reset_index(drop=True)
    styled_df = style_dataframe(df_fb)
    st.dataframe(styled_df, use_container_width=True,hide_index=True)


def display_ga4_tags(grouped_ga4_tags):
    st.header("GA4 - Event Tags")
    df_ga4 = pd.DataFrame(grouped_ga4_tags).reset_index(drop=True)
    styled_df = style_dataframe(df_ga4)
    st.dataframe(styled_df, use_container_width=True,hide_index=True)

def display_tiktok_tags(grouped_tiktok_tags):
    st.header("TikTok - Event Tags")
    df_tiktok = pd.DataFrame(grouped_tiktok_tags).reset_index(drop=True)
    styled_df = style_dataframe(df_tiktok)
    st.dataframe(styled_df, use_container_width=True,hide_index=True)

def display_floodlight_tags(grouped_floodlight_tags):
    st.header("Floodlight Tags")
    df_floodlight = pd.DataFrame(grouped_floodlight_tags).reset_index(drop=True)
    styled_df = style_dataframe(df_floodlight)
    st.dataframe(styled_df, use_container_width=True,hide_index=True)

if __name__ == "__main__":
    main()