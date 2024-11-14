import os
import time
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chromium.remote_connection import ChromiumRemoteConnection
from bs4 import BeautifulSoup
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
SBR_WEBDRIVER = os.getenv("SBR_WEBDRIVER")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")

# Configure Streamlit app
st.title("AI-Powered Web Scraper and Parser")

# Step 1: User Inputs
url = st.text_input("Enter Website URL")

response_type = st.selectbox(
    "Choose AI Response Type",
    options=["Concise Summary", "Detailed Analysis", "Keywords Only"]
)

parse_description = st.text_area("Describe what you want to parse")

# AI Model Setup
model = OllamaLLM(model="llama3", api_key=OLLAMA_API_KEY)
base_template = (
    "You are tasked with analyzing the following content: {content}. "
    "Instructions:\n"
    "1. **Extract Information** based on the provided description: {description}.\n"
)

# Modify template based on response type
templates = {
    "Concise Summary": base_template + "Provide a brief summary with essential information only.",
    "Detailed Analysis": base_template + "Provide a detailed analysis including all relevant insights.",
    "Keywords Only": base_template + "List key phrases or keywords only."
}

# Function to initialize ChromeDriver
def init_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    sbr_connection = ChromiumRemoteConnection(SBR_WEBDRIVER, "goog", "chrome")
    return webdriver.Remote(command_executor=sbr_connection, options=options)

# Function to scrape the website content
def scrape_website(website_url):
    try:
        driver = init_driver()
        driver.get(website_url)
        
        # Check for CAPTCHA
        try:
            driver.find_element(By.ID, "captcha")
            st.warning("CAPTCHA detected. Please solve manually if running locally.")
            time.sleep(10)  # Adjust as needed
        except:
            pass  # No CAPTCHA detected
        
        html_content = driver.page_source
        driver.quit()
        return html_content
    except Exception as e:
        st.error(f"Failed to scrape website: {e}")
        return None

# Function to extract and clean the body content
def clean_content(html):
    soup = BeautifulSoup(html, "html.parser")
    for script_or_style in soup(["script", "style"]):
        script_or_style.extract()
    return soup.get_text(separator="\n").strip()

# Split content for AI processing
def split_content(content, max_length=6000):
    return [content[i:i + max_length] for i in range(0, len(content), max_length)]

# AI-based parsing
def parse_content(content_chunks, description, response_type):
    template = templates[response_type]
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | model
    
    results = []
    for chunk in content_chunks:
        response = chain.invoke({"content": chunk, "description": description})
        results.append(response)
    
    return "\n".join(results).strip()

# Run scraping and parsing based on user inputs
if st.button("Scrape and Parse"):
    if url and parse_description:
        st.write("Scraping the website...")
        html_content = scrape_website(url)
        
        if html_content:
            cleaned_content = clean_content(html_content)
            content_chunks = split_content(cleaned_content)
            
            # Show preview of scraped content
            with st.expander("View Cleaned Content"):
                st.text_area("Cleaned Content", cleaned_content[:3000], height=250)

            st.write("Parsing the content with AI...")
            with st.spinner("Running AI parsing..."):
                parsed_result = parse_content(content_chunks, parse_description, response_type)
                st.write("Parsed Results:")
                st.text_area("AI Output", parsed_result, height=250)
                
                # Option to download results
                st.download_button("Download Parsed Results", parsed_result, file_name="parsed_results.txt")
        else:
            st.error("Failed to scrape the website. Please check the URL and try again.")
    else:
        st.warning("Please enter a URL and a parsing description.")
