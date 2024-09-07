from typing import List, Dict, Any, Tuple, Set
from collections import Counter
import re
from id_extraction import extract_facebook_id, extract_ga4_id, extract_google_ads_id, extract_ua_id, extract_tiktok_id, resolve_variable

def check_id_consistency(tags, variables, gtm_data):
    facebook_ids = set()
    ga4_ids = set()
    google_ads_ids = set()
    ua_ids = set()
    tiktok_ids = set()
    paused_tags = []
    inconsistencies = []
    
    # First, try to find the Facebook Pixel ID from the PageView event
    for tag in tags:
        if tag['type'].startswith('cvt_'):
            for param in tag.get('parameter', []):
                if param.get('key') == 'standardEventName' and param.get('value') == 'PageView':
                    fb_id = extract_facebook_id(tag, gtm_data)
                    if fb_id:
                        facebook_ids.add(fb_id)
                        break
            if facebook_ids:
                break  # Stop if we've found the PageView event

    # If we didn't find a Facebook ID from PageView, check all tags
    if not facebook_ids:
        for tag in tags:
            fb_id = extract_facebook_id(tag, gtm_data)
            if fb_id:
                facebook_ids.add(fb_id)

    for tag in tags:
        if not isinstance(tag, dict):
            continue

        if tag.get('paused', False):
            paused_tags.append(tag.get('name', 'Unnamed Tag'))
        
        if tag.get('type') == 'html':
            for param in tag.get('parameter', []):
                if param.get('key') == 'html':
                    html_content = param.get('value', '')
                    ua_id = extract_ua_id(html_content)
                    if ua_id:
                        ua_ids.add(ua_id)
        
        elif tag.get('type') in ['gaawe', 'googtag']:
            ga4_id = extract_ga4_id(tag)
            if ga4_id.startswith('{{'):
                ga4_id = resolve_variable(ga4_id.strip('{}'), variables) or ga4_id
            if ga4_id != 'No Measurement ID':
                ga4_ids.add(ga4_id)
        
        elif tag.get('type') in ['awct', 'sp']:
            ads_id = extract_google_ads_id(tag)
            if ads_id != 'No Conversion ID':
                google_ads_ids.add(ads_id)

        tiktok_id = extract_tiktok_id(tag)
        if tiktok_id and tiktok_id != 'No Pixel ID':
            tiktok_ids.add(tiktok_id)

    # Check for inconsistencies
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
                issues.append(f"**Google Ads:** Duplicate Google Ads Conversion Tags found for ID - {ads_id}, Label: {conversion_label}")
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

def get_conversion_label(tag):
    for param in tag.get('parameter', []):
        if param['key'] == 'conversionLabel':
            return param.get('value', 'No Label')
    return 'No Label'

def group_ga4_tags(tags, trigger_names):
    ga4_tags = []
    ga4_ids = set()

    for tag in tags:
        if tag['type'] == 'gaawe':  # GA4 - Event
            ga4_id = extract_ga4_id(tag)
            event_name = get_event_name(tag)
            tag_name = tag.get('name', 'Unnamed Tag')

            trigger_ids = tag.get('firingTriggerId', [])
            triggers = [trigger_names.get(str(tid), f"Unknown Trigger (ID: {tid})") for tid in trigger_ids]

            ga4_tags.append({
                'Tag Name': tag_name,
                'GA4 Measurement ID': ga4_id,
                'Event Name': event_name,
                'Trigger Name': ', '.join(triggers) if triggers else 'No Triggers',
                'Issue': ""
            })

            ga4_ids.add(ga4_id)

    # Check for multiple GA4 IDs after processing all tags
    if len(ga4_ids) > 1:
        issue = f"Multiple GA4 Measurement IDs found: {', '.join(ga4_ids)}"
        for tag in ga4_tags:
            tag['Issue'] = issue

    return ga4_tags

