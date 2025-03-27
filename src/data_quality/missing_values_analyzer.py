import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from sklearn.impute import SimpleImputer

class MissingValuesAnalyzer:
    def __init__(self):
        self.SMALL_PERCENTAGE = 5  # Consider 5% or less as small percentage
        self.strategies = {
            'numeric': [
                {
                    'name': 'mean',
                    'description': 'Replace missing values with the mean of the column',
                    'condition': lambda df, col: len(df) >= 3,  # Need at least 3 values for mean to make sense
                    'code': lambda col: f"df['{col}'] = df['{col}'].fillna(df['{col}'].mean())"
                },
                {
                    'name': 'median',
                    'description': 'Replace missing values with the median (middle value) of the column',
                    'condition': lambda df, col: len(df) >= 3,
                    'code': lambda col: f"df['{col}'] = df['{col}'].fillna(df['{col}'].median())"
                },
                {
                    'name': 'interpolate',
                    'description': 'Fill missing values using interpolation between existing values',
                    'condition': lambda df, col: len(df) >= 3,
                    'code': lambda col: f"df['{col}'] = df['{col}'].interpolate(method='linear')"
                },
                {
                    'name': 'zero',
                    'description': 'Replace missing values with zero',
                    'condition': lambda df, col: True,
                    'code': lambda col: f"df['{col}'] = df['{col}'].fillna(0)"
                }
            ],
            'categorical': [
                {
                    'name': 'mode',
                    'description': 'Replace missing values with the most frequent value',
                    'condition': lambda df, col: df[col].nunique() > 0,
                    'code': lambda col: f"df['{col}'] = df['{col}'].fillna(df['{col}'].mode()[0])"
                },
                {
                    'name': 'new_category',
                    'description': 'Replace missing values with "Unknown" or similar placeholder',
                    'condition': lambda df, col: True,
                    'code': lambda col: f"df['{col}'] = df['{col}'].fillna('Unknown')"
                }
            ],
            'datetime': [
                {
                    'name': 'forward_fill',
                    'description': 'Fill missing values with the previous valid value',
                    'condition': lambda df, col: True,
                    'code': lambda col: f"df['{col}'] = df['{col}'].fillna(method='ffill')"
                },
                {
                    'name': 'backward_fill',
                    'description': 'Fill missing values with the next valid value',
                    'condition': lambda df, col: True,
                    'code': lambda col: f"df['{col}'] = df['{col}'].fillna(method='bfill')"
                }
            ]
        }
        
        # Add drop strategies that apply to any column type
        self.drop_strategies = [
            {
                'name': 'drop_rows',
                'description': 'Drop rows with missing values in this column',
                'condition': lambda df, col: df[col].isna().sum() / len(df) <= self.SMALL_PERCENTAGE,
                'code': lambda col: f"df = df.dropna(subset=['{col}'])"
            }
        ]

    def get_column_type(self, series: pd.Series) -> str:
        """Determine the high-level type of a column."""
        if pd.api.types.is_numeric_dtype(series):
            return 'numeric'
        elif pd.api.types.is_datetime64_any_dtype(series):
            return 'datetime'
        else:
            return 'categorical'

    def analyze_missing_values(self, df: pd.DataFrame) -> Dict:
        """
        Analyze missing values in the dataframe and suggest solutions.
        
        Returns:
            Dict with analysis and suggestions for each column with missing values
        """
        results = {}
        
        # Get columns with missing values
        missing_cols = df.columns[df.isna().any()].tolist()
        
        for col in missing_cols:
            missing_count = df[col].isna().sum()
            missing_percentage = (missing_count / len(df)) * 100
            col_type = self.get_column_type(df[col])
            
            # Get applicable strategies for this column type
            strategies = self.strategies.get(col_type, []).copy()
            
            # Add drop strategies if they meet the conditions
            for drop_strategy in self.drop_strategies:
                if drop_strategy['condition'](df, col):
                    strategies.append(drop_strategy)
            
            # Filter strategies based on their conditions
            valid_strategies = [
                {
                    'name': strategy['name'],
                    'description': strategy['description'],
                    'code': strategy['code'](col)
                }
                for strategy in strategies
                if strategy['condition'](df, col)
            ]
            
            # Get sample of non-null values
            non_null_sample = df[col].dropna().sample(min(5, len(df[col].dropna()))).tolist()
            
            results[col] = {
                'missing_count': missing_count,
                'missing_percentage': missing_percentage,
                'column_type': col_type,
                'strategies': valid_strategies,
                'non_null_sample': non_null_sample
            }
        
        return results

    def apply_strategy(self, df: pd.DataFrame, column: str, strategy_code: str) -> pd.DataFrame:
        """
        Apply the selected strategy to the dataframe.
        
        Args:
            df: The input dataframe
            column: The column to apply the strategy to
            strategy_code: The code to execute
        
        Returns:
            Modified dataframe
        """
        try:
            # Create a copy of the dataframe
            df_copy = df.copy()
            
            # Execute the strategy code
            exec(strategy_code, {'df': df_copy, 'pd': pd, 'np': np})
            
            return df_copy
            
        except Exception as e:
            raise Exception(f"Failed to apply strategy: {str(e)}")

def get_missing_value_suggestions(df: pd.DataFrame) -> Dict:
    """
    Analyze a dataframe and return suggestions for handling missing values.
    
    Args:
        df (pd.DataFrame): Input dataframe to analyze
        
    Returns:
        Dict with analysis and suggestions for each column with missing values
    """
    analyzer = MissingValuesAnalyzer()
    return analyzer.analyze_missing_values(df) 