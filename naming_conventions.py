from typing import List, Dict, Any
import re

# Define valid platform prefixes
VALID_PLATFORMS = {
    'FB': 'Facebook',
    'GA': 'Google Analytics',
    'AW': 'Google Ads',
    'TT': 'TikTok',
    'DCM': 'DoubleClick',
    'TTD': 'The Trade Desk',
    'FL' : 'Floodlight',
    'FB' : 'Facebook',
    'HS' : 'Hubspot',
    'HS' : 'HubSpot',
    'GA4' : 'Google Analytics 4',
    'LI' : 'LinkedIn'
    # Add more platform prefixes as needed
}

def assess_naming_convention(tag_name: str) -> Dict[str, str]:
    if not tag_name or tag_name == 'Unnamed Tag':
        return {"overall": "❌ Missing name", "details": "Tag name is missing or unnamed."}

    # Check for separators
    if '|' in tag_name:
        separator = '|'
        parts = tag_name.split(separator)
    elif '-' in tag_name:
        separator = '-'
        parts = tag_name.split(separator)
    else:
        separator = None
        parts = [tag_name]  # Treat the whole name as one part

    # Check platform prefix
    first_part = parts[0].strip()
    platform_prefix = next((prefix for prefix in VALID_PLATFORMS.keys() if first_part.upper().startswith(prefix)), None)

    if platform_prefix:
        if separator:
            if len(parts) < 2:
                return {"overall": "⚠️ Insufficient parts", "details": f"Tag name should have at least 2 parts when using a separator."}
        return {"overall": "✅ Acceptable", "details": "Tag name follows the naming convention guidelines."}
    else:
        # Check if the full platform name is used
        if any(platform.lower() in first_part.lower() for platform in VALID_PLATFORMS.values()):
            return {"overall": "⚠️ Full platform name used", "details": f"Consider using the platform prefix (e.g., {', '.join(VALID_PLATFORMS.keys())}) instead of the full name."}
        else:
            return {"overall": "❌ Invalid platform prefix", "details": f"'{first_part}' is not a recognized platform prefix or name."}

def gather_tag_naming_info(tags: List[Dict[str, Any]], trigger_names: Dict[str, str]) -> List[Dict[str, str]]:
    tag_naming_info = []
    
    for tag in tags:
        tag_name = tag.get('name', 'Unnamed Tag')
        tag_type = tag.get('type', 'Unknown Type')
        
        # Get trigger names
        trigger_ids = tag.get('firingTriggerId', [])
        triggers = [trigger_names.get(str(tid), f"Unknown Trigger (ID: {tid})") for tid in trigger_ids]
        trigger_names_str = ', '.join(triggers) if triggers else 'No Triggers'
        
        assessment_result = assess_naming_convention(tag_name)
        
        tag_naming_info.append({
            'Tag Name': tag_name,
            'Tag Type': tag_type,
            'Trigger Name': trigger_names_str,
            'Naming Convention': assessment_result['overall'],
            'Details': assessment_result['details']
        })
    
    return tag_naming_info