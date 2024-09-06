from collections import defaultdict
from id_extraction import extract_facebook_id, extract_ga4_id, extract_google_ads_id, extract_ua_id, extract_tiktok_id
import re

# Dictionary of built-in GTM trigger IDs and their names
BUILT_IN_TRIGGERS = {
    "2147479553": "All Pages",  # Example of built-in trigger mapping
    # Add other built-in triggers here as necessary
}

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

# Helper function to generate action points
def generate_action_points(facebook_ids, ga4_ids, google_ads_ids, ua_ids, tiktok_ids, paused_tags, google_ads_issues=None):
    action_points = []
    
    if google_ads_issues:
        action_points.extend(google_ads_issues)
    
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
            triggers = [BUILT_IN_TRIGGERS.get(str(tid), trigger_names.get(str(tid), f"Unknown Trigger (ID: {tid})")) for tid in trigger_ids]

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

# Function to group GA4 tags
def group_ga4_tags(tags, trigger_names):
    ga4_tags = []
    for tag in tags:
        if tag['type'] == 'gaawe':  # GA4 - Event
            ga4_id = extract_ga4_id(tag)
            event_name = get_event_name(tag)
            tag_name = tag.get('name', 'Unnamed Tag')

            trigger_ids = tag.get('firingTriggerId', [])
            triggers = [BUILT_IN_TRIGGERS.get(str(tid), trigger_names.get(str(tid), f"Unknown Trigger (ID: {tid})")) for tid in trigger_ids]

            ga4_tags.append({
                'Tag Name': tag_name,
                'GA4 Measurement ID': ga4_id,
                'Event Name': event_name,
                'Trigger Name': ', '.join(triggers) if triggers else 'No Triggers',
            })

    return ga4_tags

# Helper function to extract the eventName from the GA4 tag parameters
def get_event_name(tag):
    for param in tag.get('parameter', []):
        if param.get('key') == 'eventName':
            return param.get('value', 'No Event Name')
    return 'No Event Name'

# Function to group TikTok tags
def group_tiktok_tags(tags, trigger_names):
    tiktok_tags = []

    for tag in tags:
        tag_name = tag.get('name', 'Unnamed Tag')

        # Handle base TikTok Pixel code (HTML tag type with ttq.load())
        if tag['type'] == 'html':
            tiktok_id = None
            html_content = ""
            
            # Extract the HTML content from the tag
            for param in tag.get('parameter', []):
                if param['key'] == 'html':
                    html_content = param.get('value', '')

            # Only process if the content includes 'ttq.load' (indicating it's a TikTok Pixel)
            if 'ttq.load' in html_content:
                tiktok_id_match = re.search(r"ttq\.load\('([A-Z0-9]+)'\)", html_content)
                if tiktok_id_match:
                    tiktok_id = tiktok_id_match.group(1)
                    
                # Get the trigger names associated with this tag
                trigger_ids = tag.get('firingTriggerId', [])
                triggers = [BUILT_IN_TRIGGERS.get(str(tid), trigger_names.get(str(tid), f"Unknown Trigger (ID: {tid})")) for tid in trigger_ids]

                tiktok_tags.append({
                    'Tag Name': tag_name,
                    'TikTok Pixel ID': tiktok_id or '✗ Not Found',
                    'Event': 'Base Pixel',
                    'Trigger Name': ', '.join(triggers) if triggers else 'No Triggers'
                })

        # Handle TikTok event tags (type starts with 'cvt')
        elif tag['type'].startswith('cvt'):
            tiktok_id = extract_tiktok_id(tag)
            event_name = None

            # Extract event name from tag parameters
            for param in tag.get('parameter', []):
                if param['key'] == 'event':
                    event_name = param.get('value', 'No Event Name')

            # Get the trigger names associated with this tag
            trigger_ids = tag.get('firingTriggerId', [])
            triggers = [BUILT_IN_TRIGGERS.get(str(tid), trigger_names.get(str(tid), f"Unknown Trigger (ID: {tid})")) for tid in trigger_ids]

            tiktok_tags.append({
                'Tag Name': tag_name,
                'TikTok Pixel ID': tiktok_id or '',
                'Event': event_name or 'No Event Name',
                'Trigger Name': ', '.join(triggers) if triggers else 'No Triggers',
            })

    return tiktok_tags

# Function to group Floodlight (FLC) tags
def group_floodlight_tags(tags, trigger_names):
    floodlight_tags = []
    for tag in tags:
        if tag['type'] == 'flc':  # Floodlight Tag (FLC)
            # Extract necessary parameters from the Floodlight tag
            grouptag = get_floodlight_param(tag, 'groupTag')
            activitytag = get_floodlight_param(tag, 'activityTag')
            advertiserid = get_floodlight_param(tag, 'advertiserId')
            
            # Get the trigger names associated with this tag
            trigger_ids = tag.get('firingTriggerId', [])
            triggers = [BUILT_IN_TRIGGERS.get(str(tid), trigger_names.get(str(tid), f"Unknown Trigger (ID: {tid})")) for tid in trigger_ids]
            
            # Append the extracted values to the list
            floodlight_tags.append({
                'Tag Name': tag.get('name', 'Unnamed Tag'),
                'Group Tag': grouptag,
                'Activity Tag': activitytag,
                'Advertiser ID': advertiserid,
                'Trigger Name': ', '.join(triggers) if triggers else 'No Triggers'
            })
    return floodlight_tags

# Helper function to extract Floodlight parameters
def get_floodlight_param(tag, param_key):
    for param in tag.get('parameter', []):
        if param['key'] == param_key:
            return param.get('value', 'No Value')
    return 'No Value'

# Function to extract variables from GTM data
def extract_variables(gtm_data):
    variables = {}
    if 'variable' in gtm_data['containerVersion']:
        for variable in gtm_data['containerVersion']['variable']:
            variable_name = variable.get('name', '')
            variable_value = None
            for param in variable.get('parameter', []):
                if param.get('key') == 'name':
                    variable_value = param.get('value', 'Unknown')
            if variable_name and variable_value:
                variables[variable_name] = variable_value
    return variables

# Function to replace placeholders in tag parameters with variable values
def replace_variable_placeholders(value, variables):
    if '{{' in value and '}}' in value:
        var_name = value.strip('{}')
        if var_name in variables:
            return f"{{{{{var_name}}}}} - {variables[var_name]}"
    return value