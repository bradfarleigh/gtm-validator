# This is id_extraction.py

import re

def extract_facebook_id(tag_or_content):
    """
    Extract Facebook Pixel ID from either HTML content or a tag dictionary.
    
    Args:
    tag_or_content (Union[str, Dict]): Either HTML content as a string or a tag dictionary.
    
    Returns:
    str: Extracted Facebook Pixel ID or None if not found.
    """
    if isinstance(tag_or_content, dict):
        # Handle tag dictionary
        for param in tag_or_content.get('parameter', []):
            if param.get('key') == 'pixelId':
                return param.get('value')
        return None
    elif isinstance(tag_or_content, str):
        # Handle HTML content
        fb_id_match = re.search(r'fbq\(\'init\',\s*\'(\d{13,17})\'\)', tag_or_content)
        return fb_id_match.group(1) if fb_id_match else None
    else:
        return None
    
def extract_ga4_id(tag):
    for param in tag.get('parameter', []):
        if param['key'] == 'measurementId':
            return param.get('value', 'No Measurement ID')
    return 'No Measurement ID'

def extract_google_ads_id(tag):
    for param in tag.get('parameter', []):
        if param['key'] == 'conversionId':
            return param.get('value', 'No Conversion ID')
    return 'No Conversion ID'

def extract_ua_id(html_content):
    ua_id_match = re.search(r'UA-\d+-\d+', html_content)
    return ua_id_match.group(0) if ua_id_match else None

def extract_tiktok_id(tag):
    for param in tag.get('parameter', []):
        if param['key'] == 'pixel_code':
            return param.get('value', 'No Pixel ID')
    return 'No Pixel ID'