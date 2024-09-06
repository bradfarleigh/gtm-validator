from id_extraction import extract_facebook_id, extract_ga4_id, extract_google_ads_id, extract_ua_id, extract_tiktok_id
from collections import Counter

# Function to check consistency of tracking IDs and collect relevant information
def check_id_consistency(tags):
    facebook_ids = set()
    ga4_ids = set()
    google_ads_ids = set()
    ua_ids = set()
    tiktok_ids = set()
    paused_tags = []
    inconsistencies = []
    
    for tag in tags:
        if not isinstance(tag, dict):  # Ensure tag is a dictionary
            continue

        if tag.get('paused', False):
            paused_tags.append(tag.get('name', 'Unnamed Tag'))
        
        if tag.get('type') == 'html':
            for param in tag.get('parameter', []):
                if param.get('key') == 'html':
                    html_content = param.get('value', '')
                    fb_id = extract_facebook_id(html_content)
                    if fb_id:
                        facebook_ids.add(fb_id)
                    ua_id = extract_ua_id(html_content)
                    if ua_id:
                        ua_ids.add(ua_id)
                    tiktok_id = extract_tiktok_id(tag)
                    if tiktok_id:
                        tiktok_ids.add(tiktok_id)
        
        elif tag.get('type') in ['gaawe', 'googtag']:
            ga4_id = extract_ga4_id(tag)
            if ga4_id:
                ga4_ids.add(ga4_id)
        
        elif tag.get('type') in ['awct', 'sp']:
            ads_id = extract_google_ads_id(tag)
            if ads_id:
                google_ads_ids.add(ads_id)

    if len(facebook_ids) > 1:
        inconsistencies.append(f"Multiple Facebook IDs found: {', '.join(facebook_ids)}")
    if len(ga4_ids) > 1:
        inconsistencies.append(f"Multiple GA4 Measurement IDs found: {', '.join(ga4_ids)}")
    if len(google_ads_ids) > 1:
        inconsistencies.append(f"Multiple Google Ads IDs found: {', '.join(google_ads_ids)}")
    if len(tiktok_ids) > 1:
        inconsistencies.append(f"Multiple TikTok IDs found: {', '.join(tiktok_ids)}")
    if len(ua_ids) > 1:
        inconsistencies.append(f"Multiple Universal Analytics IDs found: {', '.join(ua_ids)}")

    return facebook_ids, ga4_ids, google_ads_ids, ua_ids, tiktok_ids, paused_tags, inconsistencies

# Function to group Google Ads tags with trigger and conversion details
def group_google_ads_tags(tags, trigger_names):
    google_ads_tags = []
    tag_check = {}
    issues = []
    issue_flags = {}

    for tag in tags:
        if tag['type'] == 'awct':  # Google Ads - Conversion
            ads_id = extract_google_ads_id(tag)
            conversion_label = get_conversion_label(tag)
            tag_name = tag.get('name', 'Unnamed Tag')

            tag_key = (ads_id, conversion_label)
            issue_flag = False

            if tag_key in tag_check:
                issue_flag = True
                issues.append(f"Duplicate Google Ads Conversion Tags found for ID: {ads_id}, Label: {conversion_label}")
                issue_flags[tag_key] = True

            tag_check[tag_key] = tag_name

            trigger_ids = tag.get('firingTriggerId', [])
            triggers = [trigger_names.get(str(tid), f"Unknown Trigger (ID: {tid})") for tid in trigger_ids]

            google_ads_tags.append({
                'Tag Name': tag_name,
                'Tracking ID': ads_id,
                'Conversion Label': conversion_label,
                'Trigger Name': ', '.join(triggers) if triggers else 'No Triggers',
                'Issue': "⚠️ Potential issue: same ID/label, different tag name" if issue_flag else ""
            })
    
    for i, tag in enumerate(google_ads_tags):
        tag_key = (tag['Tracking ID'], tag['Conversion Label'])
        if issue_flags.get(tag_key, False):
            google_ads_tags[i]['Issue'] = "⚠️ Potential issue: same ID/label, different tag name"

    return google_ads_tags, issues

# Helper function to extract conversion label from a Google Ads tag
def get_conversion_label(tag):
    for param in tag.get('parameter', []):
        if param['key'] == 'conversionLabel':
            return param.get('value', 'No Label')
    return 'No Label'

from collections import Counter

# Function to group GA4 tags and flag inconsistent measurement IDs
def group_ga4_tags(tags, trigger_names):
    ga4_tags = []
    ga4_ids = []

    # First, collect all GA4 measurement IDs
    for tag in tags:
        if tag['type'] == 'gaawe':  # GA4 - Event
            ga4_id = extract_ga4_id(tag)
            if ga4_id:
                ga4_ids.append(ga4_id)

    # Count occurrences of each GA4 measurement ID
    ga4_id_counter = Counter(ga4_ids)

    # If more than one unique GA4 ID is found, all should be flagged
    inconsistent_ids = [ga4_id for ga4_id, count in ga4_id_counter.items() if count > 1] if len(ga4_id_counter) > 1 else []

    # Now process the tags and flag those that use an inconsistent GA4 measurement ID
    for tag in tags:
        if tag['type'] == 'gaawe':  # GA4 - Event
            ga4_id = extract_ga4_id(tag)
            event_name = get_event_name(tag)
            tag_name = tag.get('name', 'Unnamed Tag')

            trigger_ids = tag.get('firingTriggerId', [])
            triggers = [trigger_names.get(str(tid), f"Unknown Trigger (ID: {tid})") for tid in trigger_ids]

            # Flag the tag if its GA4 measurement ID is one of the inconsistent ones
            issue = ""
            if ga4_id in inconsistent_ids:
                issue = f"Inconsistent GA4 Measurement ID: {ga4_id} (Found Multiple Unique IDs)"

            ga4_tags.append({
                'Tag Name': tag_name,
                'GA4 Measurement ID': ga4_id,
                'Event Name': event_name,
                'Trigger Name': ', '.join(triggers) if triggers else 'No Triggers',
                'Issue': issue  # Add the issue flag if inconsistent
            })

    return ga4_tags

# Helper function to extract the eventName from the GA4 tag parameters
def get_event_name(tag):
    for param in tag.get('parameter', []):
        if param.get('key') == 'eventName':
            return param.get('value', 'No Event Name')
    return 'No Event Name'