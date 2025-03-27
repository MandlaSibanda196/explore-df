import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from data_quality import (
    get_dtype_suggestions,
    get_missing_value_suggestions,
    get_accuracy_suggestions,
    get_consistency_suggestions,
    get_timeliness_suggestions,
    get_uniqueness_suggestions,
    get_validity_suggestions,
    get_outlier_suggestions
)
from data_quality_views import (
    render_data_type_analysis,
    render_missing_values_analysis,
    render_consistency_analysis,
    render_accuracy_analysis,
    render_uniqueness_analysis,
    render_timeliness_analysis,
    render_validity_analysis,
    render_outlier_analysis
)

# Initialize session state for storing issues and suggestions
if 'data_quality_issues' not in st.session_state:
    st.session_state.data_quality_issues = {
        'consistency': [],
        'accuracy': [],
        'uniqueness': [],
        'timeliness': [],
        'validity': []
    }

if 'accepted_suggestions' not in st.session_state:
    st.session_state['accepted_suggestions'] = []

# Page config and header
st.title(":material/checklist: Data Quality Report", anchor=False)
st.caption("Analyze and improve the quality of your dataset")
st.write("")

df = st.session_state['df']

# Function to analyze data quality
def analyze_data_quality(df):
    issues = {
        'consistency': [],
        'accuracy': [],
        'uniqueness': [],
        'timeliness': [],
        'validity': []
    }
    
    # Consistency checks
    def check_mixed_types(series):
        if series.dtype == 'object':
            numeric_mask = pd.to_numeric(series, errors='coerce').notna()
            if numeric_mask.any() and (~numeric_mask).any():
                return True
        return False
    
    mixed_type_cols = [col for col in df.columns if check_mixed_types(df[col])]
    if mixed_type_cols:
        issues['consistency'].append(f"Mixed data types in: {', '.join(mixed_type_cols)}")
    
    # Accuracy checks
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
    for col in numeric_cols:
        if any(word in col.lower() for word in ['age', 'count', 'quantity', 'amount', 'price', 'cost']):
            neg_count = (df[col] < 0).sum()
            if neg_count > 0:
                issues['accuracy'].append(f"{neg_count} negative values in '{col}'")
    
    # Uniqueness checks
    exact_duplicates = df.duplicated().sum()
    if exact_duplicates > 0:
        issues['uniqueness'].append(f"Found {exact_duplicates} duplicate rows")
    
    # Timeliness checks
    date_cols = df.select_dtypes(include=['datetime64']).columns
    if len(date_cols) > 0:
        for col in date_cols:
            df_sorted = df.sort_values(col)
            time_diffs = df_sorted[col].diff()
            large_gaps = time_diffs[time_diffs > time_diffs.median() * 5]
            if not large_gaps.empty:
                issues['timeliness'].append(f"Found {len(large_gaps)} large time gaps in '{col}'")
    
    # Validity checks
    categorical_cols = df.select_dtypes(include=['object']).columns
    for col in categorical_cols:
        if 'email' in col.lower():
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            invalid_emails = df[~df[col].str.match(email_pattern, na=True)].shape[0]
            if invalid_emails > 0:
                issues['validity'].append(f"Found {invalid_emails} invalid email formats in '{col}'")
    
    return issues

# Run analysis and store results
st.session_state.data_quality_issues = analyze_data_quality(df)

