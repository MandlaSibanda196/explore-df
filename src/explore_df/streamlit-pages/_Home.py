import streamlit as st

# Header section
st.title(":material/speed: Explore-DF", anchor=False)
st.caption("Interactive Exploratory Data Analysis Tool")

# Brief introduction
with st.container(border=True):
    st.info("""
    These modules help you understand your data through interactive visualizations and analysis. 
    The goal is to give you a quick overview of your data and help you identify the most important features and relationships and perhaps probe questions you had not thought of.

    Happy exploring!        
    """)

st.divider()

with st.container(border=True):
    st.subheader("Core Analysis", anchor=False)
    st.caption("Essential analysis tools for your dataset")
    
    # Dataset Overview section
    st.page_link(
        "streamlit-pages/0_Dataset_Overview_and_Insights.py",
        label=" **Dataset Overview & Insights:** Basic Statistics, Data Types, and Quick Insights",
        icon=":material/insights:",
    )
    st.page_link(
        "streamlit-pages/1_Univariate_Analysis.py",
        label=" **Univariate Analysis:** Single Variable Distributions and Statistics",
        icon=":material/analytics:",
    )
    st.page_link(
        "streamlit-pages/2_Bivariate_Analysis.py",
        label="**Bivariate Analysis:** Relationships between Pairs of Variables",
        icon=":material/swap_horizontal_circle:",
    )
    st.page_link(
        "streamlit-pages/6_Data_Quality.py",
        label=" **Data Quality Report:** Missing Values, Duplicates, and Data Consistency",
        icon=":material/checklist:",
    )
    st.page_link(
        "streamlit-pages/7_Charts.py",
        label="**Charts:** Visualizations for your dataset",
        icon=":material/bar_chart:",
    )

with st.container(border=True):
    st.subheader("Advanced Analysis", anchor=False)
    st.caption("In-depth analytical tools for deeper insights")
    
    st.page_link(
        "streamlit-pages/3_Time_Series.py",
        label="**Time Series Analysis:** Temporal Patterns, Trends, and Seasonality",
        icon=":material/schedule:",
    )
    st.page_link(
        "streamlit-pages/4_Categorical_Analysis.py",
        label="**Categorical Analysis:** Frequency Analysis and Categorical Insights",
        icon=":material/category:",
    )

with st.container(border=True):
    st.subheader("Accepted Suggestions", anchor=False)
    st.caption("As you explore your data, you can accept suggestions and add the code will will be added to this page.")
    
    st.page_link(
        "streamlit-pages/10_Accepted_Suggestions.py",
        label="**Accepted Suggestions:** Complete Code Block and Individual Suggestions",
        icon=":material/code:",
    )

st.write("")

st.warning(":material/lightbulb: Tip: Click on any module to navigate to the analysis page.") 

# Footer
st.divider()