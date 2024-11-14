import streamlit as st
import requests
from bs4 import BeautifulSoup
from transformers import pipeline
from collections import Counter
import pandas as pd
import plotly.express as px

# Initialize the NLP models
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6", revision="a4f8f3e")
keyword_extractor = pipeline("ner", aggregation_strategy="simple")

# Streamlit UI
st.title("AI-Powered Web Scraper and Parser with Interactive Visualizations")

# Step 1: User Inputs
url = st.text_input("Enter Website URL")
response_type = st.selectbox(
    "Choose AI Response Type",
    options=["Concise Summary", "Detailed Analysis", "Keywords Only"]
)
parse_description = st.text_area("Describe what you want to parse")

# Function to scrape website content
def scrape_website(website_url):
    try:
        response = requests.get(website_url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to retrieve content: {e}")
        return None

# Function to extract and clean text content
def clean_content(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    for script_or_style in soup(["script", "style"]):
        script_or_style.extract()  # Remove JavaScript and CSS
    return soup.get_text(separator="\n").strip()

# AI-based parsing functions
def summarize_content(content):
    return summarizer(content, max_length=100, min_length=30, do_sample=False)[0]["summary_text"]

def extract_keywords(content):
    keywords = keyword_extractor(content)
    return keywords  # Return list of keywords for visualization

def parse_content(content, response_type):
    if response_type == "Concise Summary":
        return summarize_content(content)
    elif response_type == "Detailed Analysis":
        return summarize_content(content)  # Using same summarizer for this demo
    elif response_type == "Keywords Only":
        return extract_keywords(content)

# Visualization: Word Frequency Analysis
def visualize_word_frequency(content):
    word_list = content.split()
    word_counts = Counter(word_list)
    word_counts_df = pd.DataFrame(word_counts.most_common(10), columns=["Word", "Frequency"])
    fig = px.bar(word_counts_df, x="Word", y="Frequency", title="Top 10 Word Frequencies")
    st.plotly_chart(fig)

# Visualization: Keyword Extraction
def visualize_keywords(keywords):
    keywords_df = pd.DataFrame(keywords)
    fig = px.bar(keywords_df, x="word", color="entity_group", title="Extracted Keywords and Entities")
    st.plotly_chart(fig)

# Main scraping and parsing logic
if st.button("Scrape and Parse"):
    if url:
        st.write("Scraping the website...")
        html_content = scrape_website(url)
        
        if html_content:
            cleaned_content = clean_content(html_content)
            st.text_area("Cleaned Content Preview", cleaned_content[:3000], height=250)  # Display a portion

            # Word Frequency Visualization
            st.subheader("Word Frequency Analysis")
            visualize_word_frequency(cleaned_content)

            # Run AI Parsing if description is provided
            if parse_description:
                st.write("Parsing the content with AI...")
                with st.spinner("Running AI parsing..."):
                    parsed_result = parse_content(cleaned_content, response_type)
                    st.write("Parsed Results:")

                    if response_type == "Keywords Only":
                        # Visualization for Keywords
                        st.subheader("Extracted Keywords and Entities")
                        visualize_keywords(parsed_result)
                        keywords_text = ", ".join([kw["word"] for kw in parsed_result])
                        st.text_area("Extracted Keywords", keywords_text, height=100)
                    else:
                        st.text_area("AI Output", parsed_result, height=250)
                    
                    # Download parsed results
                    st.download_button("Download Parsed Results", str(parsed_result), file_name="parsed_results.txt")
            else:
                st.warning("Please enter a parsing description.")
        else:
            st.error("Failed to retrieve content. Please check the URL and try again.")
