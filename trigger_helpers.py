# Here is trigger_helpers.py

from collections import defaultdict

# Dictionary of built-in GTM trigger IDs and their names
BUILT_IN_TRIGGERS = {
    "2147479553": "All Pages",  # Example of built-in trigger mapping
    # Add other built-in triggers here as necessary
}

# Function to extract trigger names from GTM data
def get_trigger_names(gtm_data):
    trigger_names = {}
    if 'trigger' in gtm_data['containerVersion']:
        for trigger in gtm_data['containerVersion']['trigger']:
            trigger_names[trigger['triggerId']] = trigger['name']
    return trigger_names

# Function to group tags by their type
def group_tags_by_type(tags):
    grouped_tags = defaultdict(list)
    for tag in tags:
        grouped_tags[tag['type']].append(tag)
    return grouped_tags