# Helper function to generate action points
def generate_action_points(facebook_ids, ga4_ids, google_ads_ids, ua_ids, tiktok_ids, paused_tags, google_ads_issues=None):
    action_points = []
    
    if google_ads_issues:
        action_points.extend(google_ads_issues)
    
    if len(facebook_ids) > 1:
        action_points.append("**Facebook** - Multiple Facebook tracking IDs being used across tags.");
    if len(ga4_ids) > 1:
        action_points.append("**GA4** - Multiple GA4 tracking IDs being used across tags.");
    if len(google_ads_ids) > 1:
        action_points.append("**Google Ads** - Multiple Google Ads tracking IDs being used across tags.");
    if len(tiktok_ids) > 1:
        action_points.append("**TikTok** - Multiple TikTok tracking IDs being used across tags.");
    if ua_ids:
        action_points.append("**Universal Analytics** - Cleanup required of Universal (UA) tags.")
    if paused_tags:
        action_points.append(f"**Paused Tags** - Review and decide on the status of paused tags: `{', '.join(paused_tags)}`")

    return action_points