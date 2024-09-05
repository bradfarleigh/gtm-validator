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

def extract_tiktok_id(tag):
    """Extract TikTok Pixel ID from HTML content."""
    for param in tag.get('parameter', []):
        if param['key'] == 'html':
            html_content = param.get('value', '')
            # Ensure we are only using the regex on strings
            if isinstance(html_content, str):
                # Use regex to extract the TikTok Pixel ID from the ttq.load() function
                tiktok_id_match = re.search(r"ttq\.load\('([A-Z0-9]+)'\)", html_content)
                if tiktok_id_match:
                    return tiktok_id_match.group(1)
    return None