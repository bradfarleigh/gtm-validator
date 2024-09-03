import streamlit as st
import json
import pandas as pd
import re

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

def extract_facebook_id(html_content):
    match = re.search(r'https://www\.facebook\.com/tr\?id=(\d+)&ev=PageView&noscript=1', html_content)
    return match.group(1) if match else None

def extract_ga4_id(tag):
    if tag['type'] in ['gaawe', 'googtag']:
        for param in tag['parameter']:
            if param['key'] in ['measurementIdOverride', 'tagId']:
                return param['value']
    return None

def extract_google_ads_id(tag):
    if tag['type'] == 'awct' or tag['type'] == 'sp':
        for param in tag['parameter']:
            if param['key'] == 'conversionId':
                return param['value']
    return None

def get_trigger_names(gtm_data):
    trigger_names = {}
    if 'trigger' in gtm_data['containerVersion']:
        for trigger in gtm_data['containerVersion']['trigger']:
            trigger_names[trigger['triggerId']] = trigger['name']
    return trigger_names

def check_id_consistency(tags):
    facebook_ids = set()
    ga4_ids = set()
    google_ads_ids = set()
    ua_tags = []
    paused_tags = []
    inconsistencies = []
    
    for tag in tags:
        if tag.get('paused', False):
            paused_tags.append(tag['name'])
        
        if tag['type'] == 'html' and 'Facebook' in tag['name']:
            for param in tag['parameter']:
                if param['key'] == 'html':
                    fb_id = extract_facebook_id(param.get('value', ''))
                    if fb_id:
                        facebook_ids.add(fb_id)
        elif tag['type'] in ['gaawe', 'googtag']:
            ga4_id = extract_ga4_id(tag)
            if ga4_id:
                ga4_ids.add(ga4_id)
        elif tag['type'] in ['awct', 'sp']:
            ads_id = extract_google_ads_id(tag)
            if ads_id:
                google_ads_ids.add(ads_id)
        elif tag['type'] == 'ua':
            ua_tags.append(tag['name'])

    if len(facebook_ids) > 1:
        inconsistencies.append(f"Multiple Facebook IDs found: {', '.join(facebook_ids)}")
    if len(ga4_ids) > 1:
        inconsistencies.append(f"Multiple GA4 Measurement IDs found: {', '.join(ga4_ids)}")
    if len(google_ads_ids) > 1:
        inconsistencies.append(f"Multiple Google Ads IDs found: {', '.join(google_ads_ids)}")

    return facebook_ids, ga4_ids, google_ads_ids, ua_tags, paused_tags, inconsistencies

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

def main():
    st.title("GTM Tag Explorer and Validator")
    
    uploaded_file = st.file_uploader("Upload GTM JSON file", type="json")
    
    if uploaded_file is not None:
        gtm_data = load_gtm_json(uploaded_file)
        
        if gtm_data:
            tags = extract_tags(gtm_data)
            trigger_names = get_trigger_names(gtm_data)
            
            if tags:
                facebook_ids, ga4_ids, google_ads_ids, ua_tags, paused_tags, inconsistencies = check_id_consistency(tags)
                
                st.header("Tracking ID Summary")
                st.subheader("Facebook")
                if facebook_ids:
                    st.write(f"Tracking ID(s): {', '.join(facebook_ids)}")
                    st.write(f"Status: {'Consistent' if len(facebook_ids) == 1 else 'Inconsistent'}")
                else:
                    st.write("No Facebook tracking ID found")
                
                st.subheader("Google Analytics 4 (GA4)")
                if ga4_ids:
                    st.write(f"Measurement ID(s): {', '.join(ga4_ids)}")
                    st.write(f"Status: {'Consistent' if len(ga4_ids) == 1 else 'Inconsistent'}")
                else:
                    st.write("No GA4 measurement ID found")
                
                st.subheader("Google Ads")
                if google_ads_ids:
                    st.write(f"Conversion ID(s): {', '.join(google_ads_ids)}")
                    st.write(f"Status: {'Consistent' if len(google_ads_ids) == 1 else 'Inconsistent'}")
                else:
                    st.write("No Google Ads conversion ID found")
                
                st.subheader("Universal Analytics (UA)")
                if ua_tags:
                    st.write("Redundant UA tags found:")
                    for ua_tag in ua_tags:
                        st.write(f"- {ua_tag}")
                else:
                    st.write("No redundant UA tags found")
                
                if inconsistencies:
                    st.header("Inconsistencies")
                    for inconsistency in inconsistencies:
                        st.warning(inconsistency)
                else:
                    st.success("No inconsistencies found in tracking IDs")
                
                st.header("All Tags")
                for tag in tags:
                    display_tag_details(tag, trigger_names)
                
                st.header("Action Points")
                action_points = []
                if len(facebook_ids) > 1:
                    action_points.append("Consolidate Facebook tracking IDs to use a single ID across all tags")
                if len(ga4_ids) > 1:
                    action_points.append("Consolidate GA4 measurement IDs to use a single ID across all tags")
                if len(google_ads_ids) > 1:
                    action_points.append("Consolidate Google Ads conversion IDs to use a single ID across all tags")
                if ua_tags:
                    action_points.append("Remove or update redundant Universal Analytics (UA) tags to GA4")
                if paused_tags:
                    action_points.append(f"Review and decide on the status of paused tags: {', '.join(paused_tags)}")
                if not facebook_ids:
                    action_points.append("Consider adding Facebook tracking if it's relevant for your analytics needs")
                if not ga4_ids:
                    action_points.append("Implement Google Analytics 4 (GA4) for future-proof analytics")
                
                if action_points:
                    for point in action_points:
                        st.write(f"- {point}")
                else:
                    st.write("No immediate action required. Your GTM setup appears to be consistent.")
            else:
                st.warning("No tags found in the GTM JSON file.")
    else:
        st.info("Please upload a GTM JSON file to begin.")

if __name__ == "__main__":
    main()