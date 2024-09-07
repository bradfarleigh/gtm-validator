from typing import List, Dict, Any
import re

# Define valid prefixes and their longer forms
VALID_PREFIXES = {
    'GA': 'GoogleAnalytics',
    'FB': 'Facebook',
    'AW': 'AdWords',
    'TT': 'TikTok',
    # Add more valid prefixes here
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

    # Check separator consistency
    pipe_count = tag_name.count('|')
    hyphen_count = tag_name.count('-')
    if pipe_count > 0 and hyphen_count > 0:
        return {"overall": "❌ Inconsistent separator", "details": "Mixed use of '|' and '-' separators."}
    
    separator = '|' if pipe_count > 0 else '-' if hyphen_count > 0 else None
    if not separator:
        return {"overall": "❌ No separator", "details": "No '|' or '-' separator found in the tag name."}

    parts = tag_name.split(separator)
    
    # Check number of parts
    if len(parts) < 3:
        return {"overall": "❌ Insufficient parts", "details": f"Tag name should have at least 3 parts separated by '{separator}'."}

    # Check prefix
    prefix = parts[0]
    if prefix not in VALID_PREFIXES and prefix not in VALID_PREFIXES.values():
        return {"overall": "❌ Invalid prefix", "details": f"'{prefix}' is not a valid prefix."}

    # Check action/event
    if len(parts[1]) < 2:
        return {"overall": "❌ Invalid action/event", "details": "Action/event part is too short."}

    # Check specificity
    if len(parts) >= 3 and len(parts[2]) < 2:
        return {"overall": "⚠️ Low specificity", "details": "Consider adding more specific details in the third part."}

    # Check for version control (if present)
    if len(parts) >= 4 and parts[-1].startswith('v'):
        if not parts[-1][1:].isdigit():
            return {"overall": "⚠️ Invalid version format", "details": "Version should be in the format 'v<number>'."}

    return {"overall": "✅ Acceptable", "details": "Tag name follows the naming convention guidelines."}

def check_naming_pattern(tag_name: str) -> str:
    """Check if the tag name follows the specific pattern defined in the rules."""
    pattern = r'^([A-Za-z]{2,3}|[A-Za-z]+)[\|-]([A-Za-z]{2,}|[A-Za-z]+)[\|-]([A-Za-z]{2,}|[A-Za-z]+)([\|-][A-Za-z]+)?([\|-]v\d+)?$'
    if re.match(pattern, tag_name):
        return "✅ Follows naming pattern"
    else:
        return "❌ Does not follow recommended naming pattern"

__all__ = ['gather_tag_naming_info', 'assess_naming_convention', 'check_naming_pattern']