# This is floodlight_helpers.py

from typing import List, Dict, Any
from trigger_helpers import BUILT_IN_TRIGGERS

def group_floodlight_tags(tags: List[Dict[str, Any]], trigger_names: Dict[str, str]) -> List[Dict[str, str]]:
    """
    Group and extract information from Floodlight tags.

    Args:
    tags (List[Dict[str, Any]]): List of all tags from GTM configuration.
    trigger_names (Dict[str, str]): Dictionary mapping trigger IDs to their names.

    Returns:
    List[Dict[str, str]]: List of dictionaries containing information about each Floodlight tag.
    """
    floodlight_tags = []
    for tag in tags:
        if tag['type'] == 'flc':
            try:
                floodlight_tags.append({
                    'Tag Name': tag.get('name', 'Unnamed Tag'),
                    'Group Tag': get_floodlight_param(tag, 'groupTag'),
                    'Activity Tag': get_floodlight_param(tag, 'activityTag'),
                    'Advertiser ID': get_floodlight_param(tag, 'advertiserId'),
                    'Trigger Name': get_trigger_names(tag.get('firingTriggerId', []), trigger_names)
                })
            except KeyError as e:
                print(f"Error processing Floodlight tag {tag.get('name', 'Unnamed Tag')}: {str(e)}")
    return floodlight_tags

def get_floodlight_param(tag: Dict[str, Any], param_key: str) -> str:
    """
    Extract a specific parameter value from a Floodlight tag.

    Args:
    tag (Dict[str, Any]): The tag dictionary.
    param_key (str): The key of the parameter to extract.

    Returns:
    str: The value of the specified parameter, or 'No Value' if not found.
    """
    for param in tag.get('parameter', []):
        if param['key'] == param_key:
            return param.get('value', 'No Value')
    return 'No Value'

def get_trigger_names(trigger_ids: List[str], trigger_names: Dict[str, str]) -> str:
    """
    Get the names of triggers associated with a tag.

    Args:
    trigger_ids (List[str]): List of trigger IDs associated with the tag.
    trigger_names (Dict[str, str]): Dictionary mapping trigger IDs to their names.

    Returns:
    str: Comma-separated string of trigger names, or 'No Triggers' if none found.
    """
    triggers = [BUILT_IN_TRIGGERS.get(str(tid), trigger_names.get(str(tid), f"Unknown Trigger (ID: {tid})")) for tid in trigger_ids]
    return ', '.join(triggers) if triggers else 'No Triggers'