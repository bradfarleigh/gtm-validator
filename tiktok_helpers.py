import re
from id_extraction import extract_tiktok_id
from trigger_helpers import BUILT_IN_TRIGGERS

# Function to group TikTok tags
def group_tiktok_tags(tags, trigger_names):
    tiktok_tags = []
    
    for tag in tags:
        tag_name = tag.get('name', 'Unnamed Tag')

        # Handle base TikTok Pixel code (HTML tag type with ttq.load())
        if tag['type'] == 'html':
            tiktok_id = extract_tiktok_id(tag)
            if tiktok_id:  # Ensure TikTok ID is found
                # Get the trigger names associated with this tag
                trigger_ids = tag.get('firingTriggerId', [])
                triggers = [trigger_names.get(str(tid), "Unknown Trigger") for tid in trigger_ids]

                tiktok_tags.append({
                    'Tag Name': tag_name,
                    'TikTok Pixel ID': tiktok_id or '✗ Not Found',
                    'Event': 'Base Pixel',
                    'Trigger Name': ', '.join(triggers) if triggers else 'No Triggers'
                })

        # Handle TikTok event tags (type = 'cvt_45667423_47')
        elif tag['type'] == 'cvt_45667423_47':
            tiktok_id = extract_tiktok_id(tag)
            event_name = None

            # Extract event name from tag parameters
            for param in tag.get('parameter', []):
                if param['key'] == 'event':
                    event_name = param.get('value', 'No Event Name')

            # Get the trigger names associated with this tag
            trigger_ids = tag.get('firingTriggerId', [])
            triggers = [trigger_names.get(str(tid), "Unknown Trigger") for tid in trigger_ids]

            tiktok_tags.append({
                'Tag Name': tag_name,
                'TikTok Pixel ID': tiktok_id or '',
                'Event': event_name or 'No Event Name',
                'Trigger Name': ', '.join(triggers) if triggers else 'No Triggers',
            })

    return tiktok_tags