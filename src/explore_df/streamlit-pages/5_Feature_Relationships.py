import streamlit as st
import pandas as pd
import numpy as np
from explore_df import plotter

st.title("🔗 Feature Relationships", anchor=False)

df = st.session_state['df']

# Feature Visualization Section
with st.container(border=True):
    st.subheader("📊 Feature Visualization", anchor=False, divider="blue")
    st.caption("Explore relationships between features using different visualization techniques.")
    
    viz_type = st.radio(
        "Select Visualization Type",
        ["Scatter Matrix", "Density Heatmap", "Parallel Categories", "Radar Plot"],
        horizontal=True,
        help="Choose the type of visualization that best suits your analysis needs"
    )

    # Scatter Matrix
    if viz_type == "Scatter Matrix":
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
            st.warning("⚠️ No numeric columns found in the dataset!")
        else:
            st.caption("Compare multiple numeric variables simultaneously. Best with 2-4 variables for clarity.")
            selected_cols = st.multiselect(
                "Select Numeric Variables",
                numeric_cols,
                default=list(numeric_cols[:min(3, len(numeric_cols))]),
                max_selections=4,
                help="Select up to 4 numeric columns to compare"
            )
            if selected_cols:
                fig = plotter.create_scatter_matrix(df, selected_cols)
                fig.update_layout(
                    height=600,
                    title=None,
                    plot_bgcolor='white',
                    paper_bgcolor='white'
                )
                st.plotly_chart(fig, use_container_width=True)

    # Density Heatmap
    elif viz_type == "Density Heatmap":
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) < 2:
            st.warning("⚠️ Need at least 2 numeric columns for density heatmap!")
        else:
            st.caption("Visualize the density of points between two numeric variables.")
            col1, col2 = st.columns(2)
            with col1:
                x_col = st.selectbox(
                    "Select X-axis Variable", 
                    numeric_cols, 
                    key="x_heatmap",
                    help="Variable for the horizontal axis"
                )
            with col2:
                y_col = st.selectbox(
                    "Select Y-axis Variable", 
                    numeric_cols, 
                    key="y_heatmap",
                    help="Variable for the vertical axis"
                )
            
            if x_col and y_col:
                fig = plotter.create_density_heatmap(df, x_col, y_col)
                fig.update_layout(
                    height=600,
                    title=dict(
                        text=f"Density Heatmap: {x_col} vs {y_col}",
                        x=0.45,
                        y=0.95
                    ),
                    plot_bgcolor='white',
                    paper_bgcolor='white'
                )
                st.plotly_chart(fig, use_container_width=True)

    # Parallel Categories
    elif viz_type == "Parallel Categories":
        cat_cols = df.select_dtypes(include=['object', 'category']).columns
        if len(cat_cols) < 2:
            st.warning("⚠️ Need at least 2 categorical columns for parallel categories plot!")
        else:
            st.caption("Visualize relationships between multiple categorical variables.")
            selected_cols = st.multiselect(
                "Select Categorical Variables",
                cat_cols,
                default=list(cat_cols[:min(3, len(cat_cols))]),
                help="Select categorical columns to visualize their relationships"
            )
            if selected_cols:
                try:
                    fig = plotter.create_parallel_categories(df, selected_cols)
                    fig.update_layout(
                        height=600,
                        title=dict(
                            text="Category Flow Diagram",
                            x=0.45,
                            y=0.95
                        ),
                        plot_bgcolor='white',
                        paper_bgcolor='white'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error("Error creating parallel categories plot. Please check for missing or invalid values.")
                    st.caption(f"Details: {str(e)}")

    # Radar Plot
    else:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) < 3:
            st.warning("⚠️ Need at least 3 numeric columns for radar plot!")
        else:
            st.caption("Compare multiple numeric variables on a radial plot. Best with 3-8 variables.")
            selected_cols = st.multiselect(
                "Select Numeric Variables",
                numeric_cols,
                default=list(numeric_cols[:min(5, len(numeric_cols))]),
                max_selections=8,
                help="Select 3-8 numeric columns to compare"
            )
            if len(selected_cols) >= 3:
                fig = plotter.create_radar_plot(df, selected_cols)
                fig.update_layout(
                    height=600,
                    title=dict(
                        text="Feature Comparison Radar",
                        x=0.45,
                        y=0.95
                    ),
                    plot_bgcolor='white',
                    paper_bgcolor='white'
                )
                st.plotly_chart(fig, use_container_width=True)
            elif selected_cols:
                st.info("ℹ️ Please select at least 3 variables for the radar plot")

# Correlation Analysis Section
with st.container(border=True):
    st.subheader("📈 Correlation Analysis", anchor=False, divider="violet")
    st.caption("Analyze statistical relationships between numeric variables.")
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) < 2:
        st.warning("⚠️ Need at least 2 numeric columns for correlation analysis!")
    else:
        corr_type = st.selectbox(
            "Select Correlation Method",
            ["Pearson", "Spearman", "Kendall"],
            help="""
            - Pearson: Linear correlation (most common)
            - Spearman: Monotonic relationships, less sensitive to outliers
            - Kendall: Ordinal relationships, robust to outliers
            """
        )

        try:
            correlations = plotter.create_correlation_analysis(df, method=corr_type)
            if correlations is not None:
                fig = plotter.create_correlation_heatmap(correlations)
                fig.update_layout(
                    height=600,
                    title=dict(
                        text=f"{corr_type} Correlation Heatmap",
                        x=0.45,
                        y=0.95
                    ),
                    plot_bgcolor='white',
                    paper_bgcolor='white'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Could not calculate correlations for the selected method.")
        except Exception as e:
            st.error("Error calculating correlations")
            st.caption(f"Details: {str(e)}") 