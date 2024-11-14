from selenium.webdriver import Remote, ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import time

load_dotenv()

SBR_WEBDRIVER = os.getenv("SBR_WEBDRIVER")

def scrape_website(website):
    print("Connecting to Scraping Browser...")
    
    # Set up options for headless Chrome
    options = ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Establish a connection to the Chrome WebDriver
    sbr_connection = ChromiumRemoteConnection(SBR_WEBDRIVER, "goog", "chrome")
    
    # Use Remote WebDriver with headless Chrome options
    with Remote(command_executor=sbr_connection, options=options) as driver:
        driver.get(website)
        
        # Check for CAPTCHA
        try:
            print("Waiting for CAPTCHA to solve...")
            time.sleep(5)  # Wait and see if CAPTCHA resolves

            # Optional: Locate CAPTCHA elements and prompt users if not solved
            captcha_element = driver.find_element(By.ID, "captcha")  # Example; adjust as needed
            if captcha_element:
                print("CAPTCHA detected; waiting for manual solve...")
                time.sleep(10)  # Wait longer if CAPTCHA detected; adjust as needed

            print("Captcha solved or not detected. Navigating page...")
            html = driver.page_source
            return html
        
        except Exception as e:
            print(f"Error with CAPTCHA or scraping: {e}")
            return None
