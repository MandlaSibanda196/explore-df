import streamlit as st
import pandas as pd
import numpy as np
from explore_df import plotter
from collections import Counter

st.title(":material/description: Text Analysis", anchor=False)
st.caption("Analyze patterns and insights in text data")

df = st.session_state['df']
text_cols = df.select_dtypes(include=['object']).columns

if len(text_cols) == 0:
    st.warning(":material/alert: No text columns found in the dataset!")
    st.stop()

# Initialize analysis variable and text data
analysis = None
text_data = None
words = None

# Basic Text Analysis Section
st.subheader(" Basic Text Analysis", anchor=False, divider="grey")
st.caption(":material/info: Analyze basic statistics and patterns in text data.")

with st.container(border=True):
    text_col = st.selectbox(
        " Select Text Column",
        text_cols,
        help="Choose a text column to analyze",
        key="text_analysis_col"
    )

# Display results in a more organized way
try:
    # Prepare text data
    text_data = df[text_col].fillna('').astype(str)
    
    # Calculate length statistics
    length_stats = {
        "Mean Length": text_data.str.len().mean(),
        "Max Length": text_data.str.len().max(),
        "Min Length": text_data.str.len().min()
    }
    
    # Calculate pattern statistics
    pattern_stats = {
        "URLs": text_data.str.contains(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+').sum(),
        "Emails": text_data.str.contains(r'[\w\.-]+@[\w\.-]+').sum(),
        "Numbers": text_data.str.contains(r'\d+').sum()
    }
    
    # Calculate word statistics
    # Split text into words and filter out empty strings
    words = [word for word in " ".join(text_data).split() if word.strip()]
    
    if not words:
        st.warning(":material/alert_circle: No valid words found in the selected column.")
        st.stop()
        
    word_stats = {
        "Total Words": len(words),
        "Unique Words": len(set(words)),
        "Avg Words per Entry": len(words) / len(text_data),
        "Top Words": Counter(words).most_common(10),
        "Word Lengths": Counter([len(word) for word in words])
    }
    
    # Combine all statistics
    analysis = {
        "Length Stats": length_stats,
        "Pattern Analysis": pattern_stats,
        "Word Stats": word_stats
    }
    
    # Display statistics in columns
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        with st.container(border=True):
            st.markdown(":material/straighten: **Length Statistics**")
            for stat, value in length_stats.items():
                st.metric(stat, f"{value:.0f}")
    
    with col2:
        with st.container(border=True):
            st.markdown(":material/manage_search: **Pattern Analysis**")
            for pattern, count in pattern_stats.items():
                icon = {
                    "URLs": ":material/link:",
                    "Emails": ":material/email:",
                    "Numbers": ":material/pin:"
                }[pattern]
                st.metric(f"{icon} {pattern}", f"{count:,}")
    
    with col3:
        with st.container(border=True):
            st.markdown(":material/analytics: **Word Statistics**")
            st.metric(":material/numbers: Total Words", f"{word_stats['Total Words']:,}")
            st.metric(":material/fingerprint: Unique Words", f"{word_stats['Unique Words']:,}")
            st.metric(":material/calculate: Average Words per Entry", f"{word_stats['Avg Words per Entry']:.0f}")

except Exception as e:
    st.error(":material/alert: Error analyzing text data")
    with st.expander(":material/help: Error Details"):
        st.caption(f":material/error: {str(e)}")
    st.stop()

# Word Analysis Section
with st.container(border=True):
    st.subheader("Word Analysis", anchor=False, divider="grey")
    st.caption(":material/info: Explore word frequencies and patterns in the text.")
    
    if analysis is not None and words:  # Only show if analysis exists and we have words
        col1, col2 = st.columns([3, 2])
        
        with col1:
            with st.container(border=True):
                st.markdown(":material/format_list_numbered: **Most Common Words**")
                try:
                    top_words = pd.DataFrame(
                        analysis["Word Stats"]["Top Words"],
                        columns=["Word", "Count"]
                    )
                    top_words["Percentage"] = (top_words["Count"] / analysis["Word Stats"]["Total Words"] * 100).round(1)
                    top_words["Percentage"] = top_words["Percentage"].astype(str) + '%'
                    st.dataframe(
                        top_words,
                        column_config={
                            "Word": st.column_config.TextColumn("Word", help="The word found in the text"),
                            "Count": st.column_config.NumberColumn("Count", help="Number of occurrences"),
                            "Percentage": st.column_config.TextColumn("Percentage", help="Percentage of total words")
                        },
                        hide_index=True,
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(":material/alert: Error analyzing word frequencies")
                    st.caption(f":material/error: {str(e)}")
        
        with col2:
            with st.container(border=True):
                st.markdown(":material/leaderboard: **Word Length Distribution**")
                try:
                    word_lengths = analysis["Word Stats"]["Word Lengths"]
                    if word_lengths:
                        fig = plotter.create_word_length_dist(word_lengths)
                        fig.update_layout(
                            height=300,
                            margin=dict(t=30, l=50, r=20, b=50),
                            plot_bgcolor='white',
                            paper_bgcolor='white'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.info(":material/info: Word length distribution not available")
    else:
        st.info(":material/hand_pointing_up: Please select a text column above to view word analysis")

# Word Cloud Section
with st.container(border=True):
    st.subheader(":material/cloud: Word Cloud", anchor=False, divider="grey")
    st.caption(":material/info: Visualize word frequencies in a cloud format.")
    
    if analysis is not None and words:  # Only show if analysis exists and we have words
        try:
            from wordcloud import WordCloud
            import matplotlib.pyplot as plt
            
            col1, col2 = st.columns(2)
            with col1:
                with st.container(border=True):
                    min_word_length = st.slider(
                        "Minimum Word Length",
                        min_value=1,
                        max_value=10,
                        value=3,
                        help="Filter out words shorter than this length"
                    )
            
            with col2:
                with st.container(border=True):
                    max_words = st.slider(
                        "Maximum Number of Words",
                        min_value=50,
                        max_value=500,
                        value=200,
                        help="Maximum number of words to include in the cloud"
                    )
            
            # Filter words by length and join them
            filtered_words = [word for word in words if len(word) >= min_word_length]
            
            if not filtered_words:
                st.warning(f":material/error: No words found with length >= {min_word_length}. Try a smaller minimum length.")
                st.stop()
            
            text = " ".join(filtered_words)
            
            with st.container(border=True):
                wordcloud = WordCloud(
                    width=800,
                    height=400,
                    background_color='white',
                    max_words=max_words
                ).generate(text)
                
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.imshow(wordcloud, interpolation='bilinear')
                ax.axis('off')
                st.pyplot(fig)
            
        except ImportError:
            st.info(":material/package: Install wordcloud package to enable word cloud visualization: `pip install wordcloud`")
        except Exception as e:
            st.error(":material/alert: Error generating word cloud")
            with st.expander(":material/help: Error Details"):
                st.caption(f":material/error: {str(e)}")
    else:
        st.info(":material/hand_pointing_up: Please select a text column above to generate word cloud") 