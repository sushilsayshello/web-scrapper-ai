import os
import streamlit as st
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from selenium.webdriver import Remote, ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.chromium.remote_connection import ChromiumRemoteConnection
import time

# Load environment variables
load_dotenv()

# WebDriver setup from environment variable
SBR_WEBDRIVER = os.getenv("SBR_WEBDRIVER")

# Initialize Ollama model for parsing
model = OllamaLLM(model="llama3")

# Template for parsing instructions
template = (
    "You are tasked with extracting specific information from the following text content: {dom_content}. "
    "Please follow these instructions carefully: \n\n"
    "1. **Extract Information:** Only extract the information that directly matches the provided description: {parse_description}. "
    "2. **No Extra Content:** Do not include any additional text, comments, or explanations in your response. "
    "3. **Empty Response:** If no information matches the description, return an empty string ('')."
    "4. **Direct Data Only:** Your output should contain only the data that is explicitly requested, with no other text."
)

def scrape_website(website):
    # Configure Chrome options for headless mode
    options = ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # Connect to WebDriver
    sbr_connection = ChromiumRemoteConnection(SBR_WEBDRIVER, "goog", "chrome")
    with Remote(command_executor=sbr_connection, options=options) as driver:
        driver.get(website)
        
        # Check for CAPTCHA and wait if detected
        try:
            print("Checking for CAPTCHA...")
            time.sleep(5)  # Initial wait time
            captcha_element = driver.find_element(By.ID, "captcha")  # Adjust ID if needed
            if captcha_element:
                print("CAPTCHA detected; please solve manually if visible.")
                time.sleep(10)
            html = driver.page_source
            return html
        except Exception as e:
            print(f"Error while scraping: {e}")
            return None

def extract_body_content(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    body_content = soup.body
    return str(body_content) if body_content else ""

def clean_body_content(body_content):
    soup = BeautifulSoup(body_content, "html.parser")
    for script_or_style in soup(["script", "style"]):
        script_or_style.extract()
    cleaned_content = soup.get_text(separator="\n")
    cleaned_content = "\n".join(line.strip() for line in cleaned_content.splitlines() if line.strip())
    return cleaned_content

def split_dom_content(dom_content, max_length=6000):
    return [dom_content[i:i + max_length] for i in range(0, len(dom_content), max_length)]

def parse_with_ollama(dom_chunks, parse_description):
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | model
    parsed_results = []
    
    # Streamlit progress bar
    progress_bar = st.progress(0)
    total_chunks = len(dom_chunks)

    for i, chunk in enumerate(dom_chunks, start=1):
        try:
            response = chain.invoke({"dom_content": chunk, "parse_description": parse_description})
            print(f"Parsed batch: {i} of {total_chunks}")
            if response:
                parsed_results.append(response)
        except Exception as e:
            st.error(f"Error in parsing batch {i}: {e}")
            print(f"Error in batch {i}: {e}")
        progress_bar.progress(i / total_chunks)
    
    progress_bar.empty()
    return "\n".join(parsed_results).strip()

# Streamlit UI
st.title("AI Web Scraper")
url = st.text_input("Enter Website URL")

if st.button("Scrape Website"):
    if url:
        st.write("Scraping the website...")
        dom_content = scrape_website(url)
        if dom_content:
            body_content = extract_body_content(dom_content)
            cleaned_content = clean_body_content(body_content)
            st.session_state.dom_content = cleaned_content
            with st.expander("View DOM Content"):
                st.text_area("DOM Content", cleaned_content[:10000], height=300)  # Display a portion
        else:
            st.error("Failed to retrieve content. Please check the URL and try again.")

# Parsing Section
if "dom_content" in st.session_state:
    parse_description = st.text_area("Describe what you want to parse")
    if st.button("Parse Content"):
        if parse_description:
            st.write("Parsing the content...")
            dom_chunks = split_dom_content(st.session_state.dom_content)
            parsed_result = parse_with_ollama(dom_chunks, parse_description)
            st.write(parsed_result)
