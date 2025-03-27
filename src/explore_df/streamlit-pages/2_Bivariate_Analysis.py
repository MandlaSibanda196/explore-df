import streamlit as st
import pandas as pd
import numpy as np
from explore_df import plotter
from scipy import stats
import plotly.express as px

st.title(":material/swap_horizontal_circle: Bivariate Analysis", anchor=False)
st.caption("Analyze relationships between pairs of variables")

df = st.session_state['df']

# Get numeric and categorical columns
numeric_cols = df.select_dtypes(include=[np.number]).columns
cat_cols = df.select_dtypes(exclude=[np.number]).columns

# Add Correlation Overview section
if len(numeric_cols) > 1:  # Only show if we have at least 2 numeric columns
    with st.container(border=True):
        st.subheader(":material/conversion_path: Correlation Overview", anchor=False, divider="grey")
        
        # Calculate correlation matrix for numeric columns
        corr_matrix = df[numeric_cols].corr()
        
        # Find highly correlated pairs (absolute correlation > 0.7)
        high_corr_pairs = []
        for i in range(len(numeric_cols)):
            for j in range(i + 1, len(numeric_cols)):
                corr = corr_matrix.iloc[i, j]
                if abs(corr) > 0.7:
                    high_corr_pairs.append({
                        'Variable 1': numeric_cols[i],
                        'Variable 2': numeric_cols[j],
                        'Correlation': corr
                    })
        
        if high_corr_pairs:
            # Create DataFrame of highly correlated pairs
            high_corr_df = pd.DataFrame(high_corr_pairs)
            high_corr_df['Correlation'] = high_corr_df['Correlation'].round(3)
            
            # Display summary
            st.markdown(":material/timeline: **Highly Correlated Variables** (|correlation| > 0.7)")
            st.dataframe(
                high_corr_df,
                column_config={
                    "Variable 1": st.column_config.TextColumn("Variable 1", width="medium"),
                    "Variable 2": st.column_config.TextColumn("Variable 2", width="medium"),
                    "Correlation": st.column_config.NumberColumn(
                        "Correlation",
                        format="%.3f",
                        width="small"
                    )
                },
                hide_index=True
            )
        else:
            st.info(":material/information: No highly correlated numeric variables found in the dataset (|correlation| > 0.7)")

# Variable Selection
with st.container(border=True):
    st.subheader(":material/view_column: Variable Selection", anchor=False, divider="grey")
    
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            x_col = st.selectbox(
                ":material/arrow_right: First Variable",
                options=df.columns,
                key="x_axis"
            )
    with col2:
        with st.container(border=True):
            y_col = st.selectbox(
                ":material/arrow_left: Second Variable",
                options=df.columns,
                key="y_axis"
            )

