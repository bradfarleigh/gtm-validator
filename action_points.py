# Helper function to generate action points
def generate_action_points(facebook_ids, ga4_ids, google_ads_ids, ua_ids, tiktok_ids, paused_tags, google_ads_issues=None):
    action_points = []
    
    if google_ads_issues:
        action_points.extend(google_ads_issues)
    
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