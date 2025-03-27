import pandas as pd
import numpy as np

def get_accuracy_suggestions(df):
    """
    Analyze data accuracy and suggest fixes.
    Returns a dictionary of columns with accuracy issues and suggested fixes.
    """
    suggestions = {}
    
    # Check numeric columns for invalid values
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
    for column in numeric_cols:
        issues = []
        strategies = []
        
        # Check for negative values in columns that should be positive
        if any(word in column.lower() for word in ['age', 'count', 'quantity', 'amount', 'price', 'cost']):
            neg_count = (df[column] < 0).sum()
            if neg_count > 0:
                issues.append({
                    'type': 'negative_values',
                    'description': f'Found {neg_count} negative values in column that should be positive',
                    'sample': df[df[column] < 0][column].head().tolist()
                })
                strategies.append({
                    'name': 'Replace negatives with absolute values',
                    'description': 'Convert negative values to positive using absolute value',
                    'code': f"df['{column}'] = df['{column}'].abs()"
                })
                strategies.append({
                    'name': 'Replace negatives with NaN',
                    'description': 'Replace negative values with NaN for later handling',
                    'code': f"df.loc[df['{column}'] < 0, '{column}'] = np.nan"
                })
        
        # Check for unreasonable values based on column name
        if 'age' in column.lower() and df[column].max() > 150:
            issues.append({
                'type': 'unreasonable_values',
                'description': f'Found ages greater than 150 years',
                'sample': df[df[column] > 150][column].head().tolist()
            })
            strategies.append({
                'name': 'Cap age values',
                'description': 'Cap age values at 150 years',
                'code': f"df['{column}'] = df['{column}'].clip(upper=150)"
            })
        elif 'percentage' in column.lower() or 'ratio' in column.lower():
            if df[column].max() > 100:
                issues.append({
                    'type': 'unreasonable_values',
                    'description': f'Found percentage values greater than 100',
                    'sample': df[df[column] > 100][column].head().tolist()
                })
                strategies.append({
                    'name': 'Cap percentage values',
                    'description': 'Cap percentage values at 100',
                    'code': f"df['{column}'] = df['{column}'].clip(upper=100)"
                })
        
        if issues:
            suggestions[column] = {
                'issues': issues,
                'strategies': strategies
            }
    
    # Check date columns for future dates where inappropriate
    date_cols = df.select_dtypes(include=['datetime64']).columns
    current_date = pd.Timestamp.now()
    
    for column in date_cols:
        if any(word in column.lower() for word in ['birth', 'start', 'created', 'registered']):
            future_dates = df[df[column] > current_date]
            if len(future_dates) > 0:
                if column not in suggestions:
                    suggestions[column] = {'issues': [], 'strategies': []}
                
                suggestions[column]['issues'].append({
                    'type': 'future_dates',
                    'description': f'Found {len(future_dates)} dates in the future',
                    'sample': future_dates[column].head().tolist()
                })
                suggestions[column]['strategies'].append({
                    'name': 'Replace future dates',
                    'description': 'Replace future dates with current date',
                    'code': f"""# Replace future dates with current date
df.loc[df['{column}'] > pd.Timestamp.now(), '{column}'] = pd.Timestamp.now()"""
                })
    
    return suggestions 