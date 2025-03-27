import pandas as pd
import numpy as np

def get_consistency_suggestions(df):
    """
    Analyze data consistency and suggest fixes.
    Returns a dictionary of columns with consistency issues and suggested fixes.
    """
    suggestions = {}
    
    def check_mixed_types(series):
        if series.dtype == 'object':
            numeric_mask = pd.to_numeric(series, errors='coerce').notna()
            if numeric_mask.any() and (~numeric_mask).any():
                return True
        return False
    
    # Check for mixed data types
    for column in df.columns:
        if check_mixed_types(df[column]):
            # Sample the different types in the column
            sample_values = df[column].dropna().sample(min(5, len(df[column].dropna()))).tolist()
            numeric_values = [x for x in sample_values if pd.to_numeric(str(x), errors='coerce') == pd.to_numeric(str(x), errors='coerce')]
            non_numeric = [x for x in sample_values if x not in numeric_values]
            
            suggestions[column] = {
                'issue_type': 'mixed_types',
                'description': 'Column contains mixed data types',
                'sample_values': sample_values,
                'numeric_sample': numeric_values,
                'non_numeric_sample': non_numeric,
                'strategies': []
            }
            
            # Add strategies based on the data
            if numeric_values:
                suggestions[column]['strategies'].append({
                    'name': 'Convert to numeric',
                    'description': 'Convert all values to numeric, replacing non-numeric values with NaN',
                    'code': f"df['{column}'] = pd.to_numeric(df['{column}'], errors='coerce')"
                })
            
            suggestions[column]['strategies'].append({
                'name': 'Convert to string',
                'description': 'Convert all values to strings for consistent text processing',
                'code': f"df['{column}'] = df['{column}'].astype(str)"
            })
    
    # Check for inconsistent text formatting
    text_columns = df.select_dtypes(include=['object']).columns
    for column in text_columns:
        sample = df[column].dropna()
        if len(sample) == 0:
            continue
            
        # Check for mixed case formatting
        lower_case = sample.str.islower().sum()
        upper_case = sample.str.isupper().sum()
        title_case = sample.str.istitle().sum()
        
        if min(lower_case, upper_case, title_case) > 0:
            if column not in suggestions:
                suggestions[column] = {
                    'issue_type': 'inconsistent_formatting',
                    'description': 'Inconsistent text formatting',
                    'sample_values': sample.sample(min(5, len(sample))).tolist(),
                    'strategies': []
                }
            
            # Add case formatting strategies
            if lower_case >= upper_case and lower_case >= title_case:
                suggestions[column]['strategies'].append({
                    'name': 'Convert to lowercase',
                    'description': 'Convert all text to lowercase for consistency',
                    'code': f"df['{column}'] = df['{column}'].str.lower()"
                })
            elif upper_case >= lower_case and upper_case >= title_case:
                suggestions[column]['strategies'].append({
                    'name': 'Convert to uppercase',
                    'description': 'Convert all text to uppercase for consistency',
                    'code': f"df['{column}'] = df['{column}'].str.upper()"
                })
            else:
                suggestions[column]['strategies'].append({
                    'name': 'Convert to title case',
                    'description': 'Convert all text to title case for consistency',
                    'code': f"df['{column}'] = df['{column}'].str.title()"
                })
        
        # Check for inconsistent spacing
        if sample.str.contains(r'\s{2,}|\s+$|^\s+').any():
            if column not in suggestions:
                suggestions[column] = {
                    'issue_type': 'inconsistent_spacing',
                    'description': 'Inconsistent spacing in text',
                    'sample_values': sample[sample.str.contains(r'\s{2,}|\s+$|^\s+')].sample(min(5, len(sample))).tolist(),
                    'strategies': []
                }
            
            suggestions[column]['strategies'].append({
                'name': 'Normalize spacing',
                'description': 'Remove extra spaces and trim whitespace',
                'code': f"df['{column}'] = df['{column}'].str.replace(r'\s+', ' ').str.strip()"
            })
    
    return suggestions 