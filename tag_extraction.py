# This is tag_extraction.py

from typing import List, Dict, Any, Tuple, Set
from collections import Counter
import re
import streamlit as st
from id_extraction import extract_facebook_id, extract_ga4_id, extract_google_ads_id, extract_ua_id, extract_tiktok_id

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
    ga4_ids = []

    for tag in tags:
        if tag['type'] == 'gaawe':  # GA4 - Event
            ga4_id = extract_ga4_id(tag)
            if ga4_id:
                ga4_ids.append(ga4_id)

    ga4_id_counter = Counter(ga4_ids)

    inconsistent_ids = [ga4_id for ga4_id, count in ga4_id_counter.items() if count > 1] if len(ga4_id_counter) > 1 else []

    for tag in tags:
        if tag['type'] == 'gaawe':  # GA4 - Event
            ga4_id = extract_ga4_id(tag)
            event_name = get_event_name(tag)
            tag_name = tag.get('name', 'Unnamed Tag')

            trigger_ids = tag.get('firingTriggerId', [])
            triggers = [trigger_names.get(str(tid), f"Unknown Trigger (ID: {tid})") for tid in trigger_ids]

            issue = ""
            if ga4_id in inconsistent_ids:
                issue = f"Inconsistent GA4 Measurement ID: {ga4_id} (Found Multiple Unique IDs)"

            ga4_tags.append({
                'Tag Name': tag_name,
                'GA4 Measurement ID': ga4_id,
                'Event Name': event_name,
                'Trigger Name': ', '.join(triggers) if triggers else 'No Triggers',
                'Issue': issue
            })

    return ga4_tags

def group_fb_event_tags(tags: List[Dict[str, Any]], trigger_names: Dict[str, str], gtm_data: Dict[str, Any]) -> Tuple[List[Dict[str, str]], List[str]]:
    """
    Group Facebook event tags and detect issues.

    Args:
    tags (List[Dict[str, Any]]): List of all tags from GTM configuration.
    trigger_names (Dict[str, str]): Dictionary mapping trigger IDs to their names.
    gtm_data (Dict[str, Any]): The full GTM configuration data.

    Returns:
    Tuple[List[Dict[str, str]], List[str]]: List of Facebook event tags and list of issues.
    """
    facebook_event_tags = []
    tag_check = {}
    issues = []

    for tag in tags:
        tag_name = tag.get('name', 'Unnamed Tag')
        template_name = get_custom_template_name(tag, gtm_data)

        if template_name == "Facebook Pixel":
            event_name = get_event_name(tag)
            fb_id = extract_facebook_id(tag)

            trigger_names_str = get_trigger_names(tag.get('firingTriggerId', []), trigger_names)
            
            tag_key = (event_name, tag_name, trigger_names_str)
            
            if tag_key in tag_check:
                issues.append(f"**Facebook:** Duplicate Event Name - {event_name} for tag {tag_name}")

            tag_check[tag_key] = tag_name

            facebook_event_tags.append({
                'Tag Name': tag_name,
                'Facebook Pixel ID': fb_id or '✗ Not Found',
                'Event Name': event_name,
                'Trigger Name': trigger_names_str,
                'Issue': "⚠️ Potential duplicate event name" if tag_key in tag_check else ""
            })

    return facebook_event_tags, issues

def get_event_name(tag: Dict[str, Any]) -> str:
    """Extract event name from tag parameters."""
    for param in tag.get('parameter', []):
        if param['key'] == 'event' or param['key'] == 'standardEventName':
            return param.get('value', 'No Event Name')
    return 'No Event Name'

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