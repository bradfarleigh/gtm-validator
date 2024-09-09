from typing import List, Dict, Any
import re

# Define valid platform prefixes
VALID_PLATFORMS = {
    'FB': 'Facebook',
    'GA4': 'Google Analytics 4',
    'GA': 'Google Analytics',
    'GADS': 'Google Ads',
    'TT': 'TikTok',
    'DCM': 'DoubleClick',
    'TTD': 'The Trade Desk',
    'FL': 'Floodlight',
    'HS': 'HubSpot',
    'LI': 'LinkedIn',
    'Clarity': 'Microsoft Clarity',
    'Microsoft Clarity' : 'Microsoft Clarity',
    'Conversion Linker' : 'Conversion Linker',
    # Add more platform prefixes as needed
}

# Define mapping of tag types to suggested prefixes
TAG_TYPE_TO_PREFIX = {
    'ua': 'GA',
    'gaawc': 'GA4',
    'gaawe': 'GA4',
    'awct': 'Google Ads',
    'sp': 'Google Ads - Remarketing',
    'flc': 'FL',
    # Add more mappings as needed
}

# Define whitelisted tags
WHITELISTED_TAGS = {
    'Conversion Linker',
    # Add more whitelisted tag names here
}

def assess_naming_convention(tag_name: str, tag_type: str) -> Dict[str, str]:
    if not tag_name or tag_name == 'Unnamed Tag':
        return {"overall": "❌ Missing name", "details": "Tag name is missing or unnamed."}

    # Check if the tag is whitelisted
    if tag_name in WHITELISTED_TAGS:
        return {"overall": "✅ Whitelisted", "details": "This tag name is whitelisted and exempt from naming convention checks."}

    # Check for separators
    if '|' in tag_name:
        separator = '|'
        parts = tag_name.split(separator)
    elif '-' in tag_name:
        separator = '-'
        parts = tag_name.split(separator)
    else:
        separator = '-'  # Default separator if none is found
        parts = [tag_name]  # Treat the whole name as one part

    # Check platform prefix in first or second slot
    for i in range(min(2, len(parts))):
        part = parts[i].strip()
        platform_prefix = next((prefix for prefix in VALID_PLATFORMS.keys() if part.upper().startswith(prefix)), None)
        if platform_prefix:
            if len(parts) < 2:
                return {"overall": "⚠️ Insufficient parts", "details": f"Tag name should have at least 2 parts when using a separator."}
            return {"overall": "✅ Acceptable", "details": "Tag name follows the naming convention guidelines."}

    # Suggest prefix based on tag type if no valid prefix found
    suggested_prefix = TAG_TYPE_TO_PREFIX.get(tag_type.lower())
    if suggested_prefix:
        suggested_name = f"{suggested_prefix} {separator} {separator.join(parts)}"
        example = f"Consider adding the prefix '{suggested_prefix}'. Instead of '{tag_name}' use '{suggested_name}'"
        return {"overall": "⚠️ Missing prefix", "details": example}

    return {"overall": "❌ Invalid platform prefix", "details": f"No recognized platform prefix found, and unable to suggest a prefix based on the tag type '{tag_type}'."}

def gather_tag_naming_info(tags: List[Dict[str, Any]], trigger_names: Dict[str, str]) -> List[Dict[str, str]]:
    tag_naming_info = []
    
    for tag in tags:
        tag_name = tag.get('name', 'Unnamed Tag')
        tag_type = tag.get('type', 'Unknown Type')
        
        # Get trigger names
        trigger_ids = tag.get('firingTriggerId', [])
        triggers = [trigger_names.get(str(tid), f"Unknown Trigger (ID: {tid})") for tid in trigger_ids]
        trigger_names_str = ', '.join(triggers) if triggers else 'No Triggers'
        
        assessment_result = assess_naming_convention(tag_name, tag_type)
        
        tag_naming_info.append({
            'Tag Name': tag_name,
            'Tag Type': tag_type,
            'Trigger Name': trigger_names_str,
            'Naming Convention': assessment_result['overall'],
            'Details': assessment_result['details']
        })
    
    return tag_naming_info

__all__ = ['gather_tag_naming_info', 'assess_naming_convention', 'WHITELISTED_TAGS']