# id_extraction.py

import re

def extract_facebook_id(html_content):
    pixel_match = re.search(r'https://www\.facebook\.com/tr\?id=(\d+)&ev=PageView&noscript=1', html_content)
    if pixel_match:
        return pixel_match.group(1)
    init_match = re.search(r"fbq\('init',\s*'(\d+)'\)", html_content)
    return init_match.group(1) if init_match else None

def extract_tiktok_id(html_content):
    # Extract TikTok Pixel ID
    pixel_match = re.search(r"ttq\.load\('([A-Z0-9]+)'\)", html_content)
    tiktok_id = pixel_match.group(1) if pixel_match else None

    # Extract email or phone parameters
    email_match = re.search(r"email['\"]?:\s*['\"]([^'\"]+)['\"]", html_content)
    phone_match = re.search(r"phone['\"]?:\s*['\"]([^'\"]+)['\"]", html_content)

    email = email_match.group(1) if email_match else 'No Email'
    phone = phone_match.group(1) if phone_match else 'No Phone'

    return tiktok_id, email, phone

def extract_ga4_id(tag):
    if tag['type'] in ['gaawe', 'googtag']:
        for param in tag['parameter']:
            if param['key'] in ['measurementIdOverride', 'tagId']:
                return param['value']
    return None

def extract_google_ads_id(tag):
    if tag['type'] == 'awct' or tag['type'] == 'sp':
        for param in tag['parameter']:
            if param['key'] == 'conversionId':
                return param['value']
    return None

def extract_ua_id(html_content):
    match = re.search(r'UA-\d{4,10}-\d{1,4}', html_content)
    return match.group(0) if match else None
