import streamlit as st
import pandas as pd
import numpy as np
import re

def render_validity_analysis(df, suggestions):
    """Render the validity analysis section."""
    st.subheader("Validity Analysis", anchor=False)
    st.caption("Analyze and fix data validity issues")

    with st.expander("What do we check for validity?", icon=":material/info:"):
        st.info(
            "• Email address format validity\n\n"
            "• Phone number format validity\n\n"
            "• URL format validity\n\n"
            "• ZIP/Postal code format validity\n\n"
            "• Date format validity\n\n"
            "• Range constraints:\n\n"
            "• Percentages (0-100)\n\n"
            "• Probabilities (0-1)\n\n"
            "• Age ranges\n\n"
            "• Currency values\n\n"
            "• Format-specific patterns\n\n"
            "• Domain-specific rules\n\n"
            "• Logical constraints"
        )
    
    if suggestions:
        with st.container(border=True):
            st.write("The following columns have validity issues:")
            
            for column, analysis in suggestions.items():
                with st.expander(f":material/verified: {column}"):
                    st.markdown(f"**Issue Type:** `{analysis['type']}`")
                    st.markdown(f"**Description:** {analysis['description']}")
                    
                    # Show sample values
                    st.markdown("**Sample invalid values:**")
                    st.write(analysis['sample'])
                    
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
                                exec(strategy['code'], {'df': df_preview, 'pd': pd, 'np': np, 're': re})
                                
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
                                    exec(strategy['code'], {'df': df, 'pd': pd, 'np': np, 're': re})
                                    
                                    # Update the dataframe in session state
                                    st.session_state['df'] = df
                                    
                                    # Add the code to accepted suggestions
                                    if strategy['code'] not in st.session_state['accepted_suggestions']:
                                        st.session_state['accepted_suggestions'].append(strategy['code'])
                                    
                                    st.success(f"Successfully applied {strategy['name']} to {column}!")
                                    
                                except Exception as e:
                                    st.error(f"Failed to apply strategy: {str(e)}")
    else:
        st.success(":material/check_circle: No validity issues found in your dataset!") 