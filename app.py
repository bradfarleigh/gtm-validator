import streamlit as st
import pandas as pd
from file_operations import load_gtm_json, extract_tags
from id_extraction import extract_facebook_id, extract_ga4_id, extract_google_ads_id, extract_ua_id, extract_tiktok_id
from display import display_tracking_id_summary, display_grouped_tags, display_action_points
from utils import get_trigger_names, group_tags_by_type, check_id_consistency, generate_action_points, group_google_ads_tags, group_floodlight_tags, group_ga4_tags, group_tiktok_tags

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
                grouped_tiktok_tags = group_tiktok_tags(tags, trigger_names)
                
                # Generate action points (including Google Ads issues)
                action_points = generate_action_points(facebook_ids, ga4_ids, google_ads_ids, ua_tags, tiktok_ids, paused_tags, google_ads_issues)
                
                # Display action points (always displayed under the file uploader)
                display_action_points(action_points)
                
                st.header("🔧 The details")

                with st.container(border=True):
                
                    # Create tabs to organize the data display
                    tabs = st.tabs(["Tracking ID Summary", "Google Ads Conversion Tags", "GA4 Tags", "TikTok Tags", "Floodlight Tags", "Tag Summary"])

                    # Tab 1: Tracking ID Summary (including issues)
                    with tabs[0]:
                        display_tracking_id_summary(facebook_ids, ga4_ids, google_ads_ids, ua_tags, tiktok_ids, inconsistencies)
                    
                    # Tab 2: Google Ads Conversion Tags (only if found)
                    with tabs[1]:
                        if grouped_google_ads_tags:
                            st.write("### Google Ads Conversion Tags")

                            st.markdown(
                                """    
                                We analyse your Google Ads Conversion Tags and extract the tracking ID and Labels.

                                Be sure to validate the ID's against your Google Ads conversion configurations, and measurement plan.
                                """
                            )
                            
                            # Create a DataFrame
                            df_ads = pd.DataFrame(grouped_google_ads_tags).reset_index(drop=True)

                            # Define a function to highlight rows with issues
                            def highlight_issues(row):
                                if row['Issue']:  # If there is an issue
                                    return ['background-color: yellow'] * len(row)
                                else:
                                    return [''] * len(row)

                            # Apply highlighting to the DataFrame
                            styled_df = df_ads.style.apply(highlight_issues, axis=1)

                            # Display the styled DataFrame
                            st.dataframe(styled_df)
                        else:
                            st.write("No Google Ads Conversion Tags found.")
                    
                    # Tab 3: GA4 Tags
                    with tabs[2]:
                        if grouped_ga4_tags:
                            st.write("### GA4 - Event Tags")
                            # Create a DataFrame for GA4 tags, including eventName
                            df_ga4 = pd.DataFrame(grouped_ga4_tags).reset_index(drop=True)
                            st.dataframe(df_ga4)
                        else:
                            st.write("No GA4 Tags found.")
                    
                    # Tab 4: TikTok Tags
                    with tabs[3]:
                        if grouped_tiktok_tags:
                            st.write("### TikTok - Event Tags")
                            st.dataframe(pd.DataFrame(grouped_tiktok_tags).reset_index(drop=True))
                        else:
                            st.markdown(
                                """
                                <p style='text-align: center;'>👍 No TikTok Tags found.</p>
                                """, unsafe_allow_html=True
                            )
                
                    # Tab 5: Floodlight Tags (only if found)
                    with tabs[4]:
                        grouped_floodlight_tags = group_floodlight_tags(tags, trigger_names)
                        if grouped_floodlight_tags:
                            st.write("### Floodlight Tags")
                            st.dataframe(pd.DataFrame(grouped_floodlight_tags).reset_index(drop=True))
                        else:
                            st.write("No Floodlight Tags found.")
                    
                    # Tab 6: Tags
                    with tabs[5]:
                        grouped_tags = group_tags_by_type(tags)
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

    st.divider()
    st.markdown(
        """
        Built by <a href="https://www.linkedin.com/in/brad-farleigh" target="_blank">Brad Farleigh</a>.
        """, unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()