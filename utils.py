# utils.py

from collections import defaultdict
from id_extraction import extract_facebook_id, extract_ga4_id, extract_google_ads_id, extract_ua_id, extract_tiktok_id


# Function to extract trigger names from GTM data
def get_trigger_names(gtm_data):
    trigger_names = {}
    if 'trigger' in gtm_data['containerVersion']:
        for trigger in gtm_data['containerVersion']['trigger']:
            trigger_names[trigger['triggerId']] = trigger['name']
    return trigger_names


# Function to group tags by their type
def group_tags_by_type(tags):
    grouped_tags = defaultdict(list)
    for tag in tags:
        grouped_tags[tag['type']].append(tag)
    return grouped_tags


def check_id_consistency(tags):
    facebook_ids = set()
    ga4_ids = set()
    google_ads_ids = set()
    ua_ids = set()
    tiktok_ids = set()
    paused_tags = []
    inconsistencies = []
    
    for tag in tags:
        # Check for paused tags
        if tag.get('paused', False):
            paused_tags.append(tag['name'])
        
        # Handle HTML tags
        if tag['type'] == 'html':
            html_content = get_html_content(tag)
            fb_id = extract_facebook_id(html_content)
            if fb_id:
                facebook_ids.add(fb_id)
            ua_id = extract_ua_id(html_content)
            if ua_id:
                ua_ids.add(ua_id)
            
            # Unpack the TikTok info correctly
            tiktok_id, email, phone = extract_tiktok_id(html_content)
            if tiktok_id:
                tiktok_ids.add(tiktok_id)
        
        # Handle GA4 tags
        elif tag['type'] in ['gaawe', 'googtag']:
            ga4_id = extract_ga4_id(tag)
            if ga4_id:
                ga4_ids.add(ga4_id)
        
        # Handle Google Ads tags
        elif tag['type'] in ['awct', 'sp']:
            ads_id = extract_google_ads_id(tag)
            if ads_id:
                google_ads_ids.add(ads_id)

    # Identify inconsistencies for each platform
    check_for_inconsistencies(facebook_ids, 'Facebook', inconsistencies)
    check_for_inconsistencies(ga4_ids, 'GA4 Measurement', inconsistencies)
    check_for_inconsistencies(google_ads_ids, 'Google Ads', inconsistencies)
    check_for_inconsistencies(tiktok_ids, 'TikTok', inconsistencies)
    check_for_inconsistencies(ua_ids, 'Universal Analytics', inconsistencies)

    return facebook_ids, ga4_ids, google_ads_ids, ua_ids, tiktok_ids, paused_tags, inconsistencies


# Helper function to check for multiple IDs and add inconsistencies to the list
def check_for_inconsistencies(ids_set, platform_name, inconsistencies):
    if len(ids_set) > 1:
        inconsistencies.append(f"Multiple {platform_name} IDs found: {', '.join(ids_set)}")


# Helper function to extract HTML content from a tag
def get_html_content(tag):
    for param in tag.get('parameter', []):
        if param.get('key') == 'html':
            return param.get('value', '')
    return ''


# Function to generate action points based on the consistency of IDs and paused tags
def generate_action_points(facebook_ids, ga4_ids, google_ads_ids, ua_ids, tiktok_ids, paused_tags):
    action_points = []
    if len(facebook_ids) > 1:
        action_points.append("Consolidate Facebook tracking IDs to use a single ID across all tags")
    if len(ga4_ids) > 1:
        action_points.append("Consolidate GA4 measurement IDs to use a single ID across all tags")
    if len(google_ads_ids) > 1:
        action_points.append("Consolidate Google Ads conversion IDs to use a single ID across all tags")
    if len(tiktok_ids) > 1:
        action_points.append("Consolidate TikTok tracking IDs to use a single ID across all tags")
    if ua_ids:
        action_points.append("Review and delete UA tags as they are no longer collecting data")
    if paused_tags:
        action_points.append(f"Review and decide on the status of paused tags: {', '.join(paused_tags)}")
    if not facebook_ids:
        action_points.append("Consider adding Facebook tracking if it's relevant for your analytics needs")
    if not ga4_ids:
        action_points.append("Implement Google Analytics 4 (GA4) for future-proof analytics")
    if not tiktok_ids:
        action_points.append("Consider adding TikTok tracking if it's relevant for your marketing strategy")
    return action_points


# Function to group Google Ads tags with trigger and conversion details
def group_google_ads_tags(tags, trigger_names):
    google_ads_tags = []
    for tag in tags:
        if tag['type'] in ['awct', 'sp']:  # Assuming these are the types for Google Ads conversion tags
            ads_id = extract_google_ads_id(tag)
            conversion_label = get_conversion_label(tag)
            
            if ads_id:
                # Get the trigger names associated with this tag
                trigger_ids = tag.get('firingTriggerId', [])
                triggers = [trigger_names.get(str(tid), "Unknown Trigger") for tid in trigger_ids]
                
                google_ads_tags.append({
                    'Tag Name': tag.get('name', 'Unnamed Tag'),
                    'Tracking ID': ads_id,
                    'Conversion Label': conversion_label,
                    'Trigger Name': ', '.join(triggers) if triggers else 'No Triggers'
                })
    return google_ads_tags


# Helper function to extract the conversion label from a tag
def get_conversion_label(tag):
    for param in tag.get('parameter', []):
        if param['key'] == 'conversionLabel':
            return param.get('value', 'No Label')
    return 'No Label'

