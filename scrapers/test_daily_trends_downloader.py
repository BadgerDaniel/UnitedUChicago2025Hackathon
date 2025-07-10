import os
import time
import pandas as pd
import glob
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException

# --- Configuration (Copied from notebook and adapted for this script's location) ---
# Assumes the script is run from the project's root directory.
cwd = os.getcwd()
script_dir = "scrapers"
dependencies_dir = os.path.join(cwd, script_dir, "dependencies")
download_dir = os.path.join(cwd, script_dir, "downloads")
screenshot_dir = os.path.join(cwd, script_dir, "screenshots")

os.makedirs(download_dir, exist_ok=True)
os.makedirs(screenshot_dir, exist_ok=True)

# Clean the download directory before starting
for f in os.listdir(download_dir):
    os.remove(os.path.join(download_dir, f))

driver_path = os.path.join(dependencies_dir, "geckodriver.exe")
service_log_path = os.path.join(dependencies_dir, "geckodriver.log")
firefox_path = os.path.join(dependencies_dir, 'FF_Portable', 'App', 'Firefox64', 'firefox.exe')

# Firefox options from the reference notebook
firefox_options = Options()
firefox_options.binary_location = firefox_path
# firefox_options.add_argument('--headless') # Temporarily disabled for debugging
firefox_options.set_preference("permissions.default.image", 2)
firefox_options.set_preference("media.autoplay.default", 5)
firefox_options.set_preference("browser.download.folderList", 2)
firefox_options.set_preference("browser.download.dir", os.path.abspath(download_dir))
firefox_options.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/csv")
firefox_options.set_preference("browser.download.manager.showWhenStarting", False)
firefox_options.set_preference("pdfjs.disabled", True)

# WebDriver setup from the reference notebook
firefox_service = FirefoxService(executable_path=driver_path, log_output=service_log_path)
driver = webdriver.Firefox(service=firefox_service, options=firefox_options)

# --- Target Page ---
dma_target = {"dma_code": 524, "dma_name": "Atlanta (ATL)"}
base_url = "https://trends.google.com/trending?geo={dma}&hours=24&sort=search-volume"

# --- Main Scraping Logic ---
def download_daily_trends():
    url = base_url.format(dma=dma_target["dma_code"])
    print(f" Navigating to Daily Trends for {dma_target['dma_name']}...")
    driver.get(url)
    
    # Adding refresh and longer sleep, similar to the working notebook
    print(" Waiting for initial page load and refreshing...")
    time.sleep(5)
    driver.refresh()
    time.sleep(10) # Longer wait after refresh

    try:
        # A more precise XPath selector based on the visible text in the screenshot
        export_button_xpath = "//button[descendant::span[contains(text(), 'Export')]]"
        
        print(" Searching for the export button with new selector...")
        export_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, export_button_xpath))
        )
        
        print(" Export button found. Clicking to open menu...")
        driver.execute_script("arguments[0].click();", export_button)
        
        # Using the exact, full XPath you provided for the "Download CSV" option
        time.sleep(2) 
        download_csv_xpath = "/html/body/c-wiz/div/div[5]/div[1]/c-wiz/div/div[1]/div[3]/div[2]/div[2]/div/div[2]/div/div/ul/li[1]"
        print(" Searching for the 'Download CSV' button with the full XPath...")
        download_csv_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, download_csv_xpath))
        )
        print(" 'Download CSV' button found. Clicking to download...")
        driver.execute_script("arguments[0].click();", download_csv_button)

        # Wait for the download to start and complete
        time.sleep(5)

        list_of_files = glob.glob(os.path.join(download_dir, '*.csv'))
        if not list_of_files:
            raise Exception("No CSV file was downloaded.")
            
        latest_file = max(list_of_files, key=os.path.getctime)
        print(f"📄 Found downloaded file: {os.path.basename(latest_file)}")
        
        df = pd.read_csv(latest_file, skiprows=1)
        print("\n Successfully parsed CSV data:")
        print(df.head())
        
        os.remove(latest_file)
        print(f"\n Processed and removed {os.path.basename(latest_file)}.")
        
    except TimeoutException:
        print(f"Timeout: Could not find the export button.")
        screenshot_path = os.path.join(screenshot_dir, "daily_trends_failure.png")
        driver.save_screenshot(screenshot_path)
        print(f"A debug screenshot has been saved to: {screenshot_path}")
    except Exception as e:
        print(f"\n An unexpected error occurred: {e}")
    finally:
        driver.quit()
        print(" Script finished.")

if __name__ == "__main__":
    download_daily_trends() 
