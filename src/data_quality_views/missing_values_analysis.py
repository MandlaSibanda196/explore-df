import streamlit as st
import pandas as pd
import numpy as np

def render_missing_values_analysis(df, suggestions):
    """Render the missing values analysis section."""
    st.subheader("Missing Values Analysis", anchor=False)
    st.caption("Suggestions for handling missing values in your dataset")

    with st.expander("What do we check for missing values?", icon=":material/info:"):
        st.info(
            "• Null/NaN values in each column\n\n"
            "• Missing value patterns and correlations\n\n"
            "• Appropriate imputation strategies based on:\n\n"
            "• Column type (numeric, categorical, datetime)\n\n"
            "• Missing value percentage\n\n"
            "• Distribution of non-missing values\n\n"
            "• Presence of time series patterns\n\n"
            "• Impact of different imputation methods\n\n"
            "• Hidden missing values (empty strings, special values)\n\n"
            "• Missing value sequences and gaps"
        )

    if suggestions:
        st.write("The following columns have missing values that could be handled:")
        
        for column, analysis in suggestions.items():
            with st.expander(f":material/help_outline: {column} ({analysis['missing_percentage']:.1f}% missing)"):
                # Show missing values statistics in three columns
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write("**Missing Values**")
                    st.write(f"{analysis['missing_count']} ({analysis['missing_percentage']:.1f}%)", color="red")
                with col2:
                    st.write("**Column Type**")
                    st.write(analysis['column_type'], color="gray")
                with col3:
                    st.write("**Sample Values**")
                    samples = analysis['non_null_sample'][:3]  # Get up to 3 samples
                    sample_text = ", ".join(str(x) for x in samples) if samples else "No samples"
                    st.write(sample_text, color="gray")
                
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
                        
                        try:
                            # Create a copy of the dataframe and apply the strategy
                            df_preview = df.copy()
                            exec(strategy['code'], {'df': df_preview, 'pd': pd, 'np': np})
                            
                            # Create two columns for preview and apply buttons
                            preview_col, apply_col = st.columns(2)
                            
                            # Show preview button and results in a popover
                            with preview_col:
                                with st.popover("Preview Results", icon=":material/preview:", use_container_width=True):
                                    preview_df = pd.DataFrame({
                                        'Original': df[column].head(),
                                        'After Fixing': df_preview[column].head()
                                    })
                                    st.dataframe(preview_df, use_container_width=True)
                            
                            # Apply button
                            with apply_col:
                                if st.button(":material/check_circle: Apply Strategy", key=f"apply_{column}_{strategy['name']}", use_container_width=True):
                                    try:
                                        # Apply the strategy to the actual dataframe
                                        exec(strategy['code'], {'df': df, 'pd': pd, 'np': np})
                                        
                                        # Update the dataframe in session state
                                        st.session_state['df'] = df
                                        
                                        # Add the code to accepted suggestions
                                        if strategy['code'] not in st.session_state['accepted_suggestions']:
                                            st.session_state['accepted_suggestions'].append(strategy['code'])
                                        
                                        st.success(f"Successfully applied {strategy['name']} to {column}!")
                                        
                                    except Exception as e:
                                        st.error(f"Failed to apply strategy: {str(e)}")
                        except Exception as e:
                            st.error(f"Preview failed: {str(e)}")
    else:
        st.success(":material/check_circle: No missing values found in your dataset!") 