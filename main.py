import streamlit as st
import requests
from bs4 import BeautifulSoup
from transformers import pipeline

# Initialize the NLP model (e.g., distilbart for summarization, can be customized)
summarizer = pipeline("summarization")
keyword_extractor = pipeline("ner", aggregation_strategy="simple")

# Streamlit UI
st.title("AI-Powered Web Scraper and Parser")

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
    return ", ".join([kw["word"] for kw in keywords if kw["entity_group"] == "MISC"])

def parse_content(content, response_type):
    if response_type == "Concise Summary":
        return summarize_content(content)
    elif response_type == "Detailed Analysis":
        return summarize_content(content)  # Can be the same summarizer for this demo
    elif response_type == "Keywords Only":
        return extract_keywords(content)

# Main scraping and parsing logic
if st.button("Scrape and Parse"):
    if url:
        st.write("Scraping the website...")
        html_content = scrape_website(url)
        
        if html_content:
            cleaned_content = clean_content(html_content)
            st.text_area("Cleaned Content Preview", cleaned_content[:3000], height=250)  # Display a portion
            
            if parse_description:
                st.write("Parsing the content with AI...")
                with st.spinner("Running AI parsing..."):
                    parsed_result = parse_content(cleaned_content, response_type)
                    st.write("Parsed Results:")
                    st.text_area("AI Output", parsed_result, height=250)
                    
                    # Download parsed results
                    st.download_button("Download Parsed Results", parsed_result, file_name="parsed_results.txt")
            else:
                st.warning("Please enter a parsing description.")
        else:
            st.error("Failed to retrieve content. Please check the URL and try again.")
