import streamlit as st
import pandas as pd
import numpy as np
from explore_df import plotter
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from statsmodels.tsa.seasonal import seasonal_decompose

st.title(":material/schedule: Time Series Analysis", anchor=False)
st.caption("Analyze temporal patterns and trends in your data")

df = st.session_state['df']

# Data Selection and Preprocessing
with st.container(border=True):
    st.subheader(":material/calendar_clock: Data Selection", anchor=False, divider="grey")
    
    # Identify datetime columns
    date_cols = df.select_dtypes(include=['datetime64']).columns

    # If no datetime columns, check if any object columns can be converted
    if len(date_cols) == 0:
        potential_date_cols = []
        for col in df.select_dtypes(include=['object']).columns:
            try:
                pd.to_datetime(df[col])
                potential_date_cols.append(col)
            except:
                continue
        
        if potential_date_cols:
            st.info(":material/calendar: No datetime columns found, but some columns could be converted to datetime.")
            with st.container(border=True):
                date_col = st.selectbox(
                    ":material/calendar_today: Select Date Column",
                    potential_date_cols,
                    key="time_series_date_col"
                )
            df[date_col] = pd.to_datetime(df[date_col])
        else:
            st.warning(":material/alert: No datetime columns found in the dataset!")
            st.stop()
    else:
        with st.container(border=True):
            date_col = st.selectbox(
                ":material/calendar_today: Select Date Column",
                date_cols,
                key="time_series_date_col"
            )

    # Select value column
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    with st.container(border=True):
        value_col = st.selectbox(
            ":material/timeline: Select Value Column",
            numeric_cols,
            key="time_series_value_col"
        )

# Handle missing values by dropping them
df_clean = df.dropna(subset=[date_col, value_col])
if len(df_clean) < len(df):
    st.caption(f":material/error: {len(df) - len(df_clean)} rows with missing values were removed to ensure accurate time series analysis.")

# Time series analysis
if len(df_clean) > 0:
    # Time Series Overview
    with st.container(border=True):
        st.subheader("Time Series Overview", anchor=False, divider="grey")
        
        metrics = plotter.create_time_series_metrics(df_clean, date_col, value_col)
        
        col1, col2, col3 = st.columns(3)

        with col1:
            with st.container(border=True):
                st.markdown(":material/trending_up: **Trend Analysis**")
                trend = metrics["Trend"]
                st.metric(
                    "Trend Direction",
                    trend["Trend"],
                    delta_color="normal" if trend["Trend"] == "No Trend" else ("normal" if trend["Trend"] == "Upward" else "inverse")
                )

        with col2:
            with st.container(border=True):
                st.markdown(":material/spoke: **Model Fit**")
                st.metric(
                    "R-squared",
                    f"{trend['R-squared']:.4f}",
                    help="Measure of how well the trend line fits the data"
                )

        with col3:
            with st.container(border=True):
                st.markdown(":material/planner_review: **Seasonality**")
                seasonality = metrics["Seasonality"]
                st.metric(
                    "Seasonal Strength",
                    f"{seasonality['Seasonal Strength']:.4f}",
                    help="Measure of seasonal pattern strength (0-1)"
                )

    # Decomposition Analysis
    with st.container(border=True):
        st.subheader(" Time Series Decomposition", anchor=False, divider="grey")
        st.caption(":material/info: Breaking down the time series into its core components: trend, seasonality, and residuals.")
        
        try:
            # Create decomposition
            result = seasonal_decompose(df_clean[value_col], period=30)
            
            components = {
                "Original Series": (df_clean[date_col], df_clean[value_col], value_col, ":material/show_chart:"),
                "Trend Component": (df_clean[date_col], result.trend, f"{value_col} (Trend)", ":material/trending_up:"),
                "Seasonal Component": (df_clean[date_col], result.seasonal, f"{value_col} (Seasonal)", ":material/planner_review:"),
                "Residual Component": (df_clean[date_col], result.resid, f"{value_col} (Residual)", ":material/ssid_chart:")
            }
            
            for title, (dates, values, y_label, icon) in components.items():
                with st.container(border=True):
                    st.markdown(f"{icon} **{title}**")
                    component_df = pd.DataFrame({
                        date_col: dates,
                        y_label: values
                    }).dropna()
                    
                    fig = plotter.create_time_series_plot(
                        component_df, 
                        date_col, 
                        y_label
                    )
                    fig.update_layout(
                        margin=dict(t=30, l=50, r=20, b=50),
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        modebar=dict(
                            remove=['zoom', 'pan', 'select', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d']
                        )
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f":material/alert: Error creating decomposition plot: {str(e)}")

else:
    st.error(":material/alert: No valid data available after removing missing values. Please check your data.")
    st.stop() 