import pandas as pd
import numpy as np

def get_uniqueness_suggestions(df):
    """
    Analyze data uniqueness and suggest fixes.
    Returns a dictionary of uniqueness issues and suggested fixes.
    """
    suggestions = {}
    
    # Check for exact duplicate rows
    exact_duplicates = df.duplicated()
    duplicate_count = exact_duplicates.sum()
    
    if duplicate_count > 0:
        suggestions['exact_duplicates'] = {
            'description': f'Found {duplicate_count} exact duplicate rows',
            'sample': df[exact_duplicates].head().to_dict('records'),
            'strategies': [{
                'name': 'Remove exact duplicates',
                'description': 'Remove all exact duplicate rows, keeping the first occurrence',
                'code': "df.drop_duplicates(inplace=True)"
            }]
        }
    
    # Check for potential ID columns
    for column in df.columns:
        col_name = column.lower()
        if ('id' in col_name or 'key' in col_name or 'code' in col_name) and df[column].nunique() > len(df) * 0.9:
            duplicates = df[df[column].duplicated()]
            if len(duplicates) > 0:
                if column not in suggestions:
                    suggestions[column] = {
                        'description': f'Found {len(duplicates)} duplicate values in potential ID column',
                        'sample': duplicates[column].head().tolist(),
                        'strategies': [{
                            'name': 'Remove ID duplicates',
                            'description': f'Remove duplicate rows based on {column}, keeping the first occurrence',
                            'code': f"df.drop_duplicates(subset=['{column}'], inplace=True)"
                        }]
                    }
    
    # Check for near-duplicate rows based on subset of columns
    text_cols = df.select_dtypes(include=['object']).columns
    for col1 in text_cols:
        # Skip very unique columns (likely IDs) and columns with too many nulls
        if df[col1].nunique() > len(df) * 0.9 or df[col1].isna().sum() > len(df) * 0.5:
            continue
            
        for col2 in text_cols:
            if col1 >= col2:  # Skip same column and already checked pairs
                continue
                
            # Skip very unique columns and columns with too many nulls
            if df[col2].nunique() > len(df) * 0.9 or df[col2].isna().sum() > len(df) * 0.5:
                continue
            
            # Find rows where these columns have the same values
            duplicates = df[df.duplicated(subset=[col1, col2], keep=False)]
            if len(duplicates) > len(df) * 0.01:  # Only report if more than 1% of rows
                key = f"{col1}_{col2}_duplicates"
                suggestions[key] = {
                    'description': f'Found {len(duplicates)} rows with duplicate values in {col1} and {col2}',
                    'sample': duplicates[[col1, col2]].head().to_dict('records'),
                    'strategies': [{
                        'name': f'Remove {col1}-{col2} duplicates',
                        'description': f'Remove duplicate rows based on {col1} and {col2}, keeping the first occurrence',
                        'code': f"df.drop_duplicates(subset=['{col1}', '{col2}'], inplace=True)"
                    }]
                }
    
    # Check for columns with very low cardinality (might indicate data quality issues)
    for column in df.columns:
        unique_ratio = df[column].nunique() / len(df)
        if 0 < unique_ratio < 0.01 and df[column].nunique() > 1:  # Less than 1% unique values
            if column not in suggestions:
                suggestions[column] = {
                    'description': f'Column has very low cardinality ({df[column].nunique()} unique values in {len(df)} rows)',
                    'sample': df[column].value_counts().head().to_dict(),
                    'strategies': [{
                        'name': 'Convert to category',
                        'description': 'Convert to categorical type to save memory and improve performance',
                        'code': f"df['{column}'] = df['{column}'].astype('category')"
                    }]
                }
    
    return suggestions 