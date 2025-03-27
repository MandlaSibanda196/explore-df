import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

def render_outlier_analysis(df, suggestions):
    """Render the outlier analysis section."""
    st.subheader("Extreme Outlier Analysis", anchor=False)
    st.caption("Analyze and fix extreme outliers in your dataset")

    with st.expander("What do we check for outliers?", icon=":material/info:"):
        st.info(
            "• IQR Method (3× IQR from quartiles)\n\n"
            "• Z-score Method (>3 standard deviations)\n\n"
            "• Modified Z-score (robust against outliers)\n\n"
            "• For each affected column, we provide:\n\n"
            "• Multiple detection methods to confirm outliers\n\n"
            "• Visual distribution analysis\n\n"
            "• Statistical summaries\n\n"
            "• Various handling strategies:\n\n"
            "• Capping at boundaries\n\n"
            "• Replacing with NaN\n\n"
            "• Winsorization\n\n"
            "• Log transformation (for positive values)"
        )
    
    if suggestions:
        with st.container(border=True):
            st.write("The following columns have extreme outliers:")
            
            for column, analysis in suggestions.items():
                with st.expander(f":material/analytics: {column} ({analysis['outlier_percentage']:.1f}% outliers)"):
                    # Show statistics
                    st.markdown("**Statistical Summary:**")
                    stats_df = pd.DataFrame({
                        'Metric': ['Mean', 'Median', 'Std Dev', 'IQR', 'Outlier Count'],
                        'Value': [
                            f"{analysis['stats']['mean']:.2f}",
                            f"{analysis['stats']['median']:.2f}",
                            f"{analysis['stats']['std']:.2f}",
                            f"{analysis['stats']['iqr']:.2f}",
                            f"{analysis['stats']['outlier_count']}"
                        ]
                    })
                    st.dataframe(stats_df, hide_index=True)
                    
                    # Show distribution plot
                    fig = px.box(df, y=column, title=f"Distribution of {column}")
                    fig.update_layout(showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Show issues from different methods
                    st.markdown("**Detected Issues:**")
                    for issue in analysis['issues']:
                        st.markdown(f"• **{issue['type']}:** {issue['description']}")
                        if 'bounds' in issue:
                            st.caption(f"Valid range: [{issue['bounds']['lower']:.2f}, {issue['bounds']['upper']:.2f}]")
                        st.caption("Sample outliers: " + str(issue['sample']))
                    
                    # Show available strategies
                    st.markdown("**Available strategies:**")
                    
                    # Create a dictionary mapping strategy indices to their names
                    strategy_map = {
                        i: strategy['name'].title() 
                        for i, strategy in enumerate(analysis['strategies'])
                    }

                    # Use pills to select the strategy with a unique key
                    selected_strategy_idx = st.pills(
                        "Select strategy",
                        options=strategy_map.keys(),
                        format_func=lambda x: strategy_map[x],
                        selection_mode="single",
                        key=f"pills_{column}_{len(strategy_map)}"
                    )

                    # If a strategy is selected, show its details
                    if selected_strategy_idx is not None:
                        strategy = analysis['strategies'][selected_strategy_idx]
                        with st.container(border=True):
                            st.markdown(strategy['description'])
                            st.code(strategy['code'])
                            
                            # Preview section
                            st.markdown("**Preview Results**")
                            try:
                                # Create a copy of the dataframe and apply the strategy
                                df_preview = df.copy()
                                exec(strategy['code'], {'df': df_preview, 'pd': pd, 'np': np})
                                
                                # Show preview of the results
                                st.markdown("**Preview Results**")
                                
                                # Show statistics comparison
                                compare_df = pd.DataFrame({
                                    'Metric': ['Mean', 'Std Dev', 'Min', 'Max'],
                                    'Original': [
                                        f"{df[column].mean():.2f}",
                                        f"{df[column].std():.2f}",
                                        f"{df[column].min():.2f}",
                                        f"{df[column].max():.2f}"
                                    ],
                                    'After Fix': [
                                        f"{df_preview[column].mean():.2f}",
                                        f"{df_preview[column].std():.2f}",
                                        f"{df_preview[column].min():.2f}",
                                        f"{df_preview[column].max():.2f}"
                                    ]
                                })
                                st.dataframe(compare_df, hide_index=True)
                                
                                # Show small distribution plot
                                fig = px.box(
                                    pd.DataFrame({
                                        'Original': df[column],
                                        'After Fix': df_preview[column]
                                    }).melt(),
                                    y='value',
                                    x='variable',
                                    title="Distribution Comparison"
                                )
                                fig.update_layout(showlegend=False, height=200)
                                st.plotly_chart(fig, use_container_width=True)
                                
                            except Exception as e:
                                st.error(f"Preview failed: {str(e)}")
                            
                            # Apply button
                            if st.button("Apply Strategy", key=f"apply_{column}_{strategy['name']}", use_container_width=True):
                                try:
                                    # Apply the strategy to the actual dataframe
                                    exec(strategy['code'], {'df': df, 'pd': pd, 'np': np})
                                    
                                    # Update the dataframe in session state
                                    st.session_state['df'] = df
                                    
                                    # Add the code to accepted suggestions
                                    if strategy['code'] not in st.session_state['accepted_suggestions']:
                                        st.session_state['accepted_suggestions'].append(strategy['code'])
                                        
                                        # Add a comment to identify the outlier fix
                                        comment = f"# Outlier fix for {column}: {strategy['name']}"
                                        if comment not in st.session_state['accepted_suggestions']:
                                            st.session_state['accepted_suggestions'].append(comment)
                                    
                                    st.success(f"Successfully applied {strategy['name']} to {column}!")
                                    
                                except Exception as e:
                                    st.error(f"Failed to apply strategy: {str(e)}")
    else:
        st.success(":material/check_circle: No extreme outliers found in your dataset!") 