if x_col and y_col:
    # Relationship Analysis
    with st.container(border=True):
        st.subheader(":material/scatter_plot: Relationship Analysis", anchor=False, divider="grey")
        
        # Check if same variable is selected
        if x_col == y_col:
            st.warning(":material/alert: Please select different variables for meaningful bivariate analysis.")
            st.stop()
        
        # Both numeric
        if pd.api.types.is_numeric_dtype(df[x_col]) and pd.api.types.is_numeric_dtype(df[y_col]):
            # Drop rows with missing values in either column
            valid_data = df[[x_col, y_col]].dropna()
            
            # Create columns for stats and visualization
            col1, col2 = st.columns([1.2, 2])
            
            with col1:
                with st.container(border=True):
                    st.markdown("**Statistical Summary**")
                    
                    # Only calculate statistics if we have valid data
                    if len(valid_data) > 1:  # Need at least 2 points for analysis
                        try:
                            # Convert to numpy arrays for calculations
                            x_vals = valid_data[x_col].values
                            y_vals = valid_data[y_col].values
                            
                            # Calculate correlation
                            correlation = np.corrcoef(x_vals, y_vals)[0, 1]
                            
                            # Calculate regression
                            slope, intercept, r_value, p_value, std_err = stats.linregress(x_vals, y_vals)
                            
                            st.write(f"**Correlation:** {correlation:.3f}")
                            st.write(f"**R-squared:** {r_value**2:.3f}")
                            # Format p-value to be more readable
                            if p_value < 0.001:
                                st.write("**P-value:** < 0.001")
                            else:
                                st.write(f"**P-value:** {p_value:.3f}")

                            # Add relationship strength indicator
                            abs_corr = abs(correlation)
                            if p_value < 0.05:
                                st.success(":material/check_circle: Relationship is statistically significant")
                                
                                if abs_corr < 0.3:
                                    st.warning(":material/error: However, the relationship is very weak")
                                elif abs_corr < 0.5:
                                    st.info(":material/info: The relationship is weak")
                                elif abs_corr < 0.7:
                                    st.info(":material/info: The relationship is moderate")
                                elif abs_corr < 0.9:
                                    st.success(":material/check_circle: The relationship is strong")
                                else:
                                    st.success(":material/check_circle: The relationship is very strong")
                            else:
                                st.warning(":material/error: No statistically significant relationship found")

                        except Exception as e:
                            st.error(":material/error: Error calculating statistics. Please check your data.")
                            st.write(f"Error details: {str(e)}")
                    else:
                        st.warning(":material/error: Insufficient data for statistical analysis")
            
            with col2:
                try:
                    fig = plotter.create_scatter_plot(df, x_col, y_col)
                    fig.update_layout(
                        title=dict(
                            text=f'Scatter Plot: {x_col} vs {y_col}',
                            x=0.45,
                            y=0.95
                        ),
                        margin=dict(t=50, l=50, r=20, b=50),
                        showlegend=False,
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        modebar=dict(
                            remove=['zoom', 'pan', 'select', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d']
                        )
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(":material/alert: Error creating scatter plot. Please check your data.")
        
        # One numeric, one categorical
        elif (pd.api.types.is_numeric_dtype(df[x_col]) and not pd.api.types.is_numeric_dtype(df[y_col])) or \
             (pd.api.types.is_numeric_dtype(df[y_col]) and not pd.api.types.is_numeric_dtype(df[x_col])):
            
            # Ensure numeric is y and categorical is x for consistent visualization
            if pd.api.types.is_numeric_dtype(df[x_col]):
                x_col, y_col = y_col, x_col
            
            # Calculate summary statistics
            summary_stats = df.groupby(x_col)[y_col].agg(['mean', 'median', 'std', 'count'])
            summary_stats = summary_stats.round(2)
            
            col1, col2 = st.columns([1.2, 1.8])
            
            with col1:
                with st.container(border=True):
                    st.markdown(f"**Statistics of {y_col} by {x_col}**")
                    st.dataframe(summary_stats, height=200)
            
            with col2:
                fig = plotter.create_box_plot(df, x_col, y_col)
                fig.update_layout(
                    title=dict(
                        text=f'Distribution of {y_col} by {x_col}',
                        x=0.45,
                        y=0.95
                    ),
                    margin=dict(t=50, l=50, r=20, b=50),
                    showlegend=False,
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    modebar=dict(
                        remove=['zoom', 'pan', 'select', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d']
                    )
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Both categorical
        else:
            # Create contingency table
            contingency = pd.crosstab(df[x_col], df[y_col])
            
            # Calculate chi-square test
            chi2, p_value, dof, expected = stats.chi2_contingency(contingency)
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                with st.container(border=True):
                    st.markdown(":material/chart_sankey: **Association Analysis**")
                    st.write(f":material/chart_bell_curve: **Chi-square:** {chi2:.2f}")
                    st.write(f":material/alpha_p: **P-value:** {p_value:.3e}")
                    st.write(f":material/counter: **Degrees of freedom:** {dof}")
                    
                    if p_value < 0.05:
                        st.success(":material/check_circle: *Association is statistically significant*")
            
            with col2:
                # Create heatmap of contingency table
                fig = px.imshow(
                    contingency,
                    labels=dict(x=y_col, y=x_col, color="Count"),
                    aspect="auto"
                )
                fig.update_layout(
                    title=dict(
                        text=f'Association between {x_col} and {y_col}',
                        x=0.45,
                        y=0.95
                    ),
                    margin=dict(t=50, l=50, r=20, b=50),
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    modebar=dict(
                        remove=['zoom', 'pan', 'select', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d']
                    )
                )
                st.plotly_chart(fig, use_container_width=True)

    # Add this at the bottom, after all analysis sections
    with st.expander(":material/info: What do these numbers in the statistical summary mean?"):
        st.markdown("""
        - **Correlation** ranges from -1 to 1:
            - 0.0 to 0.3: Very weak relationship
            - 0.3 to 0.5: Weak relationship
            - 0.5 to 0.7: Moderate relationship
            - 0.7 to 0.9: Strong relationship
            - 0.9 to 1.0: Very strong relationship
            - Negative values indicate inverse relationships
        
        - **R-squared** ranges from 0 to 1:
            - Shows how much variation in one variable is explained by the other
            - Higher values indicate better fit
            - Example: 0.65 means 65% of variation is explained
        
        - **P-value** indicates statistical significance:
            - < 0.05: Statistically significant
            - ≥ 0.05: Not statistically significant
        """)

