import re

def extract_facebook_id(html_content):
    """Extracts Facebook Pixel ID from HTML content."""
    pixel_match = re.search(r'https://www\.facebook\.com/tr\?id=(\d+)&ev=PageView&noscript=1', html_content)
    if pixel_match:
        return pixel_match.group(1)
    
    init_match = re.search(r"fbq\('init',\s*'(\d+)'\)", html_content)
    return init_match.group(1) if init_match else None

def extract_ga4_id(tag):
    """Extracts GA4 Measurement ID from a tag."""
    for param in tag.get('parameter', []):
        if param['key'] in ['measurementIdOverride', 'tagId']:
            return param['value']
    return None

def extract_google_ads_id(tag):
    """Extracts Google Ads conversion ID from a tag."""
    for param in tag.get('parameter', []):
        if param['key'] == 'conversionId':
            return param['value']
    return None

def extract_ua_id(html_content):
    """Extracts Universal Analytics ID from HTML content."""
    match = re.search(r'UA-\d{4,10}-\d{1,4}', html_content)
    return match.group(0) if match else None

def extract_tiktok_id(html_content):
    """Extracts TikTok Pixel ID, email, and phone from the HTML content"""
    # Extract TikTok pixel ID
    tiktok_id_match = re.search(r"ttq\.load\('([A-Z0-9]+)'\)", html_content)
    tiktok_id = tiktok_id_match.group(1) if tiktok_id_match else None

    # Extract email (if available)
    email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", html_content)
    email = email_match.group(0) if email_match else None

    # Extract phone (if available)
    phone_match = re.search(r"\+?[0-9.\-() ]{7,}", html_content)
    phone = phone_match.group(0) if phone_match else None

    # Return a tuple (tiktok_id, email, phone) even if some of them are None
    return tiktok_id, email, phone