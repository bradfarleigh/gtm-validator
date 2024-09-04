from collections import defaultdict
from id_extraction import extract_facebook_id, extract_ga4_id, extract_google_ads_id, extract_ua_id, extract_tiktok_id

def get_trigger_names(gtm_data):
    trigger_names = {}
    if 'trigger' in gtm_data['containerVersion']:
        for trigger in gtm_data['containerVersion']['trigger']:
            trigger_names[trigger['triggerId']] = trigger['name']
    return trigger_names

def group_tags_by_type(tags):
    grouped_tags = defaultdict(list)
    for tag in tags:
        grouped_tags[tag['type']].append(tag)
    return grouped_tags

def check_id_consistency(tags):
    facebook_ids = set()
    ga4_ids = set()
    google_ads_ids = set()
    ua_ids = set()
    tiktok_ids = set()
    paused_tags = []
    inconsistencies = []
    
    for tag in tags:
        if tag.get('paused', False):
            paused_tags.append(tag['name'])
        
        if tag['type'] == 'html':
            for param in tag['parameter']:
                if param['key'] == 'html':
                    html_content = param.get('value', '')
                    fb_id = extract_facebook_id(html_content)
                    if fb_id:
                        facebook_ids.add(fb_id)
                    ua_id = extract_ua_id(html_content)
                    if ua_id:
                        ua_ids.add(ua_id)
                    tiktok_id = extract_tiktok_id(html_content)
                    if tiktok_id:
                        tiktok_ids.add(tiktok_id)
        elif tag['type'] in ['gaawe', 'googtag']:
            ga4_id = extract_ga4_id(tag)
            if ga4_id:
                ga4_ids.add(ga4_id)
        elif tag['type'] in ['awct', 'sp']:
            ads_id = extract_google_ads_id(tag)
            if ads_id:
                google_ads_ids.add(ads_id)

    if len(facebook_ids) > 1:
        inconsistencies.append(f"Multiple Facebook IDs found: {', '.join(facebook_ids)}")
    if len(ga4_ids) > 1:
        inconsistencies.append(f"Multiple GA4 Measurement IDs found: {', '.join(ga4_ids)}")
    if len(google_ads_ids) > 1:
        inconsistencies.append(f"Multiple Google Ads IDs found: {', '.join(google_ads_ids)}")
    if len(tiktok_ids) > 1:
        inconsistencies.append(f"Multiple TikTok IDs found: {', '.join(tiktok_ids)}")
    if len(ua_ids) > 1:
        inconsistencies.append(f"Multiple Universal Analytics IDs found: {', '.join(ua_ids)}")

    return facebook_ids, ga4_ids, google_ads_ids, ua_ids, tiktok_ids, paused_tags, inconsistencies

def generate_action_points(facebook_ids, ga4_ids, google_ads_ids, ua_ids, tiktok_ids, paused_tags):
    action_points = []
    if len(facebook_ids) > 1:
        action_points.append("Consolidate Facebook tracking IDs to use a single ID across all tags")
    if len(ga4_ids) > 1:
        action_points.append("Consolidate GA4 measurement IDs to use a single ID across all tags")
    if len(google_ads_ids) > 1:
        action_points.append("Consolidate Google Ads conversion IDs to use a single ID across all tags")
    if len(tiktok_ids) > 1:
        action_points.append("Consolidate TikTok tracking IDs to use a single ID across all tags")
    if ua_ids:
        action_points.append("Review and delete UA tags as they are no longer collecting data")
    if paused_tags:
        action_points.append(f"Review and decide on the status of paused tags: {', '.join(paused_tags)}")
    if not facebook_ids:
        action_points.append("Consider adding Facebook tracking if it's relevant for your analytics needs")
    if not ga4_ids:
        action_points.append("Implement Google Analytics 4 (GA4) for future-proof analytics")
    if not tiktok_ids:
        action_points.append("Consider adding TikTok tracking if it's relevant for your marketing strategy")
    return action_points