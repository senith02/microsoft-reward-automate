import argparse
import logging
import time
import random
import os
import datetime
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from random_word import RandomWords

# Set up command-line arguments
parser = argparse.ArgumentParser(description="Automate Bing searches for Microsoft Rewards.")
parser.add_argument("--driver-path", required=True, help="Path to Edge WebDriver (e.g., C:\\path\\to\\msedgedriver.exe)")
parser.add_argument("--desktop", type=int, default=0, help="Number of desktop searches")
parser.add_argument("--mobile", type=int, default=0, help="Number of mobile searches")
parser.add_argument("--log-dir", default="logs", help="Directory to store log files")
args = parser.parse_args()

# Create logs directory if it doesn't exist
os.makedirs(args.log_dir, exist_ok=True)

# Get today's date for log file naming
today = datetime.datetime.now().strftime("%Y-%m-%d")
log_file = os.path.join(args.log_dir, f"bing_searches_{today}.log")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Log script start with timestamp
logger.info(f"===== Bing Rewards Automation Started - {today} =====")

# Function to perform searches
def perform_searches(driver, num_searches, search_type):
    logger.info(f"Starting {num_searches} {search_type} searches")
    
    # Add a separator in the log file
    with open(log_file, "a") as f:
        f.write(f"\n--- {search_type.upper()} SEARCHES - {today} ---\n")
    
    r = RandomWords()
    prefixes = ["what is", "definition of", "how to", "examples of", "meaning of"]
    search_count = 0
    
    for i in range(num_searches):
        prefix = random.choice(prefixes)
        num_words = random.choices([1, 2, 3], weights=[0.7, 0.2, 0.1])[0]
        words = [r.get_random_word() for _ in range(num_words)]
        search_term = prefix + " " + " ".join(words)
        search_count += 1
        
        # Get timestamp for this search
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        try:
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            search_box.clear()
            search_box.send_keys(search_term)
            search_box.send_keys(Keys.RETURN)
            
            # Log the search with details
            logger.info(f"[{search_type}] ({search_count}/{num_searches}) {timestamp} - Searched: \"{search_term}\"")
            
            time.sleep(random.uniform(2, 4))  # Wait for page to load
        except Exception as e:
            logger.error(f"Error performing search: {e}")
        
        # Random delay between searches
        delay = random.uniform(5, 15)
        logger.debug(f"Waiting {delay:.2f} seconds before next search")
        time.sleep(delay)
    
    logger.info(f"Completed {num_searches} {search_type} searches")

# Desktop searches
logger.info("Initializing Edge WebDriver for desktop searches")
desktop_options = webdriver.EdgeOptions()
edge_service = Service(executable_path=args.driver_path)
driver = webdriver.Edge(service=edge_service, options=desktop_options)
driver.get("https://www.bing.com")

# Check if logged in
try:
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "id_s")))
    logger.info("Already logged in.")
except:
    logger.info("Not logged in. Please log in manually.")
    driver.get("https://login.live.com")
    input("Press Enter after logging in...")
    driver.get("https://www.bing.com")

# Get cookies for session reuse
cookies = driver.get_cookies()
logger.info("Session cookies captured for reuse")

# Perform desktop searches
if args.desktop > 0:
    perform_searches(driver, args.desktop, "desktop")
driver.quit()
logger.info("Desktop session closed")

# Mobile searches
if args.mobile > 0:
    logger.info("Initializing Edge WebDriver for mobile searches")
    mobile_options = webdriver.EdgeOptions()
    mobile_options.add_argument("--user-agent=Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Mobile Safari/537.36")
    edge_service = Service(executable_path=args.driver_path)
    driver = webdriver.Edge(service=edge_service, options=mobile_options)
    driver.get("https://www.bing.com")
    
    # Set cookies to reuse session
    for cookie in cookies:
        driver.add_cookie(cookie)
    logger.info("Session cookies applied to mobile session")
    
    # Perform mobile searches
    perform_searches(driver, args.mobile, "mobile")
    driver.quit()
    logger.info("Mobile session closed")

# Log script completion
logger.info(f"===== Bing Rewards Automation Completed - {today} =====")