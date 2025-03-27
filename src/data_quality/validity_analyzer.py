import pandas as pd
import numpy as np
import re

def get_validity_suggestions(df):
    """
    Analyze data validity and suggest fixes.
    Returns a dictionary of validity issues and suggested fixes.
    """
    suggestions = {}
    
    # Common patterns for validation
    patterns = {
        'email': (r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', 
                 'Valid email address format'),
        'phone': (r'^\+?1?\d{9,15}$',
                 'Phone number with optional country code'),
        'url': (r'^https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&\/=]*)$',
               'Valid URL format'),
        'zipcode': (r'^\d{5}(?:[-\s]\d{4})?$',
                   'US ZIP code format (5 digits or 5+4)'),
        'date': (r'^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])$',
                'YYYY-MM-DD format')
    }
    
    # Check text columns for common patterns
    text_cols = df.select_dtypes(include=['object']).columns
    for column in text_cols:
        col_name = column.lower()
        sample = df[column].dropna()
        if len(sample) == 0:
            continue
        
        # Email validation
        if any(word in col_name for word in ['email', 'e-mail', 'mail']):
            invalid_mask = ~sample.str.match(patterns['email'][0], na=False)
            invalid_count = invalid_mask.sum()
            if invalid_count > 0:
                suggestions[column] = {
                    'type': 'email_format',
                    'description': f'Found {invalid_count} invalid email addresses',
                    'sample': sample[invalid_mask].head().tolist(),
                    'strategies': [{
                        'name': 'Clean email addresses',
                        'description': 'Remove whitespace and convert to lowercase',
                        'code': f"df['{column}'] = df['{column}'].str.strip().str.lower()"
                    }, {
                        'name': 'Mark invalid as NaN',
                        'description': 'Replace invalid email addresses with NaN',
                        'code': f"""# Mark invalid emails as NaN
df['{column}'] = df['{column}'].apply(lambda x: x if pd.isna(x) or re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', str(x)) else np.nan)"""
                    }]
                }
        
        # Phone number validation
        elif any(word in col_name for word in ['phone', 'mobile', 'cell', 'tel']):
            # First clean the numbers
            cleaned = sample.str.replace(r'[\s\-\(\)\.]', '', regex=True)
            invalid_mask = ~cleaned.str.match(patterns['phone'][0], na=False)
            invalid_count = invalid_mask.sum()
            if invalid_count > 0:
                suggestions[column] = {
                    'type': 'phone_format',
                    'description': f'Found {invalid_count} invalid phone numbers',
                    'sample': sample[invalid_mask].head().tolist(),
                    'strategies': [{
                        'name': 'Standardize phone numbers',
                        'description': 'Remove non-numeric characters and standardize format',
                        'code': f"""# Standardize phone numbers
df['{column}'] = df['{column}'].str.replace(r'[^\d+]', '', regex=True)"""
                    }]
                }
        
        # URL validation
        elif any(word in col_name for word in ['url', 'website', 'link', 'site']):
            invalid_mask = ~sample.str.match(patterns['url'][0], na=False)
            invalid_count = invalid_mask.sum()
            if invalid_count > 0:
                suggestions[column] = {
                    'type': 'url_format',
                    'description': f'Found {invalid_count} invalid URLs',
                    'sample': sample[invalid_mask].head().tolist(),
                    'strategies': [{
                        'name': 'Add https://',
                        'description': 'Add https:// to URLs missing protocol',
                        'code': f"""# Add https:// to URLs missing protocol
df['{column}'] = df['{column}'].apply(lambda x: 'https://' + x if pd.notna(x) and not str(x).startswith(('http://', 'https://')) else x)"""
                    }]
                }
        
        # ZIP code validation (US)
        elif any(word in col_name for word in ['zip', 'postal']):
            invalid_mask = ~sample.str.match(patterns['zipcode'][0], na=False)
            invalid_count = invalid_mask.sum()
            if invalid_count > 0:
                suggestions[column] = {
                    'type': 'zipcode_format',
                    'description': f'Found {invalid_count} invalid ZIP codes',
                    'sample': sample[invalid_mask].head().tolist(),
                    'strategies': [{
                        'name': 'Standardize ZIP codes',
                        'description': 'Keep only digits for 5-digit format',
                        'code': f"""# Keep only first 5 digits
df['{column}'] = df['{column}'].str.extract(r'(\d{{5}})').fillna(df['{column}'])"""
                    }]
                }
    
    # Check date columns for validity
    date_cols = df.select_dtypes(include=['datetime64']).columns
    for column in date_cols:
        invalid_dates = df[~df[column].notna() & df[column].astype(str).str.match(patterns['date'][0], na=False)]
        if len(invalid_dates) > 0:
            suggestions[column] = {
                'type': 'date_format',
                'description': f'Found {len(invalid_dates)} invalid dates',
                'sample': invalid_dates[column].head().tolist(),
                'strategies': [{
                    'name': 'Convert to datetime',
                    'description': 'Convert to datetime format with error handling',
                    'code': f"""# Convert to datetime with coercion
df['{column}'] = pd.to_datetime(df['{column}'], errors='coerce')"""
                }]
            }
    
    # Check numeric columns for validity based on column name hints
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
    for column in numeric_cols:
        col_name = column.lower()
        
        # Percentage validation
        if any(word in col_name for word in ['percentage', 'ratio', 'pct']):
            invalid_mask = (df[column] < 0) | (df[column] > 100)
            invalid_count = invalid_mask.sum()
            if invalid_count > 0:
                suggestions[column] = {
                    'type': 'percentage_range',
                    'description': f'Found {invalid_count} values outside valid percentage range (0-100)',
                    'sample': df[invalid_mask][column].head().tolist(),
                    'strategies': [{
                        'name': 'Clip to valid range',
                        'description': 'Clip values to 0-100 range',
                        'code': f"df['{column}'] = df['{column}'].clip(0, 100)"
                    }]
                }
        
        # Probability validation
        elif any(word in col_name for word in ['probability', 'prob', 'likelihood']):
            invalid_mask = (df[column] < 0) | (df[column] > 1)
            invalid_count = invalid_mask.sum()
            if invalid_count > 0:
                suggestions[column] = {
                    'type': 'probability_range',
                    'description': f'Found {invalid_count} values outside valid probability range (0-1)',
                    'sample': df[invalid_mask][column].head().tolist(),
                    'strategies': [{
                        'name': 'Clip to valid range',
                        'description': 'Clip values to 0-1 range',
                        'code': f"df['{column}'] = df['{column}'].clip(0, 1)"
                    }]
                }
    
    return suggestions 