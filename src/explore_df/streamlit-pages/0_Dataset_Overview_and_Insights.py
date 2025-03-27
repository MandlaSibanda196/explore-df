import streamlit as st
import pandas as pd
import numpy as np
from explore_df import plotter
from scipy import stats
import plotly.express as px
from src.data_quality import (
    get_dtype_suggestions,
    get_missing_value_suggestions,
    get_outlier_suggestions,
)

# Header section
st.title(":material/insights: Dataset Overview & Insights", anchor=False)
st.caption("A comprehensive overview of your dataset with automated insights and recommendations.")

df = st.session_state['df']

# Dataset Summary Section
with st.container(border=True):
    st.subheader("Dataset Overview", anchor=False)
    st.caption("Basic information about your dataset")
    
    # Basic metrics in first row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Records", f"{len(df):,}")
    with col2:
        st.metric("Features", f"{df.shape[1]:,}")
    with col3:
        bytes_usage = df.memory_usage(deep=True).sum()  # deep=True for accurate string memory usage
        if bytes_usage < 1024:  # Less than 1KB
            memory_str = f"{bytes_usage:,.0f} B"
        elif bytes_usage < 1024**2:  # Less than 1MB
            memory_str = f"{bytes_usage/1024:,.1f} KB"
        elif bytes_usage < 1024**3:  # Less than 1GB
            memory_str = f"{bytes_usage/(1024**2):,.1f} MB"
        else:  # GB or larger
            memory_str = f"{bytes_usage/(1024**3):,.1f} GB"
        st.metric("Memory Usage", memory_str)

    # Data type distribution
    dtypes = df.dtypes.value_counts()
    st.caption("**Data Type Distribution:**")
    for dtype, count in dtypes.items():
        st.write(f"- {dtype}: {count} columns")
    
    # Column details in an expander
    with st.expander("Detailed Column Information", icon=":material/table_chart:"):
        def get_detailed_type(series):
            if series.dtype == 'object':
                non_null = series.dropna()
                if len(non_null) > 0 and all(isinstance(x, str) for x in non_null):
                    return 'string'
                return 'mixed/object'
            return str(series.dtype)

        dtypes_df = pd.DataFrame({
            'Type': [get_detailed_type(df[col]) for col in df.columns],
            'Non-Null Count': df.count(),
            'Null Count': df.isna().sum(),
            'Unique Values': [df[col].nunique() for col in df.columns],
            'Sample Values': [str(df[col].sample(3).tolist()) for col in df.columns]
        })

        def highlight_missing(val):
            if isinstance(val, (int, np.integer)) and val > 0:
                return 'background-color: #ffcdd2'
            return ''

        st.dataframe(
            dtypes_df.style.applymap(highlight_missing, subset=['Null Count']),
            use_container_width=True
        )

# Data Quality Analysis
with st.container(border=True):
    st.subheader("Data Quality Analysis", anchor=False)
    st.caption("Analysis of data quality issues and potential problems")
    
    # Calculate quality metrics
    missing_cols = df.columns[df.isnull().any()].tolist()
    duplicate_rows = df.duplicated().sum()
    constant_cols = [col for col in df.columns if df[col].nunique() == 1]
    outlier_analysis = get_outlier_suggestions(df)
    
    quality_issues = []
    
    if missing_cols:
        missing_pcts = (df[missing_cols].isnull().sum() / len(df) * 100).round(1)
        for col, pct in missing_pcts.items():
            quality_issues.append(f"'{col}' has {pct}% missing values")
    
    if duplicate_rows:
        quality_issues.append(f"Found {duplicate_rows:,} duplicate rows ({(duplicate_rows/len(df)*100):.1f}% of data)")
    
    if constant_cols:
        quality_issues.append(f"Found {len(constant_cols)} constant columns: {', '.join(constant_cols)}")
    
    if outlier_analysis:
        total_outliers = sum(analysis['stats']['outlier_count'] for analysis in outlier_analysis.values())
        affected_cols = len(outlier_analysis)
        if total_outliers > 0:
            quality_issues.append(f"Found {total_outliers:,} extreme outliers across {affected_cols} columns")
            # Add details for columns with significant outliers (>1%)
            for col, analysis in outlier_analysis.items():
                if analysis['outlier_percentage'] > 1:
                    quality_issues.append(f"  • '{col}': {analysis['outlier_percentage']:.1f}% extreme values")
    
    if quality_issues:
        for issue in quality_issues:
            st.warning(issue, icon=":material/warning:")
        st.info("Visit the Data Quality Report page to fix these issues", icon=":material/arrow_forward:")
    else:
        st.success("No major data quality issues detected", icon=":material/check_circle:")

