import streamlit as st
import pandas as pd

def render_data_type_analysis(df, suggestions):
    """Render the data type analysis section."""
    st.subheader("Data Type Analysis", anchor=False)
    st.caption("Suggestions for optimizing column data types")

    with st.expander("What do we check for data types?", icon=":material/info:"):
        st.info(
            "• Numeric columns with string formatting (e.g., currency symbols, thousands separators)\n\n"
            "• Date/time strings that should be datetime objects\n\n" 
            "• Boolean values stored as strings ('yes'/'no', 'true'/'false', '1'/'0')\n\n"
            "• Categorical columns with low cardinality\n\n"
            "• Mixed data types in the same column\n\n"
            "• Memory-inefficient data types (e.g., float64 when float32 would suffice)\n\n"
            "• Object columns that could be more specific types"
        )

    if suggestions:
        with st.container(border=True):
            st.write("The following columns might benefit from data type conversion:")
            
            for column, analysis in suggestions.items():
                with st.expander(f":material/database: {column}"):
                    current_type = analysis['current_type']
                    suggested_type = analysis['suggested_type']
                    confidence = analysis['confidence']
                    reasons = analysis['reason']
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Current type:** `{current_type}`")
                    with col2:
                        st.markdown(f"**Suggested type:** `{suggested_type}`")
                    
                    st.markdown(f"**Confidence:** {'🟢' if confidence == 'high' else '🟡' if confidence == 'medium' else '🔴'} {confidence.title()}")
                    
                    if reasons:
                        st.markdown("**Reasons:**")
                        for reason in reasons:
                            st.markdown(f"- {reason}")
                    
                    # Show sample values
                    st.markdown("**Sample values:**")
                    sample_df = pd.DataFrame({
                        'Original': df[column].head(3),
                        'After Conversion': pd.Series(dtype=suggested_type)
                    })
                    
                    # Generate the conversion code
                    if suggested_type == 'datetime64[ns]':
                        conversion_code = f"df['{column}'] = pd.to_datetime(df['{column}'])"
                    elif suggested_type in ['int64', 'float64'] and any(any(symbol in str(x) for symbol in ['$', '€', '£', '¥', '₹']) for x in df[column].head().dropna()):
                        conversion_code = f"# Remove currency symbols and thousands separators\ndf['{column}'] = df['{column}'].apply(lambda x: str(x).replace('$', '').replace(',', '')).astype('{suggested_type}')"
                    else:
                        conversion_code = f"df['{column}'] = df['{column}'].astype('{suggested_type}')"
                    
                    try:
                        if suggested_type == 'datetime64[ns]':
                            sample_df['After Conversion'] = pd.to_datetime(df[column].head(3))
                        elif suggested_type == 'boolean':
                            sample_df['After Conversion'] = df[column].head(3).map({'true': True, 'false': False, '1': True, '0': False, 'yes': True, 'no': False, 'y': True, 'n': False}).astype('boolean')
                        elif suggested_type in ['int64', 'float64']:
                            # Handle currency values by removing symbols and commas
                            values = df[column].head(3).apply(lambda x: str(x).replace('$', '').replace(',', ''))
                            sample_df['After Conversion'] = values.astype(suggested_type)
                        elif suggested_type == 'category':
                            sample_df['After Conversion'] = df[column].head(3).astype('category')
                    except Exception as e:
                        sample_df['After Conversion'] = ['Conversion failed'] * 3
                    
                    st.dataframe(sample_df)
                    
                    # Add conversion code snippet
                    st.markdown("**Code to apply this change:**")
                    st.code(conversion_code)
                    
                    # Add accept button
                    if st.button("Accept Suggestion", key=f"accept_{column}", use_container_width=True):
                        try:
                            # Apply the conversion to the actual dataframe
                            if suggested_type == 'datetime64[ns]':
                                df[column] = pd.to_datetime(df[column])
                            elif suggested_type == 'boolean':
                                df[column] = df[column].map({'true': True, 'false': False, '1': True, '0': False, 'yes': True, 'no': False, 'y': True, 'n': False}).astype('boolean')
                            elif suggested_type in ['int64', 'float64']:
                                if any(any(symbol in str(x) for symbol in ['$', '€', '£', '¥', '₹']) for x in df[column].dropna()):
                                    df[column] = df[column].apply(lambda x: str(x).replace('$', '').replace(',', '')).astype(suggested_type)
                                else:
                                    df[column] = df[column].astype(suggested_type)
                            elif suggested_type == 'category':
                                df[column] = df[column].astype('category')
                            
                            # Update the dataframe in session state
                            st.session_state['df'] = df
                            
                            # Add the conversion code to accepted suggestions
                            if conversion_code not in st.session_state['accepted_suggestions']:
                                st.session_state['accepted_suggestions'].append(conversion_code)
                            
                            st.success(f"Successfully converted {column} to {suggested_type}!")
                            
                        except Exception as e:
                            st.error(f"Failed to convert {column}: {str(e)}")
    else:
        st.success(":material/check_circle: All column data types appear to be optimally set!") 