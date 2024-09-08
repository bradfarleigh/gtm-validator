from typing import List, Dict, Any
import re

# Define valid prefixes and their longer forms
VALID_PREFIXES = {
    'GA': 'GoogleAnalytics',
    'FB': 'Facebook',
    'AW': 'AdWords',
    'TT': 'TikTok',
    'GA4' : "Google Analytics 4",
    "Facebook" : "Facebook"
    # Add more valid prefixes here
}

# Define valid platform prefixes
VALID_PLATFORMS = {
    'FB': 'Facebook',
    'GA': 'Google Analytics',
    'AW': 'Google Ads',
    'TT': 'TikTok',
    'DCM': 'DoubleClick',
    'TTD': 'The Trade Desk',
    # Add more platform prefixes as needed
}


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

def assess_naming_convention(tag_name: str) -> Dict[str, str]:
    if not tag_name or tag_name == 'Unnamed Tag':
        return {"overall": "❌ Missing name", "details": "Tag name is missing or unnamed."}

    # Check for valid separators
    if '|' in tag_name:
        separator = '|'
    elif '-' in tag_name:
        separator = '-'
    else:
        return {"overall": "❌ Invalid separator", "details": "Tag name must use either '|' or '-' as separators."}

    parts = tag_name.split(separator)

    # Check number of parts
    if len(parts) < 2:
        return {"overall": "❌ Insufficient parts", "details": f"Tag name should have at least 2 parts separated by '{separator}'."}

    # Check platform prefix
    platform_prefix = parts[0].strip().upper()
    if platform_prefix not in VALID_PLATFORMS:
        return {"overall": "❌ Invalid platform prefix", "details": f"'{platform_prefix}' is not a recognized platform prefix."}

    # Check if the full platform name is used instead of the prefix
    if any(platform.lower() in parts[0].lower() for platform in VALID_PLATFORMS.values()):
        return {"overall": "⚠️ Full platform name used", "details": f"Consider using the platform prefix (e.g., {', '.join(VALID_PLATFORMS.keys())}) instead of the full name."}

    return {"overall": "✅ Acceptable", "details": "Tag name follows the naming convention guidelines."}

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

def check_naming_pattern(tag_name: str) -> str:
    """Check if the tag name follows the specific pattern defined in the rules."""
    pattern = r'^([A-Za-z]{2,3}|[A-Za-z]+)[\|-]([A-Za-z]{2,}|[A-Za-z]+)[\|-]([A-Za-z]{2,}|[A-Za-z]+)([\|-][A-Za-z]+)?([\|-]v\d+)?$'
    if re.match(pattern, tag_name):
        return "✅ Follows naming pattern"
    else:
        return "❌ Does not follow recommended naming pattern"

__all__ = ['gather_tag_naming_info', 'assess_naming_convention', 'check_naming_pattern']