# Function to extract variables from GTM data
def extract_variables(gtm_data):
    variables = {}
    if 'variable' in gtm_data['containerVersion']:
        for variable in gtm_data['containerVersion']['variable']:
            variable_name = variable.get('name', '')
            variable_value = None
            for param in variable.get('parameter', []):
                if param.get('key') == 'name':
                    variable_value = param.get('value', 'Unknown')
            if variable_name and variable_value:
                variables[variable_name] = variable_value
    return variables

# Function to replace placeholders in tag parameters with variable values
def replace_variable_placeholders(value, variables):
    if '{{' in value and '}}' in value:
        var_name = value.strip('{}')
        if var_name in variables:
            return f"{{{{{var_name}}}}} - {variables[var_name]}"
    return value