def group_fb_event_tags(tags: List[Dict[str, Any]], trigger_names: Dict[str, str], gtm_data: Dict[str, Any]) -> Tuple[List[Dict[str, str]], List[str]]:
    facebook_event_tags = []
    tag_check = {}
    issues = []

    for tag in tags:
        tag_name = tag.get('name', 'Unnamed Tag')
        template_name = get_custom_template_name(tag, gtm_data)
        is_html_tag = tag['type'] == 'html'

        if template_name == "Facebook Pixel" or (is_html_tag and 'fbq' in str(tag)):
            event_name = get_event_name(tag)
            fb_id = extract_facebook_id(tag, gtm_data) if not is_html_tag else 'N/A for HTML tags'

            trigger_names_str = get_trigger_names(tag.get('firingTriggerId', []), trigger_names)
            
            # Use both event name and pixel ID as the key, but only for non-HTML tags
            tag_key = (event_name, fb_id) if not is_html_tag else None
            
            if tag_key and tag_key in tag_check:
                issues.append(f"**Facebook:** Duplicate Event - '{event_name}' for Pixel ID '{fb_id}' in tags '{tag_name}' and '{tag_check[tag_key]}'")
                facebook_event_tags.append({
                    'Tag Name': tag_name,
                    'Facebook Pixel ID': fb_id,
                    'Event Name': event_name,
                    'Trigger Name': trigger_names_str,
                    'Issue': "⚠️ Duplicate event for this Pixel ID" if not is_html_tag else ""
                })
            else:
                if tag_key:
                    tag_check[tag_key] = tag_name
                facebook_event_tags.append({
                    'Tag Name': tag_name,
                    'Facebook Pixel ID': fb_id,
                    'Event Name': event_name,
                    'Trigger Name': trigger_names_str,
                    'Issue': ""
                })

    return facebook_event_tags, issues

def get_event_name(tag: Dict[str, Any]) -> str:
    """Extract event name from tag parameters."""
    event_name = 'No Event Name'
    custom_event_name = None
    
    if tag['type'].startswith('cvt_'):
        # For custom template (CVT) tags
        for param in tag.get('parameter', []):
            if param['key'] == 'standardEventName':
                event_name = param.get('value', 'No Event Name')
            elif param['key'] == 'customEventName':
                custom_event_name = param.get('value', '')
    else:
        # For HTML tags
        for param in tag.get('parameter', []):
            if param['key'] == 'html':
                html_content = param.get('value', '')
                event_match = re.search(r"fbq\s*\(\s*['\"](?:track|trackCustom)['\"],\s*['\"]([\w\s]+)['\"]\s*[,)]", html_content)
                if event_match:
                    event_name = event_match.group(1)
                break

    # If we have a custom event name, use that
    if custom_event_name:
        return custom_event_name
    
    return event_name

def get_trigger_names(trigger_ids: List[str], trigger_names: Dict[str, str]) -> str:
    """Get trigger names for a tag."""
    triggers = [trigger_names.get(str(tid), f"Unknown Trigger (ID: {tid})") for tid in trigger_ids]
    return ', '.join(triggers) if triggers else 'No Triggers'

def get_custom_template_name(tag: Dict[str, Any], gtm_data: Dict[str, Any]) -> str:
    """
    Extract the custom template name for a given tag.

    Args:
    tag (Dict[str, Any]): The tag dictionary.
    gtm_data (Dict[str, Any]): The full GTM configuration data.

    Returns:
    str: The name of the custom template, or None if not found.
    """
    if tag['type'].startswith('cvt_'):
        template_id = tag['type'].split('_')[-1]
        for template in gtm_data.get('containerVersion', {}).get('customTemplate', []):
            if template.get('templateId') == template_id:
                return template.get('name')
    return None

def gather_tag_naming_info(tags: List[Dict[str, Any]], trigger_names: Dict[str, str]) -> List[Dict[str, str]]:
    tag_naming_info = []
    
    for tag in tags:
        tag_name = tag.get('name', 'Unnamed Tag')
        tag_type = tag.get('type', 'Unknown Type')
        
        # Get trigger names
        trigger_ids = tag.get('firingTriggerId', [])
        triggers = [trigger_names.get(str(tid), f"Unknown Trigger (ID: {tid})") for tid in trigger_ids]
        trigger_names_str = ', '.join(triggers) if triggers else 'No Triggers'
        
        tag_naming_info.append({
            'Tag Name': tag_name,
            'Tag Type': tag_type,
            'Trigger Name': trigger_names_str
        })
    
    return tag_naming_info

# Make sure to export all the functions you want to use in other files
__all__ = [
    'check_id_consistency',
    'group_google_ads_tags',
    'group_ga4_tags',
    'group_fb_event_tags',
    'get_event_name',
    'get_trigger_names',
    'get_custom_template_name'
]