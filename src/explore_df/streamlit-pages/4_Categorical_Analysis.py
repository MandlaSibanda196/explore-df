import streamlit as st
import pandas as pd
import numpy as np
from explore_df import plotter

st.title(":material/category: Categorical Analysis", anchor=False)
st.caption("Explore relationships and patterns in categorical variables")

df = st.session_state['df']
cat_cols = df.select_dtypes(include=['object', 'category']).columns

if len(cat_cols) == 0:
    st.warning(":material/alert: No categorical columns found in the dataset!")
    st.stop()

# Hierarchical view
st.subheader(":material/donut_small: Hierarchical Analysis", anchor=False, divider="grey")
st.caption(":material/info: Explore hierarchical relationships between categorical variables using an interactive sunburst chart.")

col1, col2 = st.columns([2, 1])
with col1:
    with st.container(border=True):
        selected_cols = st.multiselect(
            ":material/atr: Select Categories (order matters)",
            cat_cols,
            max_selections=3,
            help="Choose up to 3 categorical columns. The order determines the hierarchy from center to outer rings.",
            key="categorical_cols"
        )

if selected_cols:
    # Create a copy of the dataframe with selected columns
    plot_df = df[selected_cols].copy()
    
    # Data preprocessing
    try:
        # Handle missing and empty values
        for col in selected_cols:
            # Convert column to string type first
            plot_df[col] = plot_df[col].astype(str)
            # Replace empty strings, whitespace, and 'nan' with placeholder
            mask = (plot_df[col].str.strip() == '') | (plot_df[col].str.lower() == 'nan')
            plot_df.loc[mask, col] = "(Missing)"
            # Ensure no empty values remain
            if plot_df[col].str.strip().eq('').any():
                raise ValueError(f"Column {col} still contains empty values after preprocessing")
        
        # Calculate total combinations
        with col2:
            with st.container(border=True):
                total_combinations = plot_df.value_counts().shape[0]
                st.metric(
                    ":material/fingerprint: Unique Combinations",
                    total_combinations,
                    help="Total number of unique combinations found in the selected categories"
                )
        
        # Calculate percentages for each level
        for col in selected_cols:
            col_counts = plot_df[col].value_counts()
            col_percentages = (col_counts / len(plot_df) * 100).round(1)
            # Add percentage to each value
            plot_df[col] = plot_df[col].map(lambda x: f"{x} ({col_percentages[x]}%)")
        
        # Create the visualization
        with st.container(border=True):
            fig = plotter.create_sunburst(plot_df, selected_cols)
            fig.update_layout(
                margin=dict(t=30, l=20, r=20, b=20),
                plot_bgcolor='white',
                paper_bgcolor='white',
                height=700
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Show detailed breakdown
        with st.expander(":material/table: Show detailed breakdown"):
            st.caption(":material/info: Detailed distribution of combinations:")
            # Calculate original value counts without percentages for the table
            orig_value_counts = df[selected_cols].value_counts().reset_index()
            orig_value_counts.columns = [*selected_cols, 'Count']
            orig_value_counts['Percentage'] = (orig_value_counts['Count'] / len(df) * 100).round(1).map(lambda x: f"{x}%")
            
            st.dataframe(
                orig_value_counts,
                column_config={
                    "Count": st.column_config.NumberColumn(
                        "Count",
                        help="Number of occurrences",
                        format="%d"
                    ),
                    "Percentage": st.column_config.TextColumn(
                        "Percentage",
                        help="Percentage of total"
                    )
                },
                hide_index=True,
                use_container_width=True
            )
            
    except Exception as e:
        st.error(":material/alert: Error creating visualization")
        with st.expander(":material/help: Troubleshooting"):
            st.caption(f":material/error: Error details: {str(e)}")
            st.markdown("""
            **Common solutions:**
            1. :material/check_circle: Check if your selected columns contain valid categorical data
            2. :material/refresh: Try selecting different columns
            3. :material/data_check: Ensure your data doesn't contain special characters or invalid values
            """)
else:
    with col2:
        st.write("")  # Empty space for layout consistency
    st.info(":material/arrow_upward: Select categories above to visualize their hierarchical relationship") 