# Statistical Insights
with st.container(border=True):
    st.subheader("Statistical Insights", anchor=False)
    st.caption("Key statistical patterns and distributions in your data")
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns
    
    if len(numeric_cols) > 0:
        # Distribution Analysis
        skewed_cols = []
        bimodal_cols = []
        outlier_cols = []
        
        for col in numeric_cols:
            # Check skewness
            skewness = df[col].skew()
            if abs(skewness) > 1.5:
                skewed_cols.append((col, skewness))
            
            # Check for bimodality using kernel density estimation
            try:
                kde = stats.gaussian_kde(df[col].dropna())
                x = np.linspace(df[col].min(), df[col].max(), 100)
                density = kde(x)
                peaks = len([i for i in range(1, len(density)-1) if density[i-1] < density[i] > density[i+1]])
                if peaks > 1:
                    bimodal_cols.append(col)
            except:
                pass
            
            # Check for outliers using IQR method
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers = df[col][(df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR)]
            if len(outliers) > 0:
                outlier_cols.append((col, len(outliers)))
        
        if skewed_cols:
            st.markdown("##### Distribution Patterns")
            for col, skew in skewed_cols:
                direction = "positive" if skew > 0 else "negative"
                st.info(f"'{col}' shows {direction} skew ({skew:.2f}). Consider applying transformation.", icon=":material/trending_up:")
        
        if bimodal_cols:
            st.markdown("##### Multimodal Distributions")
            st.info(f"Potential multimodal distributions detected in: {', '.join(bimodal_cols)}", icon=":material/analytics:")
            st.caption("Consider investigating these features for distinct subgroups in your data.")
        
        if outlier_cols:
            st.markdown("##### Outlier Detection")
            for col, count in outlier_cols:
                st.warning(f"'{col}' has {count:,} potential outliers ({(count/len(df)*100):.1f}% of data)", icon=":material/warning:")

# Distribution Analysis
with st.container(border=True):
    st.subheader("Column Distributions", anchor=False)
    st.caption("Visual distribution of values across all columns")
    
    # Add column count selector
    cols_per_row = st.slider("Charts per row", min_value=1, max_value=8, value=3, help="Adjust the number of charts displayed per row")
    
    # Create rows of columns (dynamic based on slider)
    for i in range(0, len(df.columns), cols_per_row):
        cols = st.columns(cols_per_row)
        
        # Get the columns for this row
        current_cols = df.columns[i:i + cols_per_row]
        
        for j, col_name in enumerate(current_cols):
            with cols[j]:
                with st.container(border=True):
                    st.write(f"**{col_name}**")
                    
                    # Get column data
                    col_data = df[col_name]
                    
                    # Handle different data types
                    if pd.api.types.is_numeric_dtype(col_data):
                        # For numeric data, create histogram
                        fig = px.histogram(df, x=col_name, nbins=30)
                        fig.update_layout(
                            height=125,
                            showlegend=False,
                            margin=dict(t=0, b=0, l=0, r=0),
                            plot_bgcolor='white'
                        )
                    else:
                        # For categorical data, create bar chart of value counts
                        value_counts = col_data.value_counts().head(10)
                        fig = px.bar(x=value_counts.index, y=value_counts.values)
                        fig.update_layout(
                            height=125,
                            xaxis_title="",
                            yaxis_title="",
                            margin=dict(t=0, b=0, l=0, r=0),
                            plot_bgcolor='white'
                        )
                        if len(value_counts) > 10:
                            st.caption("Showing top 10 categories only")

                    # Display the plot
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                    
                    # Display quick stats
                    with st.expander("Show summary statistics", icon=":material/analytics:"):
                        if pd.api.types.is_numeric_dtype(col_data):
                            stats = pd.DataFrame({
                                'Metric': ['Mean', 'Median', 'Std', 'Min', 'Max'],
                                'Value': [
                                    f"{col_data.mean():.2f}",
                                    f"{col_data.median():.2f}",
                                    f"{col_data.std():.2f}",
                                    f"{col_data.min():.2f}",
                                    f"{col_data.max():.2f}"
                                ]
                            })
                        else:
                            stats = pd.DataFrame({
                                'Metric': ['Unique Values', 'Most Common', 'Most Common Count'],
                                'Value': [
                                    col_data.nunique(),
                                    col_data.mode().iloc[0],
                                    col_data.value_counts().iloc[0]
                                ]
                            })
                        st.dataframe(stats, hide_index=True)