# Display overall summary at the top
with st.container(border=True):
    st.subheader("Summary", anchor=False, divider="grey")
    
    # Get all suggestions and organize them
    issue_categories = []
    
    # Data Types
    dtype_suggestions = get_dtype_suggestions(df)
    if dtype_suggestions:
        issue_categories.append({
            'name': 'Data Types',
            'icon': ':material/database:',
            'count': len(dtype_suggestions),
            'details': [f"• {len(dtype_suggestions)} columns need type optimization"]
        })
    
    # Missing Values
    missing_suggestions = get_missing_value_suggestions(df)
    if missing_suggestions:
        total_missing = sum(analysis['missing_count'] for analysis in missing_suggestions.values())
        issue_categories.append({
            'name': 'Missing Values',
            'icon': ':material/help_outline:',
            'count': len(missing_suggestions),
            'details': [
                f"• {total_missing:,} total missing values across {len(missing_suggestions)} columns"
            ]
        })
    
    # Consistency
    consistency_suggestions = get_consistency_suggestions(df)
    if consistency_suggestions:
        issue_categories.append({
            'name': 'Consistency',
            'icon': ':material/check_circle:',
            'count': len(consistency_suggestions),
            'details': [f"• {len(consistency_suggestions)} columns have format issues"]
        })
    
    # Accuracy
    accuracy_suggestions = get_accuracy_suggestions(df)
    if accuracy_suggestions:
        total_issues = sum(len(analysis['issues']) for analysis in accuracy_suggestions.values())
        issue_categories.append({
            'name': 'Accuracy',
            'icon': ':material/analytics:',
            'count': len(accuracy_suggestions),
            'details': [
                f"• {total_issues} accuracy issues found • Affects {len(accuracy_suggestions)} columns"
            ]
        })
    
    # Uniqueness
    uniqueness_suggestions = get_uniqueness_suggestions(df)
    if uniqueness_suggestions:
        details = []
        exact_duplicates = any('exact_duplicates' in key for key in uniqueness_suggestions.keys())
        id_duplicates = sum(1 for key in uniqueness_suggestions.keys() if 'id' in key.lower() and 'exact_duplicates' not in key)
        other_duplicates = len(uniqueness_suggestions) - (1 if exact_duplicates else 0) - id_duplicates
        
        if exact_duplicates:
            details.append("• Has exact duplicate rows")
        if id_duplicates > 0:
            details.append(f"• {id_duplicates} columns have duplicate IDs")
        if other_duplicates > 0:
            details.append(f"• {other_duplicates} columns have uniqueness issues")
        
        issue_categories.append({
            'name': 'Uniqueness',
            'icon': ':material/fingerprint:',
            'count': len(uniqueness_suggestions),
            'details': details
        })
    
    # Timeliness
    timeliness_suggestions = get_timeliness_suggestions(df)
    if timeliness_suggestions:
        total_issues = sum(len(analysis['issues']) for analysis in timeliness_suggestions.values())
        issue_categories.append({
            'name': 'Timeliness',
            'icon': ':material/schedule:',
            'count': len(timeliness_suggestions),
            'details': [
                f"• {total_issues} timing issues found • Affects {len(timeliness_suggestions)} columns"
            ]
        })
    
    # Validity
    validity_suggestions = get_validity_suggestions(df)
    if validity_suggestions:
        issue_categories.append({
            'name': 'Validity',
            'icon': ':material/verified:',
            'count': len(validity_suggestions),
            'details': [f"• {len(validity_suggestions)} columns have invalid values"]
        })
    
    # Outliers
    outlier_suggestions = get_outlier_suggestions(df)
    if outlier_suggestions:
        total_outliers = sum(analysis['stats']['outlier_count'] for analysis in outlier_suggestions.values())
        issue_categories.append({
            'name': 'Outliers',
            'icon': ':material/trending_up:',
            'count': len(outlier_suggestions),
            'details': [f"• {total_outliers:,} total outliers detected • Affects {len(outlier_suggestions)} columns"]
        })
    
    total_categories = len(issue_categories)
    
    if total_categories == 0:
        st.success(":material/check_circle: No data quality issues found in your dataset!")
    else:
        st.error(f":material/error: Found issues in {total_categories} data quality categories")
        
        # Determine layout based on number of categories
        if total_categories <= 3:
            # Single row with equal columns
            cols = st.columns(total_categories)
            for col, category in zip(cols, issue_categories):
                with col:
                    with st.container(border=True):
                        st.markdown(f"**{category['icon']} {category['name']}** ({category['count']})")
                        for detail in category['details']:
                            st.caption(detail)
        
        elif total_categories <= 6:
            # Two rows with up to 3 columns each
            row1_count = (total_categories + 1) // 2
            row2_count = total_categories - row1_count
            
            # First row
            cols = st.columns(row1_count)
            for col, category in zip(cols, issue_categories[:row1_count]):
                with col:
                    with st.container(border=True):
                        st.markdown(f"**{category['icon']} {category['name']}** ({category['count']})")
                        for detail in category['details']:
                            st.caption(detail)
            
            st.write("")  # Add some spacing between rows
            
            # Second row
            cols = st.columns(row2_count)
            for col, category in zip(cols, issue_categories[row1_count:]):
                with col:
                    with st.container(border=True):
                        st.markdown(f"**{category['icon']} {category['name']}** ({category['count']})")
                        for detail in category['details']:
                            st.caption(detail)
        
        else:
            # Three rows with up to 3 columns each
            for i in range(0, total_categories, 3):
                row_categories = issue_categories[i:i+3]
                cols = st.columns(len(row_categories))
                for col, category in zip(cols, row_categories):
                    with col:
                        with st.container(border=True):
                            st.markdown(f"**{category['icon']} {category['name']}** ({category['count']})")
                            for detail in category['details']:
                                st.caption(detail)
                if i + 3 < total_categories:
                    st.write("")  # Add spacing between rows
        
        st.divider()
        st.info("Check each tab below for detailed analysis and fix suggestions")

st.divider()
# Main Analysis Tabs
tab1, tab2, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "Data Types", "Missing Values", "Consistency", 
    "Accuracy", "Uniqueness", "Timeliness", "Validity", "Outliers"
])

with tab1:
    render_data_type_analysis(df, dtype_suggestions)

with tab2:
    render_missing_values_analysis(df, missing_suggestions)

with tab4:
    render_consistency_analysis(df, consistency_suggestions)

with tab5:
    render_accuracy_analysis(df, accuracy_suggestions)

with tab6:
    render_uniqueness_analysis(df, uniqueness_suggestions)

with tab7:
    render_timeliness_analysis(df, timeliness_suggestions)

with tab8:
    render_validity_analysis(df, validity_suggestions)

with tab9:
    render_outlier_analysis(df, outlier_suggestions)



