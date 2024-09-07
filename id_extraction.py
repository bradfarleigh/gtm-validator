# This is id_extraction.py

import re

def extract_facebook_id(tag, gtm_data):
    # Check if it's a custom template tag
    if tag['type'].startswith('cvt_'):
        template_id = tag['type'].split('_')[-1]
        # Find the corresponding custom template
        for template in gtm_data.get('containerVersion', {}).get('customTemplate', []):
            if template.get('templateId') == template_id and 'Facebook Pixel' in template.get('name', ''):
                # It's a Facebook Pixel custom template
                for param in tag.get('parameter', []):
                    if param.get('key') == 'pixelId':
                        return param.get('value')
    
    # Fallback to checking HTML content if it's an HTML tag
    elif tag['type'] == 'html':
        for param in tag.get('parameter', []):
            if param.get('key') == 'html':
                html_content = param.get('value', '')
                fb_id_match = re.search(r'fbq\s*\(\s*[\'"]init[\'"]\s*,\s*[\'"](\d{13,17})[\'"]', html_content)
                if fb_id_match:
                    return fb_id_match.group(1)
    
    return None

def extract_ga4_id(tag):
    for param in tag.get('parameter', []):
        if param['key'] in ['measurementId', 'measurementIdOverride', 'tagId']:
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

def resolve_variable(variable_name, variables):
    for var in variables:
        if var.get('name') == variable_name:
            if var.get('type') == 'smm':
                return var.get('defaultValue')
    return None