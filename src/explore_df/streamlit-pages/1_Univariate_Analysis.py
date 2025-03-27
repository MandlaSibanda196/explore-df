import streamlit as st
import pandas as pd
import numpy as np
from explore_df import plotter
from scipy import stats

def show_statistical_summary(df: pd.DataFrame, column: str):
    """Show detailed statistical summary for a numerical column."""
    if not pd.api.types.is_numeric_dtype(df[column]):
        return
    
    data = df[column].dropna()
    stats_dict = {
        "Mean": data.mean(),
        "Median": data.median(),
        "Mode": data.mode().iloc[0] if not data.mode().empty else None,
        "Std Dev": data.std(),
        "Variance": data.var(),
        "Skewness": stats.skew(data),
        "Kurtosis": stats.kurtosis(data),
        "IQR": data.quantile(0.75) - data.quantile(0.25),
        "Range": data.max() - data.min(),
        "Min": data.min(),
        "Max": data.max(),
        "25%": data.quantile(0.25),
        "75%": data.quantile(0.75)
    }
    return pd.Series(stats_dict)

def get_distribution_insights(stats_summary):
    """Generate insights about the distribution of data."""
    insights = []
    
    # Skewness insights
    skewness = stats_summary["Skewness"]
    if abs(skewness) < 0.5:
        insights.append("The distribution is approximately symmetric")
    elif skewness > 1:
        insights.append("The distribution is strongly positively skewed (right-tailed)")
    elif skewness > 0.5:
        insights.append("The distribution is moderately positively skewed")
    elif skewness < -1:
        insights.append("The distribution is strongly negatively skewed (left-tailed)")
    elif skewness < -0.5:
        insights.append("The distribution is moderately negatively skewed")
    
    # Outlier insights
    mean_median_diff = abs(stats_summary["Mean"] - stats_summary["Median"])
    std_dev = stats_summary["Std Dev"]
    if mean_median_diff > std_dev:
        insights.append("⚠️ Large difference between mean and median suggests presence of outliers")
    
    # Spread insights
    cv = std_dev / stats_summary["Mean"] if stats_summary["Mean"] != 0 else 0
    if cv > 1:
        insights.append(" High variability in the data (CV > 1)")
    elif cv < 0.1:
        insights.append("Low variability in the data (CV < 0.1)")
    
    # Kurtosis insights
    kurtosis = stats_summary["Kurtosis"]
    if abs(kurtosis) < 0.5:
        insights.append(" Normal peak in distribution (mesokurtic)")
    elif kurtosis > 1:
        insights.append("Heavy tails with high peak (leptokurtic)")
    elif kurtosis < -0.5:
        insights.append("Light tails with flat peak (platykurtic)")
    
    return insights

def get_categorical_insights(value_counts, total_count):
    """Generate insights about categorical data."""
    insights = []
    
    # Diversity insights
    unique_ratio = len(value_counts) / total_count
    if unique_ratio > 0.9:
        insights.append("🎯 High cardinality: Almost every value is unique")
    elif unique_ratio < 0.01:
        insights.append("🎯 Low cardinality: Very few unique values")
    
    # Dominance insights
    top_value_ratio = value_counts.iloc[0] / total_count
    if top_value_ratio > 0.9:
        insights.append(f"📊 Dominant category: '{value_counts.index[0]}' appears in {top_value_ratio:.1%} of records")
    
    # Balance insights
    if len(value_counts) > 1:
        balance_ratio = value_counts.iloc[-1] / value_counts.iloc[0]
        if balance_ratio < 0.01:
            insights.append("⚖️ Highly imbalanced distribution")
        elif balance_ratio > 0.9:
            insights.append("⚖️ Well-balanced distribution")
    
    return insights

st.title(":material/analytics: Univariate Analysis", anchor=False)
st.caption("Analyze individual variables in your dataset")

# Get data from session state
df = st.session_state['df']

# Column selection without type indicator
col_options = [col for col in df.columns]
selected_option = st.selectbox(
    ":material/view_column: Select Column for Analysis",
    col_options,
    key="univariate_column_select"
)
column = selected_option.split(" (")[0]  # Extract column name

