import streamlit as st
import pandas as pd
import numpy as np

def render_uniqueness_analysis(df, suggestions):
    """Render the uniqueness analysis section."""
    st.subheader("Uniqueness Analysis", anchor=False)
    st.caption("Analyze and fix data uniqueness issues")

    with st.expander("What do we check for uniqueness?", icon=":material/info:"):
        st.info(
            "• Exact duplicate rows\n\n"
            "• Duplicate values in ID/key columns\n\n"
            "• Near-duplicate records based on:\n\n"
            "• Text similarity\n\n"
            "• Multiple column combinations\n\n"
            "• Fuzzy matching\n\n"
            "• Low cardinality columns\n\n"
            "• Redundant information across columns\n\n"
            "• Primary key violations\n\n"
            "• Composite key uniqueness"
        )
    
    if suggestions:
        with st.container(border=True):
            st.write("Found the following uniqueness issues:")
            
            for key, analysis in suggestions.items():
                with st.expander(f":material/fingerprint: {key}"):
                    st.markdown(f"**Description:** {analysis['description']}")
                    
                    # Show sample values
                    st.markdown("**Sample problematic values:**")
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
                        key=f"pills_unique_{key}_{len(strategy_map)}"
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
                                st.markdown(f"Original shape: {df.shape}")
                                st.markdown(f"After fixing: {df_preview.shape}")
                                
                                if '_' in key and 'duplicates' in key:
                                    # For column pair duplicates
                                    cols = key.replace('_duplicates', '').split('_')
                                    preview_df = pd.DataFrame({
                                        'Original': df[cols].head().to_dict('records'),
                                        'After Fixing': df_preview[cols].head().to_dict('records')
                                    })
                                else:
                                    # For single column or exact duplicates
                                    preview_df = pd.DataFrame({
                                        'Original': str(df.shape),
                                        'After Fixing': str(df_preview.shape)
                                    }, index=['Row count'])
                                
                                st.dataframe(preview_df, use_container_width=True)
                                
                            except Exception as e:
                                st.error(f"Preview failed: {str(e)}")
                            
                            # Apply button
                            if st.button("Apply Strategy", key=f"apply_{key}_{strategy['name']}", use_container_width=True):
                                try:
                                    # Apply the strategy to the actual dataframe
                                    exec(strategy['code'], {'df': df, 'pd': pd, 'np': np})
                                    
                                    # Update the dataframe in session state
                                    st.session_state['df'] = df
                                    
                                    # Add the code to accepted suggestions
                                    if strategy['code'] not in st.session_state['accepted_suggestions']:
                                        st.session_state['accepted_suggestions'].append(strategy['code'])
                                        
                                    # Add a comment to identify the outlier fix
                                    comment = f"# Outlier fix for {key}: {strategy['name']}"
                                    if comment not in st.session_state['accepted_suggestions']:
                                        st.session_state['accepted_suggestions'].append(comment)
                                    
                                    st.success(f"Successfully applied {strategy['name']}!")
                                    
                                except Exception as e:
                                    st.error(f"Failed to apply strategy: {str(e)}")
    else:
        st.success(":material/check_circle: No uniqueness issues found in your dataset!") 