import pandas as pd
import numpy as np

def get_timeliness_suggestions(df):
    """
    Analyze data timeliness and suggest fixes.
    Returns a dictionary of timeliness issues and suggested fixes.
    """
    suggestions = {}
    
    # Get datetime columns
    date_cols = df.select_dtypes(include=['datetime64']).columns
    if len(date_cols) == 0:
        return suggestions
    
    current_date = pd.Timestamp.now()
    
    for column in date_cols:
        issues = []
        strategies = []
        
        # Check for future dates where inappropriate
        if any(word in column.lower() for word in ['birth', 'start', 'created', 'registered']):
            future_dates = df[df[column] > current_date]
            if len(future_dates) > 0:
                issues.append({
                    'type': 'future_dates',
                    'description': f'Found {len(future_dates)} dates in the future',
                    'sample': future_dates[column].head().tolist()
                })
                strategies.append({
                    'name': 'Replace future dates',
                    'description': 'Replace future dates with current date',
                    'code': f"""# Replace future dates with current date
df.loc[df['{column}'] > pd.Timestamp.now(), '{column}'] = pd.Timestamp.now()"""
                })
        
        # Check for very old dates that might be errors
        very_old = df[df[column] < pd.Timestamp('1900-01-01')]
        if len(very_old) > 0:
            issues.append({
                'type': 'very_old_dates',
                'description': f'Found {len(very_old)} dates before 1900',
                'sample': very_old[column].head().tolist()
            })
            strategies.append({
                'name': 'Replace old dates',
                'description': 'Replace dates before 1900 with NaT',
                'code': f"""# Replace very old dates with NaT
df.loc[df['{column}'] < pd.Timestamp('1900-01-01'), '{column}'] = pd.NaT"""
            })
        
        # Check for large gaps in time series data
        df_sorted = df.sort_values(column)
        time_diffs = df_sorted[column].diff()
        median_diff = time_diffs.median()
        if pd.notna(median_diff):
            large_gaps = time_diffs[time_diffs > median_diff * 5]
            if not large_gaps.empty:
                issues.append({
                    'type': 'time_gaps',
                    'description': f'Found {len(large_gaps)} large time gaps (>5x median interval)',
                    'sample': large_gaps.head().tolist(),
                    'median_interval': median_diff
                })
                
                # Only suggest interpolation for numeric columns
                numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
                if len(numeric_cols) > 0:
                    strategies.append({
                        'name': 'Interpolate gaps',
                        'description': 'Interpolate values for large time gaps',
                        'code': f"""# Sort by date and interpolate
df = df.sort_values('{column}')
df[{numeric_cols.tolist()}] = df[{numeric_cols.tolist()}].interpolate(method='time')"""
                    })
        
        # Check for inconsistent time intervals in time series
        if len(df) > 1:
            unique_intervals = time_diffs.dropna().unique()
            if len(unique_intervals) > 1:
                common_interval = pd.Timedelta(time_diffs.mode().iloc[0])
                inconsistent = time_diffs[time_diffs != common_interval]
                if len(inconsistent) > len(df) * 0.1:  # More than 10% inconsistent
                    issues.append({
                        'type': 'inconsistent_intervals',
                        'description': f'Found {len(inconsistent)} inconsistent time intervals',
                        'sample': inconsistent.head().tolist(),
                        'common_interval': common_interval
                    })
                    strategies.append({
                        'name': 'Resample data',
                        'description': f'Resample data to consistent {common_interval} intervals',
                        'code': f"""# Resample data to consistent intervals
df = df.set_index('{column}').resample('{common_interval}').asfreq()"""
                    })
        
        if issues:
            suggestions[column] = {
                'issues': issues,
                'strategies': strategies
            }
    
    return suggestions 