# Create a clean overview section
with st.container(border=True):
    st.subheader(":material/info: Column Overview", anchor=False, divider="grey")
    
    # Create three columns for basic stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with st.container(border=True):
            st.markdown(":material/data_array: **Data Type**")
            st.write(str(df[column].dtype))
    
    with col2:
        with st.container(border=True):
            unique_pct = round((df[column].nunique()/len(df)) * 100, 1)
            st.markdown(":material/fingerprint: **Unique Values**")
            st.write(f"{df[column].nunique()} ({unique_pct}% of total)")
    
    with col3:
        with st.container(border=True):
            missing_pct = round((df[column].isna().sum()/len(df)) * 100, 1)
            st.markdown(":material/priority_high: **Missing Values**")
            st.write(f"{df[column].isna().sum()} ({missing_pct}% of total)")

# Main analysis section
if pd.api.types.is_numeric_dtype(df[column]):
    with st.container(border=True):
        st.subheader(":material/bar_chart_4_bars: Distribution Analysis", anchor=False, divider="grey")
        
        # Create two columns for the main stats
        col1, col2 = st.columns([2, 1])
        
        with col1:
            stats_summary = show_statistical_summary(df, column)
            
            # Create two sub-columns for central tendency and spread
            stat_col1, stat_col2 = st.columns(2)
            
            with stat_col1:
                with st.container(border=True):
                    st.markdown(":material/target: **Central Tendency**")
                    metrics = {
                        "Mean": stats_summary["Mean"],
                        "Median": stats_summary["Median"],
                        "Mode": stats_summary["Mode"]
                    }
                    for name, value in metrics.items():
                        formatted_value = round(value, 2) if value is not None else "N/A"
                        st.write(f"**{name}:** {formatted_value}")
            
            with stat_col2:
                with st.container(border=True):
                    st.markdown(":material/arrow_range: **Spread & Shape**")
                    metrics = {
                        "Std Dev": stats_summary["Std Dev"],
                        "IQR": stats_summary["IQR"],
                        "Range": stats_summary["Range"]
                    }
                    for name, value in metrics.items():
                        formatted_value = round(value, 2)
                        st.write(f"**{name}:** {formatted_value}")
        
        with col2:
            with st.container(border=True):
                st.markdown(":material/lightbulb: **Distribution Insights**")
                insights = get_distribution_insights(stats_summary)
                for insight in insights:
                    st.write(insight)

else:  # Categorical analysis
    value_counts = df[column].value_counts()  # We still need this for the pie chart

# Visualization section
with st.container(border=True):
    st.subheader(":material/bar_chart: Visualizations", anchor=False, divider="grey")
    
    col1, col2 = st.columns(2)

    with col1:
        if pd.api.types.is_numeric_dtype(df[column]):
            # Use histogram with kde
            fig = plotter.create_histogram(df, column, kde=True)
            fig.update_layout(
                title=dict(
                    text=f'Distribution of {column}',
                    x=0.5,
                    y=0.95,
                    yanchor='top'
                ),
                margin=dict(t=50, l=10, r=10, b=10),
                plot_bgcolor='white',
                paper_bgcolor='white',
                modebar=dict(
                    remove=['zoom', 'pan', 'select', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d']
                )
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("")  # Add some spacing

    with col2:
        if pd.api.types.is_numeric_dtype(df[column]):
            fig = plotter.create_boxplot(df, column)
            fig.update_layout(
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("")  # Add some spacing

    # If categorical, show bar chart using full width
    if not pd.api.types.is_numeric_dtype(df[column]):
        fig = plotter.create_bar_chart(df, column)
        fig.update_layout(
            title=dict(
                text=f'Distribution of {column} (Top Categories)',
                x=0.5,
                y=0.95,
                yanchor='top'
            ),
            margin=dict(t=50, l=50, r=20, b=50),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        st.plotly_chart(fig, use_container_width=True) 