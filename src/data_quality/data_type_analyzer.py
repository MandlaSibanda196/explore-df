import pandas as pd
import numpy as np
from datetime import datetime
import re
from typing import Dict, List, Tuple

class DataTypeAnalyzer:
    def __init__(self):
        # Common patterns for different data types
        self.datetime_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}-\d{2}-\d{4}',  # DD-MM-YYYY
            r'\d{2}/\d{2}/\d{4}',  # DD/MM/YYYY
            r'\d{4}/\d{2}/\d{2}',  # YYYY/MM/DD
            r'\d{2}\.\d{2}\.\d{4}',  # DD.MM.YYYY
            r'\d{4}\.\d{2}\.\d{2}',  # YYYY.MM.DD
            r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',  # YYYY-MM-DD HH:MM:SS
            r'\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2}',  # DD-MM-YYYY HH:MM:SS
        ]
        
        self.boolean_values = {
            'true', 'false', 't', 'f', 'yes', 'no', 'y', 'n', '1', '0', 'True', 'False'
        }
        
        # Add currency symbols and patterns
        self.currency_symbols = {'$', '€', '£', '¥', '₹'}
        self.currency_pattern = re.compile(r'^[^\d]*(\d+(?:,\d{3})*(?:\.\d{2})?)[^\d]*$')
        
        # Common column name patterns
        self.column_patterns = {
            'datetime': [
                r'.*date.*', r'.*time.*', r'.*timestamp.*', r'.*created.*', r'.*updated.*',
                r'.*modified.*', r'.*birth.*', r'.*death.*', r'.*start.*', r'.*end.*'
            ],
            'boolean': [
                r'.*is_.*', r'.*has_.*', r'.*was_.*', r'.*active.*', r'.*enabled.*',
                r'.*status.*', r'.*flag.*', r'.*bool.*'
            ],
            'numeric': [
                r'.*amount.*', r'.*price.*', r'.*cost.*', r'.*qty.*', r'.*quantity.*',
                r'.*number.*', r'.*num.*', r'.*count.*', r'.*age.*', r'.*id$', r'.*_id$',
                r'.*score.*', r'.*rating.*', r'.*percentage.*', r'.*percent.*'
            ],
            'categorical': [
                r'.*category.*', r'.*type.*', r'.*status.*', r'.*level.*', r'.*grade.*',
                r'.*class.*', r'.*group.*', r'.*code.*', r'.*country.*', r'.*nation.*',
                r'.*state.*', r'.*city.*', r'.*region.*', r'.*province.*', r'.*territory.*',
                r'.*department.*', r'.*division.*'
            ]
        }

    def _check_datetime_patterns(self, sample_values: List[str]) -> bool:
        """Check if the sample values match common datetime patterns."""
        for value in sample_values:
            if pd.isna(value):
                continue
            value = str(value).strip()
            if any(re.match(pattern, value) for pattern in self.datetime_patterns):
                try:
                    pd.to_datetime(value)
                    return True
                except:
                    continue
        return False

    def _is_boolean_series(self, sample_values: List) -> bool:
        """Check if the series contains only boolean-like values."""
        unique_values = set(str(x).lower().strip() for x in sample_values if pd.notna(x))
        return unique_values.issubset(self.boolean_values)

    def _clean_numeric_string(self, value: str) -> str:
        """Clean a string that might represent a number (including currency)."""
        value = str(value).strip()
        
        # Remove currency symbols
        for symbol in self.currency_symbols:
            value = value.replace(symbol, '')
            
        # Remove thousands separators (commas)
        value = value.replace(',', '')
        
        # Remove any remaining whitespace
        value = value.strip()
        
        return value

    def _is_numeric_series(self, sample_values: List) -> bool:
        """Check if the series contains only numeric values."""
        try:
            # Check if values match currency pattern
            all_values_currency = all(
                self.currency_pattern.match(str(x))
                for x in sample_values
                if pd.notna(x)
            )
            
            if all_values_currency:
                return True
            
            # Clean and check if values are numeric
            numeric_values = [
                float(self._clean_numeric_string(x))
                for x in sample_values
                if pd.notna(x)
            ]
            
            # Additional check to prevent misclassification of sequential IDs as numeric data
            if all(isinstance(x, str) for x in sample_values if pd.notna(x)):
                # If all values are strings and don't match currency pattern, be more strict
                if not all_values_currency:
                    return False
            
            return len(numeric_values) > 0
        except ValueError:
            return False

    def _check_column_name_pattern(self, column_name: str) -> str:
        """Check if the column name matches any common patterns."""
        column_name = column_name.lower()
        for dtype, patterns in self.column_patterns.items():
            if any(re.match(pattern, column_name, re.IGNORECASE) for pattern in patterns):
                return dtype
        return None

    def analyze_column(self, series):
        """Analyze a single column and suggest data type optimizations."""
        current_type = str(series.dtype)
        non_null_count = series.count()
        
        # Skip empty series or series with all null values
        if non_null_count == 0:
            return None
            
        # Get sample values for analysis
        sample_values = series.dropna().sample(min(10, non_null_count)).tolist()
        
        # Initialize variables
        suggested_type = None
        confidence = "low"
        reasons = []
        
        column_name = series.name
        
        # Check column name pattern first
        name_based_type = self._check_column_name_pattern(column_name)
        
        # If current type is object or string, perform deeper analysis
        if current_type in ['object', 'string']:
            # First check for categorical data with low cardinality
            nunique = series.nunique()
            if nunique < len(series) * 0.05:  # If unique values are less than 5% of total values
                suggested_type = 'category'
                confidence = 'high'
                reasons.append(f'Low cardinality ({nunique} unique values)')
                return {
                    'current_type': current_type,
                    'suggested_type': suggested_type,
                    'confidence': confidence,
                    'reason': reasons
                }
                
            # Then check for datetime
            if self._check_datetime_patterns(sample_values):
                suggested_type = 'datetime64[ns]'
                confidence = 'high'
                reasons.append('Values match common datetime patterns')
            
            # Check for boolean
            elif self._is_boolean_series(sample_values):
                suggested_type = 'boolean'
                confidence = 'high'
                reasons.append('Values are boolean-like')
            
            # Check for numeric/currency values
            elif not suggested_type and self._is_numeric_series(sample_values):
                suggested_type = 'float64'
                confidence = 'high'
                if any(any(symbol in str(x) for symbol in self.currency_symbols) for x in sample_values if pd.notna(x)):
                    reasons.append('Values are currency amounts')
                else:
                    reasons.append('Values are numeric')

        # If we haven't made a suggestion based on values but have a name-based suggestion
        if not suggested_type and name_based_type:
            if name_based_type == 'datetime':
                suggested_type = 'datetime64[ns]'
            elif name_based_type == 'boolean':
                suggested_type = 'boolean'
            elif name_based_type == 'numeric':
                # Only suggest numeric if the values look numeric
                if self._is_numeric_series(sample_values):
                    suggested_type = 'float64'
            elif name_based_type == 'categorical':
                suggested_type = 'category'
            
            if suggested_type:
                confidence = 'medium'
                reasons.append(f'Column name suggests {name_based_type} type')

        return {
            'current_type': current_type,
            'suggested_type': suggested_type,
            'confidence': confidence,
            'reason': reasons
        }

    def analyze_dataframe(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """Analyze all columns in a dataframe and provide type suggestions."""
        suggestions = {}
        for column in df.columns:
            analysis = self.analyze_column(df[column])
            if analysis is not None and analysis['suggested_type'] is not None and analysis['suggested_type'] != str(df[column].dtype):
                suggestions[column] = analysis
        return suggestions

def get_dtype_suggestions(df: pd.DataFrame) -> Dict[str, Dict]:
    """
    Analyze a dataframe and return suggested data type changes.
    
    Args:
        df (pd.DataFrame): Input dataframe to analyze
        
    Returns:
        Dict[str, Dict]: Dictionary of column names and their suggested type changes
    """
    analyzer = DataTypeAnalyzer()
    return analyzer.analyze_dataframe(df) 