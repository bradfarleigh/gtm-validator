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
    'Clarity': 'Microsoft Clarity'
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

    # Check platform prefix in first or second slot
    for i in range(min(2, len(parts))):
        part = parts[i].strip()
        platform_prefix = next((prefix for prefix in VALID_PLATFORMS.keys() if part.upper().startswith(prefix)), None)
        if platform_prefix:
            if separator and len(parts) < 2:
                return {"overall": "⚠️ Insufficient parts", "details": f"Tag name should have at least 2 parts when using a separator."}
            return {"overall": "✅ Acceptable", "details": "Tag name follows the naming convention guidelines."}

    # If no valid prefix found, check for full platform names
    for prefix, full_name in VALID_PLATFORMS.items():
        if full_name.lower() in tag_name.lower():
            # Find the part containing the full name
            for i, part in enumerate(parts):
                if full_name.lower() in part.lower():
                    correct_part = part.replace(full_name, prefix).replace(full_name.lower(), prefix)
                    correct_parts = parts.copy()
                    correct_parts[i] = correct_part
                    correct_name = separator.join(correct_parts) if separator else ' '.join(correct_parts)
                    example = f"Instead of '{tag_name}' use '{correct_name}'"
                    return {"overall": "⚠️ Full platform name used", "details": f"Consider using the platform prefix. {example}"}

    return {"overall": "❌ Invalid platform prefix", "details": f"No recognized platform prefix or name found in the first two parts of the tag name."}

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