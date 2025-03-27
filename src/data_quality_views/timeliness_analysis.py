import streamlit as st
import pandas as pd
import numpy as np

def render_timeliness_analysis(df, suggestions):
    """Render the timeliness analysis section."""
    st.subheader("Timeliness Analysis", anchor=False)
    st.caption("Analyze and fix data timeliness issues")

    with st.expander("What do we check for timeliness?", icon=":material/info:"):
        st.info(
            "• Future dates in historical fields\n\n"
            "• Very old dates (before 1900)\n\n"
            "• Large gaps in time series data\n\n"
            "• Inconsistent time intervals\n\n"
            "• Temporal outliers\n\n"
            "• Missing timestamps\n\n"
            "• Date/time precision issues\n\n"
            "• Timezone inconsistencies\n\n"
            "• Seasonal patterns and anomalies"
        )
    
    if suggestions:
        with st.container(border=True):
            st.write("The following datetime columns have timeliness issues:")
            
            for column, analysis in suggestions.items():
                with st.expander(f":material/schedule: {column}"):
                    for issue in analysis['issues']:
                        st.markdown(f"**Issue Type:** `{issue['type']}`")
                        st.markdown(f"**Description:** {issue['description']}")
                        
                        # Show sample values
                        st.markdown("**Sample problematic values:**")
                        st.write(issue['sample'])
                        
                        if 'median_interval' in issue:
                            st.markdown(f"**Median interval:** {issue['median_interval']}")
                    
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
                                preview_df = pd.DataFrame({
                                    'Original': df[column].head(),
                                    'After Fixing': df_preview[column].head()
                                })
                                st.dataframe(preview_df, use_container_width=True)
                                
                                # Show statistics about changes
                                st.divider()
                                st.caption("**Change Statistics:**")
                                total_changes = (df[column] != df_preview[column]).sum()
                                st.caption(f"• Values changed: {total_changes:,} ({(total_changes/len(df)*100):.1f}%)")
                                
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
                                    
                                    st.success(f"Successfully applied {strategy['name']} to {column}!")
                                    
                                except Exception as e:
                                    st.error(f"Failed to apply strategy: {str(e)}")
    else:
        st.success(":material/check_circle: No timeliness issues found in your dataset!") 