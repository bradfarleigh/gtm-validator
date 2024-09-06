# display.py

import streamlit as st
import pandas as pd
from id_extraction import extract_ga4_id, extract_google_ads_id  # Necessary imports

def display_tracking_id_summary(facebook_ids, ga4_ids, google_ads_ids, ua_ids, tiktok_ids, inconsistencies):
    
    st.subheader("Summary of tracking ID's detected")
    st.markdown(
        """    
        We anlayse your Tags and extract the various tracking ID's being used.

        Make sure you're pushing data to the right places - be sure to validate the ID's against your accounts and measurement plan.
        """
    )
    
    # Prepare data for the table
    data = []
    issues_exist = False  # Initialize the variable to False by default
    
    # Facebook
    if facebook_ids:
        status = "✓" if len(facebook_ids) == 1 else "✗"
        issue = "Multiple Facebook IDs found" if len(facebook_ids) > 1 else ""
        data.append(["Facebook", ", ".join(facebook_ids), status, issue])
        if issue:
            issues_exist = True
    
    # Google Analytics 4 (GA4)
    if ga4_ids:
        status = "✓" if len(ga4_ids) == 1 else "✗"
        issue = "Multiple GA4 Measurement IDs found" if len(ga4_ids) > 1 else ""
        data.append(["Google Analytics 4", ", ".join(ga4_ids), status, issue])
        if issue:
            issues_exist = True
    
    # Google Ads
    if google_ads_ids:
        status = "✓" if len(google_ads_ids) == 1 else "✗"
        issue = "Multiple Google Ads IDs found" if len(google_ads_ids) > 1 else ""
        data.append(["Google Ads", ", ".join(google_ads_ids), status, issue])
        if issue:
            issues_exist = True
    
    # Universal Analytics (UA)
    if ua_ids:
        status = "✓" if len(ua_ids) == 1 else "✗"
        issue = "Multiple Universal Analytics IDs found" if len(ua_ids) > 1 else ""
        data.append(["Universal Analytics", ", ".join(ua_ids), status, issue])
        if issue:
            issues_exist = True
    
    # TikTok
    if tiktok_ids:
        status = "✓" if len(tiktok_ids) == 1 else "✗"
        issue = "Multiple TikTok IDs found" if len(tiktok_ids) > 1 else ""
        data.append(["TikTok", ", ".join(tiktok_ids), status, issue])
        if issue:
            issues_exist = True
    
    # Validate data before creating DataFrame
    if data:
        try:
            # Check if issues exist and create DataFrame accordingly
            if issues_exist:
                df = pd.DataFrame(data, columns=["Platform", "ID", "Status", "Issue"])
            else:
                # Ensure data contains only 3 columns when "Issue" is not needed
                data_without_issue = [row[:3] for row in data]
                df = pd.DataFrame(data_without_issue, columns=["Platform", "ID", "Status"])

            # Display the table
            st.dataframe(df,use_container_width = True)

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
    
    st.divider()
    st.header("🔎 Our findings")
    with st.container(border=True):
        if action_points:
            for point in action_points:
                st.write(f"{point}")
        else:
            st.write("No immediate action required. Your GTM setup appears to be consistent.")
