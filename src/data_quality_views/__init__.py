"""
Data Quality Views Module

This module contains Streamlit view components for rendering different aspects of data quality analysis.
Each view component is responsible for visualizing and allowing interaction with specific types of data
quality issues, such as:
- Data type mismatches
- Missing values
- Consistency issues
- Accuracy problems
- Uniqueness violations
- Timeliness concerns
- Validity issues
- Outlier detection

Each view provides an interactive interface for:
1. Displaying detected issues
2. Showing relevant statistics and visualizations
3. Offering fix suggestions
4. Previewing changes
5. Applying selected fixes to the dataset
"""

from .data_type_analysis import render_data_type_analysis
from .missing_values_analysis import render_missing_values_analysis
from .consistency_analysis import render_consistency_analysis
from .accuracy_analysis import render_accuracy_analysis
from .uniqueness_analysis import render_uniqueness_analysis
from .timeliness_analysis import render_timeliness_analysis
from .validity_analysis import render_validity_analysis
from .outlier_analysis import render_outlier_analysis

__all__ = [
    'render_data_type_analysis',
    'render_missing_values_analysis',
    'render_consistency_analysis',
    'render_accuracy_analysis',
    'render_uniqueness_analysis',
    'render_timeliness_analysis',
    'render_validity_analysis',
    'render_outlier_analysis'
] 