# This is display.py


import streamlit as st
import pandas as pd
from typing import List, Dict
from id_extraction import extract_facebook_id, extract_ga4_id, extract_google_ads_id, extract_ua_id, extract_tiktok_id


def display_tracking_id_summary(facebook_ids, ga4_ids, google_ads_ids, ua_ids, tiktok_ids, inconsistencies):
    st.header("Detected tracking ID's")
    st.markdown(
        """    
        We analyse your Tags and extract the various tracking ID's being used.

        Make sure you're pushing data to the right places - be sure to validate the ID's against your accounts and measurement plan.
        """
    )
    
    data = []
    issues_exist = False

    def check_for_mixed_variables(ids):
        plain_strings = any('{{' not in id for id in ids)
        variable_strings = any('{{' in id for id in ids)
        return plain_strings and variable_strings
    
    def add_platform_data(platform, ids, status_check):
        nonlocal issues_exist
        if ids:
            status = "✓" if status_check else "✗"
            issue = f"Multiple {platform} IDs found" if not status_check else ""
            
            if check_for_mixed_variables(ids):
                issue += " | Mix of static and variable IDs found, which may cause tracking inconsistencies."
            
            data.append([platform, ", ".join(ids), status, issue])
            if issue:
                issues_exist = True
        elif platform != "Universal Analytics":  # Only add row for missing IDs if it's not UA
            data.append([platform, "No ID found", "✗", f"No {platform} ID detected"])
            issues_exist = True

    add_platform_data("Facebook", facebook_ids, len(facebook_ids) <= 1)
    add_platform_data("Google Analytics 4", ga4_ids, len(ga4_ids) <= 1)
    add_platform_data("Google Ads", google_ads_ids, len(google_ads_ids) <= 1)
    if ua_ids:  # Only add UA row if UA IDs are found
        add_platform_data("Universal Analytics", ua_ids, len(ua_ids) <= 1)
    add_platform_data("TikTok", tiktok_ids, len(tiktok_ids) <= 1)

    if data:
        try:
            if issues_exist:
                df = pd.DataFrame(data, columns=["Platform", "ID", "Status", "Issue"])
            else:
                df = pd.DataFrame(data, columns=["Platform", "ID", "Status"])
            st.dataframe(df, use_container_width=True, hide_index=True)
        except ValueError as e:
            st.error(f"Error creating DataFrame: {e}")
    else:
        st.write("No Tracking IDs found.")

def display_inconsistencies(inconsistencies):
    if inconsistencies:
        st.header("Inconsistencies")
        for inconsistency in inconsistencies:
            st.warning(inconsistency)
    else:
        st.success("No inconsistencies found in tracking IDs")

def display_grouped_tags(grouped_tags, trigger_names):
    st.header("Summary of all tags")
    for tag_type, type_tags in grouped_tags.items():
        st.subheader(f"Type: {tag_type}")
        for tag in type_tags:
            display_tag_details(tag, trigger_names)

def display_tag_details(tag, trigger_names):
    title = f"Tag: {tag['name']}"
    if tag.get('paused', False):
        title += " (Paused)"
    
    with st.expander(title):
        st.write(f"Type: {tag['type']}")
        st.write(f"Status: {'Active' if not tag.get('paused', False) else 'Paused'}")
        
        if tag['type'] == 'html':
            for param in tag['parameter']:
                if param['key'] == 'html':
                    st.write("HTML Content:")
                    st.code(param.get('value', ''), language='html')
        elif tag['type'] in ['gaawe', 'googtag']:
            ga4_id = extract_ga4_id(tag)
            if ga4_id:
                st.write(f"GA4 Measurement ID: {ga4_id}")
        elif tag['type'] in ['awct', 'sp']:
            ads_id = extract_google_ads_id(tag)
            if ads_id:
                st.write(f"Google Ads ID: {ads_id}")
        
        if 'parameter' in tag:
            st.write("Parameters:")
            for param in tag['parameter']:
                if param['key'] != 'html':
                    value = param.get('value', 'N/A')
                    st.write(f"- {param['key']}: {value}")
        
        if 'firingTriggerId' in tag:
            st.write("Firing Triggers:")
            for trigger_id in tag['firingTriggerId']:
                trigger_name = trigger_names.get(trigger_id, "Unknown Trigger")
                st.write(f"- {trigger_name} (ID: {trigger_id})")

def display_action_points(action_points):
    # Remove duplicate action points
    action_points = list(set(action_points))

    with st.container(border=True):
        st.subheader("Summary")

        if action_points:
            for point in action_points:
                st.write(f"- {point}")
        else:
            st.write("No immediate action required. Your GTM setup appears to be consistent.")

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

def display_tag_naming_conventions(tag_naming_info: List[Dict[str, str]]):
    st.header("Tag Naming Conventions")
    st.markdown(
        """
        This section provides an overview of your tag names, types, and associated triggers. 
        It also assesses the naming conventions based on the provided guidelines.
        """
    )
    
    df = pd.DataFrame(tag_naming_info)
    
    # Display the dataframe
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Display detailed explanations for tags with issues
    # st.subheader("Detailed Naming Convention Issues")
    # for tag in tag_naming_info:
    #    if tag['Naming Convention'] != "✅ Acceptable":
    #        st.markdown(f"**{tag['Tag Name']}**: {tag['Naming Convention']}")
    #        st.markdown(f"- {tag['Details']}")

def assess_naming_convention(tag_name: str) -> str:
    # This is a basic assessment. You can expand this function to include more specific rules.
    if not tag_name or tag_name == 'Unnamed Tag':
        return "❌ Missing name"
    elif len(tag_name) < 5:
        return "⚠️ Name might be too short"
    elif len(tag_name) > 50:
        return "⚠️ Name might be too long"
    else:
        return "✅ Acceptable"