import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Just one DMA for testing
dma_target = {"dma_code": 524, "dma_name": "Atlanta (ATL)"}
base_url = "https://trends.google.com/trending?geo={dma}&hours=24&sort=search-volume"

def test_scrape_from_csv():
    # Create a dedicated downloads folder
    download_dir = os.path.join(os.getcwd(), "mcp_project", "downloads")
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    # Clean the directory before starting
    for f in os.listdir(download_dir):
        os.remove(os.path.join(download_dir, f))

    # Configure Firefox options for automatic downloads
    options = webdriver.FirefoxOptions()
    options.add_argument('--headless')
    options.binary_location = os.path.join(os.getcwd(), 'dependencies', 'FF_Portable', 'App', 'Firefox64', 'firefox.exe')
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.dir", download_dir)
    options.set_preference("browser.download.useDownloadDir", True)
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/csv")
    
    # Setup selenium webdriver
    gecko_driver_path = os.path.join(os.getcwd(), 'dependencies', 'geckodriver.exe')
    service = FirefoxService(executable_path=gecko_driver_path)
    driver = webdriver.Firefox(service=service, options=options)

    url = base_url.format(dma=dma_target["dma_code"])
    print(f"📡 Navigating to page for {dma_target['dma_name']}...")
    driver.get(url)

    try:
        # Use the more reliable XPath selector to find the export button
        export_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Export')]"))
        )
        print("✅ Export button found. Clicking...")
        export_button.click()
        
        # Wait for the download to complete
        time.sleep(5) 

        # Find the latest downloaded file
        list_of_files = os.listdir(download_dir)
        if not list_of_files:
            raise Exception("❌ No file was downloaded.")
            
        latest_file = max([os.path.join(download_dir, f) for f in list_of_files], key=os.path.getctime)
        print(f"📄 Found downloaded file: {os.path.basename(latest_file)}")
        
        # Read data from the CSV
        df = pd.read_csv(latest_file, skiprows=2)
        print("\n📊 Successfully parsed CSV data:")
        print(df.head())
        
        # Clean up the downloaded file
        os.remove(latest_file)
        print(f"\n🗑️ Processed and removed {os.path.basename(latest_file)}.")
        
    except Exception as e:
        print(f"\n⚠️ An error occurred: {e}")
    finally:
        driver.quit()
        print("✅ Script finished.")

if __name__ == "__main__":
    test_scrape_from_csv() 