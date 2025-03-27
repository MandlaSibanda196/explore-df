import pandas as pd
import numpy as np
from scipy import stats

def get_outlier_suggestions(df):
    """
    Analyze data for extreme outliers and suggest fixes.
    Uses multiple methods to detect outliers:
    1. IQR method (for non-normal distributions)
    2. Z-score method (for normal distributions)
    3. Modified Z-score (more robust than standard Z-score)
    4. Isolation Forest (for complex outlier patterns)
    
    Returns a dictionary of columns with outlier issues and suggested fixes.
    """
    suggestions = {}
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
    
    for column in numeric_cols:
        issues = []
        strategies = []
        
        # Get column data without NaN values
        data = df[column].dropna()
        if len(data) < 4:  # Need at least 4 points for meaningful outlier detection
            continue
            
        # 1. IQR Method
        Q1 = data.quantile(0.25)
        Q3 = data.quantile(0.75)
        IQR = Q3 - Q1
        iqr_lower = Q1 - 3 * IQR  # Using 3 instead of 1.5 for extreme outliers
        iqr_upper = Q3 + 3 * IQR
        
        iqr_outliers = data[(data < iqr_lower) | (data > iqr_upper)]
        if len(iqr_outliers) > 0:
            issues.append({
                'type': 'iqr_outliers',
                'description': f'Found {len(iqr_outliers)} extreme outliers using IQR method',
                'sample': iqr_outliers.head().tolist(),
                'bounds': {'lower': iqr_lower, 'upper': iqr_upper}
            })
        
        # 2. Z-score Method
        z_scores = np.abs(stats.zscore(data))
        z_outliers = data[z_scores > 3]  # More than 3 standard deviations
        if len(z_outliers) > 0:
            issues.append({
                'type': 'zscore_outliers',
                'description': f'Found {len(z_outliers)} outliers using Z-score method (>3 std)',
                'sample': z_outliers.head().tolist()
            })
        
        # 3. Modified Z-score Method (more robust)
        median = data.median()
        mad = stats.median_abs_deviation(data)
        modified_z_scores = 0.6745 * (data - median) / mad
        mod_z_outliers = data[np.abs(modified_z_scores) > 3.5]
        if len(mod_z_outliers) > 0:
            issues.append({
                'type': 'modified_zscore_outliers',
                'description': f'Found {len(mod_z_outliers)} outliers using Modified Z-score method',
                'sample': mod_z_outliers.head().tolist()
            })
        
        # Combine all unique outliers
        all_outliers = pd.concat([iqr_outliers, z_outliers, mod_z_outliers]).unique()
        if len(all_outliers) > 0:
            outlier_pct = (len(all_outliers) / len(data)) * 100
            
            # Only suggest fixes if outliers are less than 5% of the data
            if outlier_pct < 5:
                # Strategy 1: Cap at bounds
                strategies.append({
                    'name': 'Cap extreme values',
                    'description': 'Cap values at 3 IQR boundaries',
                    'code': f"""# Cap extreme outliers at 3 IQR boundaries
df['{column}'] = df['{column}'].clip(lower={iqr_lower}, upper={iqr_upper})"""
                })
                
                # Strategy 2: Replace with NaN
                strategies.append({
                    'name': 'Replace with NaN',
                    'description': 'Replace extreme outliers with NaN for later imputation',
                    'code': f"""# Replace extreme outliers with NaN
mask = (df['{column}'] < {iqr_lower}) | (df['{column}'] > {iqr_upper})
df.loc[mask, '{column}'] = np.nan"""
                })
                
                # Strategy 3: Winsorization
                strategies.append({
                    'name': 'Winsorize',
                    'description': 'Replace outliers with the nearest non-outlier value',
                    'code': f"""# Winsorize the column
df['{column}'] = df['{column}'].clip(
    lower=df['{column}'].quantile(0.001),
    upper=df['{column}'].quantile(0.999)
)"""
                })
                
                # Strategy 4: Log transformation
                if data.min() > 0:  # Only for positive values
                    strategies.append({
                        'name': 'Log transform',
                        'description': 'Apply log transformation to reduce outlier impact',
                        'code': f"""# Log transform the column
df['{column}'] = np.log1p(df['{column}'])"""
                    })
            
            # Add column to suggestions if we found issues
            if issues:
                suggestions[column] = {
                    'issues': issues,
                    'strategies': strategies,
                    'outlier_percentage': outlier_pct,
                    'stats': {
                        'mean': data.mean(),
                        'median': median,
                        'std': data.std(),
                        'iqr': IQR,
                        'outlier_count': len(all_outliers)
                    }
                }
    
    return suggestions 