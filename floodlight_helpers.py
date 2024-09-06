from trigger_helpers import BUILT_IN_TRIGGERS


# Function to group Floodlight (FLC) tags
def group_floodlight_tags(tags, trigger_names):
    floodlight_tags = []
    for tag in tags:
        if tag['type'] == 'flc':  # Floodlight Tag (FLC)
            # Extract necessary parameters from the Floodlight tag
            grouptag = get_floodlight_param(tag, 'groupTag')
            activitytag = get_floodlight_param(tag, 'activityTag')
            advertiserid = get_floodlight_param(tag, 'advertiserId')
            
            # Get the trigger names associated with this tag
            trigger_ids = tag.get('firingTriggerId', [])
            triggers = [BUILT_IN_TRIGGERS.get(str(tid), trigger_names.get(str(tid), f"Unknown Trigger (ID: {tid})")) for tid in trigger_ids]
            
            # Append the extracted values to the list
            floodlight_tags.append({
                'Tag Name': tag.get('name', 'Unnamed Tag'),
                'Group Tag': grouptag,
                'Activity Tag': activitytag,
                'Advertiser ID': advertiserid,
                'Trigger Name': ', '.join(triggers) if triggers else 'No Triggers'
            })
    return floodlight_tags

# Helper function to extract Floodlight parameters
def get_floodlight_param(tag, param_key):
    for param in tag.get('parameter', []):
        if param['key'] == param_key:
            return param.get('value', 'No Value')
    return 'No Value'