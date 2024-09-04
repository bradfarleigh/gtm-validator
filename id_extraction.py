import re

def extract_facebook_id(html_content):
    # Existing Facebook pixel ID extraction
    pixel_match = re.search(r'https://www\.facebook\.com/tr\?id=(\d+)&ev=PageView&noscript=1', html_content)
    if pixel_match:
        return pixel_match.group(1)
    
    # New Facebook ID extraction from fbq('init', 'XXX')
    init_match = re.search(r"fbq\('init',\s*'(\d+)'\)", html_content)
    return init_match.group(1) if init_match else None

def extract_tiktok_id(html_content):
    match = re.search(r"ttq\.load\('([A-Z0-9]+)'\)", html_content)
    return match.group(1) if match else None

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