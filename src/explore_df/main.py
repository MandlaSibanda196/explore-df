import streamlit as st
import pandas as pd
from pathlib import Path
import numpy as np
import sys
sys.path.append(str(Path(__file__).parent / "src"))

def load_data():
    """Load data from the temporary pickle file."""
    temp_path = Path(__file__).parent / "temp" / "temp_df.pkl"
    return pd.read_pickle(temp_path)

def create_sample_data():
    """Create a sample DataFrame for development."""
    # Create sample data
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    
    df = pd.DataFrame({
        # Numeric columns
        'sales': np.random.normal(1000, 200, len(dates)),
        'temperature': np.random.uniform(15, 35, len(dates)),
        'units': np.random.randint(50, 150, len(dates)),
        'price': np.random.uniform(10, 100, len(dates)).round(2),
        
        # Categorical columns
        'category': np.random.choice(['A', 'B', 'C', 'D'], len(dates)),
        'status': np.random.choice(['Active', 'Pending', 'Completed'], len(dates)),
        'region': np.random.choice(['North', 'South', 'East', 'West'], len(dates)),
        
        # DateTime column
        'date': dates,
        
        # Text column
        'description': np.random.choice([
            'Regular order', 'Express delivery', 'Special handling',
            'Bulk order', 'Priority shipping'
        ], len(dates)),
        
        # Boolean column
        'is_weekend': dates.weekday >= 5,
    })
    
    # Add some missing values
    df.loc[np.random.choice(df.index, 50), 'sales'] = np.nan
    df.loc[np.random.choice(df.index, 30), 'temperature'] = np.nan
    df.loc[np.random.choice(df.index, 20), 'category'] = np.nan
    
    # Add some correlations
    df['profit'] = df['sales'] * 0.3 + np.random.normal(0, 50, len(dates))
    df['customer_satisfaction'] = (df['temperature'] * -0.2 + 
                                 np.random.normal(8, 1, len(dates))).clip(1, 10)
    
    return df


# Get the absolute path to the images directory
current_file = Path(__file__)
project_root = current_file.parent.parent 
image_path = project_root / "images" / "explore-df-logo.png"

# Set page config
st.set_page_config(
    page_title="Explore DF",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state with data from pickle file if available, otherwise use sample data
if 'df' not in st.session_state:
    try:
        st.session_state['df'] = load_data()
    except (FileNotFoundError, pd.errors.EmptyDataError, Exception) as e:
        st.session_state['df'] = create_sample_data()

# Define the pages
pages = {
    "Home": [
        st.Page("streamlit-pages/_Home.py", title="About", icon=":material/home:"),
        st.Page("streamlit-pages/8_Data_View.py", title="Data View", icon=":material/table_chart:"),
        st.Page("streamlit-pages/10_Accepted_Suggestions.py", title="Accepted Suggestions", icon=":material/code:"),
    ],
    "Processing": [
        st.Page("streamlit-pages/0_Dataset_Overview_and_Insights.py", title="Overview & Insights", icon=":material/insights:"),
        st.Page("streamlit-pages/6_Data_Quality.py", title="Data Quality Report", icon=":material/checklist:"),
        st.Page("streamlit-pages/7_Charts.py", title="Create Charts", icon=":material/bar_chart:"),
    ],
    "Basic Analysis": [
        st.Page("streamlit-pages/1_Univariate_Analysis.py", title="Univariate Analysis", icon=":material/analytics:"),
        st.Page("streamlit-pages/2_Bivariate_Analysis.py", title="Bivariate Analysis", icon=":material/swap_horizontal_circle:"),
        st.Page("streamlit-pages/3_Time_Series.py", title="Time Series Analysis", icon=":material/schedule:"),
    ],
    "Advanced Analysis": [
        st.Page("streamlit-pages/4_Categorical_Analysis.py", title="Categorical Analysis", icon=":material/category:"),
        st.Page("streamlit-pages/8_Text_Analysis.py", title="Text Analysis", icon=":material/description:"),
    ]
}

# Set up navigation and run the current page
pg = st.navigation(pages, position="sidebar")
pg.run()
