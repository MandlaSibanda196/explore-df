import streamlit as st
import pandas as pd
import numpy as np

def render_accuracy_analysis(df, suggestions):
    """Render the accuracy analysis section."""
    st.subheader("Accuracy Analysis", anchor=False)
    st.caption("Analyze and fix data accuracy issues")

    with st.expander("What do we check for accuracy?", icon=":material/info:"):
        st.info(
            "• Domain-specific value ranges:\n\n"
            "• Age values > 150 years\n\n"
            "• Negative values in positive-only fields\n\n"
            "• Percentages > 100%\n\n"
            "• Future dates in birth/creation fields\n\n"
        )
    
    if suggestions:
        st.write("The following columns have accuracy issues:")
        
        for column, analysis in suggestions.items():
            with st.expander(f":material/analytics: {column}"):
                for issue in analysis['issues']:
                    st.markdown(f"**Issue Type:** `{issue['type']}`")
                    st.markdown(f"**Description:** {issue['description']}")
                    
                    # Show sample values
                    st.markdown("**Sample problematic values:**")
                    st.write(issue['sample'])
                    
                    if 'bounds' in issue:
                        st.markdown(f"**Valid range:** [{issue['bounds']['lower']:.2f}, {issue['bounds']['upper']:.2f}]")
                
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
        st.success(":material/check_circle: No accuracy issues found in your dataset!") 