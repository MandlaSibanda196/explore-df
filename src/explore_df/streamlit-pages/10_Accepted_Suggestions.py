import streamlit as st

# Header section
st.title(":material/code: Accepted Suggestions", anchor=False)
st.caption("A record of all the suggestions you've accepted and charts you've created")

# Initialize the accepted suggestions in session state if it doesn't exist
if 'accepted_suggestions' not in st.session_state:
    st.session_state['accepted_suggestions'] = []

if st.session_state['accepted_suggestions']:
    # Complete Code Block section
    with st.container(border=True):
        st.subheader("Complete Code Block", anchor=False)
        st.caption("All accepted suggestions combined into a single code block")
        
        # Create a complete code block with all accepted suggestions
        complete_code = "# Data type conversions\n"
        complete_code += "import pandas as pd\n\n"
        complete_code += "# Apply the following conversions to your dataframe:\n"
        for suggestion in st.session_state['accepted_suggestions']:
            complete_code += suggestion + "\n"
        
        # Display the complete code block with a copy button
        st.code(complete_code, language='python')
    
    # Individual Suggestions section
    with st.container(border=True):
        st.subheader("Individual Suggestions", anchor=False)
        st.caption("View and manage individual suggestions")
        
        for i, suggestion in enumerate(st.session_state['accepted_suggestions'], 1):
            with st.expander(f"Suggestion {i}", icon=":material/code:"):
                st.code(suggestion, language='python')
                
                # Add a remove button for each suggestion
                if st.button("Remove this suggestion", key=f"remove_{i}", icon=":material/delete:"):
                    st.session_state['accepted_suggestions'].remove(suggestion)
                    st.rerun()
else:
    with st.container(border=True):
        st.info("""
        You haven't accepted any suggestions or created any charts yet. 
        Go create some charts and suggestions will appear here!
        """, icon=":material/info:") 