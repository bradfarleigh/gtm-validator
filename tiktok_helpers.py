# This is tiktok_helpers.py

from typing import List, Dict, Any

def group_tiktok_tags(tags: List[Dict[str, Any]], trigger_names: Dict[str, str], gtm_data: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Group and extract information from TikTok-related tags.

    Args:
    tags (List[Dict[str, Any]]): List of all tags from GTM configuration.
    trigger_names (Dict[str, str]): Dictionary mapping trigger IDs to their names.
    gtm_data (Dict[str, Any]): The full GTM configuration data.

    Returns:
    List[Dict[str, str]]: List of dictionaries containing information about each TikTok tag.
    """
    tiktok_tags = []
    
    for tag in tags:
        tag_name = tag.get('name', 'Unnamed Tag')
        template_name = get_custom_template_name(tag, gtm_data)

        if template_name == "TikTok Pixel":
            tiktok_id = extract_tiktok_pixel_id(tag)
            event_name = get_event_name(tag)
            
            tiktok_tags.append({
                'Tag Name': tag_name,
                'TikTok Pixel ID': tiktok_id or '✗ Not Found',
                'Event': event_name,
                'Trigger Name': get_trigger_names(tag.get('firingTriggerId', []), trigger_names)
            })

    return tiktok_tags

def extract_tiktok_pixel_id(tag: Dict[str, Any]) -> str:
    """Extract TikTok pixel ID from tag parameters."""
    for param in tag.get('parameter', []):
        if param['key'] == 'pixel_code':
            return param.get('value', 'No Pixel ID')
    return 'No Pixel ID'

def get_event_name(tag: Dict[str, Any]) -> str:
    """Extract event name from tag parameters."""
    for param in tag.get('parameter', []):
        if param['key'] == 'event':
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