# Here is id_extraction.py

import re

# Extract Facebook Pixel ID from HTML content
def extract_facebook_id(html_content):
    # Regex to find Facebook Pixel ID in the HTML content
    fb_id_match = re.search(r'fbq\(\'init\',\s*\'(\d{13,17})\'\)', html_content)
    return fb_id_match.group(1) if fb_id_match else None

# Extract Universal Analytics (UA) ID from HTML content
def extract_ua_id(html_content):
    # Regex to find UA (Universal Analytics) ID in the HTML content
    ua_id_match = re.search(r'UA-\d{4,10}-\d{1,4}', html_content)
    return ua_id_match.group(0) if ua_id_match else None

def extract_tiktok_id(tag):
    # Check if the tag type is 'html' and it contains the 'parameter' key
    if tag.get('type') == 'html':
        for param in tag.get('parameter', []):
            if param.get('key') == 'html':  # Look for HTML content
                html_content = param.get('value', '')
                # Use regex to extract the TikTok Pixel ID from the HTML content
                tiktok_id_match = re.search(r'ttq\.load\([\'"]([A-Z0-9]+)[\'"]\)', html_content)
                if tiktok_id_match:
                    return tiktok_id_match.group(1)  # Return the TikTok ID if found
    return None  # Return None if the tag doesn't have TikTok ID or isn't the right type

# Extract Google Ads ID
def extract_google_ads_id(tag):
    for param in tag.get('parameter', []):
        if param['key'] == 'conversionId':
            return param.get('value', 'No ID')
    return 'No ID'

# Extract GA4 Measurement ID
def extract_ga4_id(tag):
    for param in tag.get('parameter', []):
        if param['key'] in ['measurementIdOverride', 'tagId']:
            return param.get('value', 'No ID')
    return 'No ID'