# Feature Relationships
with st.container(border=True):
    st.subheader("Feature Relationships", anchor=False)
    st.caption("Analysis of relationships between numeric features")
    
    if len(numeric_cols) >= 2:
        # Correlation Analysis
        corr_matrix = df[numeric_cols].corr()
        high_corr = np.where(np.abs(corr_matrix) > 0.7)
        high_corr = [(corr_matrix.index[x], corr_matrix.columns[y], corr_matrix.iloc[x, y])
                     for x, y in zip(*high_corr) if x != y and x < y]
        
        if high_corr:
            st.markdown("##### Strong Correlations")
            for col1, col2, corr in high_corr:
                st.info(f"Strong {'positive' if corr > 0 else 'negative'} correlation ({corr:.2f}) between '{col1}' and '{col2}'", icon=":material/trending_up:")
                if abs(corr) > 0.9:
                    st.caption("Consider removing one of these features to reduce multicollinearity")
        
        st.write("")
        # Display correlation heatmap
        fig = plotter.create_correlation_heatmap(df)
        fig.update_layout(
            margin=dict(t=50, l=50, r=20, b=50),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        st.plotly_chart(fig, use_container_width=True)

# Recommendations
with st.container(border=True):
    st.subheader("Recommendations", anchor=False)
    st.caption("Suggested actions based on the analysis")
    
    recommendations = []
    
    # Missing value recommendations
    if missing_cols:
        if any(df[col].isnull().sum()/len(df) > 0.5 for col in missing_cols):
            recommendations.append("Consider removing columns with more than 50% missing values")
        recommendations.append("Investigate missing value patterns using the Data Quality Report page")
    
    # Distribution recommendations
    if skewed_cols:
        recommendations.append("Apply log or Box-Cox transformation to highly skewed features")
    
    # Outlier recommendations
    if outlier_cols:
        recommendations.append("Investigate outliers using the Data Quality Report page")
    
    # Feature engineering suggestions
    if len(categorical_cols) > 0:
        high_cardinality = [col for col in categorical_cols if df[col].nunique() > 100]
        if high_cardinality:
            recommendations.append(f"Consider encoding or grouping categories for high-cardinality features: {', '.join(high_cardinality)}")
    
    # Dimensionality recommendations
    if len(numeric_cols) > 10 and high_corr:
        recommendations.append("Consider dimensionality reduction (PCA/t-SNE) due to high feature correlations")
    
    if len(df) > 10000 and bytes_usage > 1024:
        recommendations.append("Consider using data sampling or chunking for more efficient analysis")
    
    for i, rec in enumerate(recommendations, 1):
        st.write(f"{i}. {rec}")
    
    if not recommendations:
        st.info("Your dataset appears to be well-structured. Proceed with your analysis!", icon=":material/check_circle:") 