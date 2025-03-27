import streamlit as st
import pandas as pd

# Header section
st.title(":material/table_chart: Data View", anchor=False)
st.caption("The perfect way to interact with your data")
st.write("")

df = st.session_state['df']

# Add explanation of dataframe features
with st.expander("Dataframe Features", icon=":material/info:", expanded=True):
    st.markdown("""
    The interactive dataframe below provides powerful features for exploring your data:

    **Basic Interactions:**
    - :material/search: Search through data using the search icon or ⌘+F (Ctrl+F)
    - :material/download: Download data as CSV using the download icon
    - :material/content_copy: Copy cells to clipboard with ⌘+C (Ctrl+C)
    - :material/fullscreen: Toggle fullscreen view with the fullscreen icon

    **Column Management:**
    - :material/sort: Sort columns by clicking headers or using the menu
    - :material/drag_indicator: Resize columns by dragging header borders
    - :material/visibility_off: Hide columns using the column menu
    - :material/push_pin: Pin columns to the left by dragging or using the menu
    - :material/drag_indicator: Reorder columns by dragging headers

    **Data Formatting:**
    - :material/format_list_numbered: Format numbers, dates, and times using the Format menu
    - :material/auto_fix_high: Autosize columns for better visibility
    - :material/open_with: Resize the entire dataframe using the bottom-right corner
    """)

# Calculate a reasonable height for the dataframe
def calculate_dataframe_height(df):
    # Base height for header and minimal content
    base_height = 100
    
    # Add height based on number of rows (capped at 20 rows)
    row_height = 35  # Height per row
    rows_to_show = min(20, len(df))  # Show at most 20 rows
    row_based_height = rows_to_show * row_height
    
    # Add height based on number of columns (capped at 10 columns)
    col_height = 40  # Height per column
    cols_to_show = min(10, len(df.columns))  # Show at most 10 columns
    col_based_height = cols_to_show * col_height
    
    # Take the maximum of row-based and column-based heights
    calculated_height = max(base_height, row_based_height, col_based_height)
    
    # Cap the maximum height at 600px to prevent the page from becoming too long
    return min(600, calculated_height)

# Style the dataframe to highlight empty cells
def highlight_empty_cells(df):
    return df.style.applymap(
        lambda x: 'background-color: #ffebee' if pd.isna(x) else ''
    )

# Add the dataframe with dynamic height and empty cell highlighting
st.write("")
st.dataframe(
    highlight_empty_cells(df), 
    use_container_width=True,
    height=calculate_dataframe_height(df),
    hide_index=True
) 