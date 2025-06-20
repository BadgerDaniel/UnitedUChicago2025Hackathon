import os
import time
import pandas as pd
import glob
import asyncio
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException

# --- MCP Configuration ---
HOST = '127.0.0.1'
PORT = 1234

# --- Main Configuration ---
cwd = os.getcwd()
dependencies_dir = os.path.join(cwd, "dependencies")
download_dir = os.path.join(cwd, "mcp_project", "downloads")
os.makedirs(download_dir, exist_ok=True)

driver_path = os.path.join(dependencies_dir, "geckodriver.exe")
service_log_path = os.path.join(dependencies_dir, "geckodriver.log")
firefox_path = os.path.join(dependencies_dir, 'FF_Portable', 'App', 'Firefox64', 'firefox.exe')

# --- DMA Targets ---
dma_targets = [
    {"dma_code": 524, "dma_name": "Atlanta (ATL)"},
    {"dma_code": 803, "dma_name": "Los Angeles (LAX)"},
    {"dma_code": 623, "dma_name": "Dallas (DFW)"},
    {"dma_code": 751, "dma_name": "Denver (DEN)"},
    {"dma_code": 602, "dma_name": "Chicago (ORD)"},
]
base_url = "https://trends.google.com/trending?geo={dma}&hours=24&sort=search-volume"

async def send_mcp_message(writer, package, content):
    message = f"#$#{package} {content}\n"
    writer.write(message.encode())
    await writer.drain()

async def mcp_client_main(all_trends):
    reader, writer = await asyncio.open_connection(HOST, PORT)
    await send_mcp_message(writer, "mcp", "version: 2.1 to: 2.1")
    await send_mcp_message(writer, "mcp-auth", "type: client id: trend_scraper_v2_csv")

    for trend in all_trends:
        await send_mcp_message(writer, "trend-data",
            f":dma_code={trend['dma_code']} :dma_name=\"{trend['dma_name']}\" :trend=\"{trend['Trend']}\" :run_time=\"{trend['Run Time']}\"")

    print("\n✅ All trend data sent to MCP server.")
    writer.close()
    await writer.wait_closed()

def scrape_and_process_trends():
    now = datetime.now()
    all_trends = []

    # Clean the download directory before starting
    for f in os.listdir(download_dir):
        os.remove(os.path.join(download_dir, f))

    # --- Selenium Setup ---
    firefox_options = Options()
    firefox_options.binary_location = firefox_path
    firefox_options.add_argument('--headless')
    firefox_options.set_preference("browser.download.folderList", 2)
    firefox_options.set_preference("browser.download.dir", os.path.abspath(download_dir))
    firefox_options.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/csv")
    
    firefox_service = FirefoxService(executable_path=driver_path, log_output=service_log_path)
    driver = webdriver.Firefox(service=firefox_service, options=firefox_options)

    for target in dma_targets:
        dma_code = target["dma_code"]
        dma_name = target["dma_name"]
        url = base_url.format(dma=dma_code)
        
        print(f"\n📡 Processing DMA: {dma_name}")
        driver.get(url)

        try:
            time.sleep(5)
            driver.refresh()
            time.sleep(10)
            
            export_button_xpath = "//button[descendant::span[contains(text(), 'Export')]]"
            export_button = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, export_button_xpath)))
            driver.execute_script("arguments[0].click();", export_button)
            time.sleep(2)

            download_csv_xpath = "/html/body/c-wiz/div/div[5]/div[1]/c-wiz/div/div[1]/div[3]/div[2]/div[2]/div/div[2]/div/div/ul/li[1]"
            download_csv_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, download_csv_xpath)))
            driver.execute_script("arguments[0].click();", download_csv_button)
            time.sleep(5)
            
            list_of_files = glob.glob(os.path.join(download_dir, '*.csv'))
            if not list_of_files:
                print(f"⚠️ No CSV file found for {dma_name}. Skipping.")
                continue

            latest_file = max(list_of_files, key=os.path.getctime)
            
            # --- Data Cleaning and Filename Logic ---
            df = pd.read_csv(latest_file, skiprows=1)
            for index, row in df.iterrows():
                # The trend is usually in the first column
                trend_topic = row.iloc[0] 
                all_trends.append({
                    "dma_code": dma_code,
                    "dma_name": dma_name,
                    "Trend": trend_topic,
                    "Run Time": now.strftime("%Y-%m-%d %H:%M")
                })
            
            # Rename for logical archiving
            new_filename = f"{dma_name.replace(' ', '_')}_{now.strftime('%Y%m%d')}.csv"
            new_filepath = os.path.join(download_dir, new_filename)
            os.rename(latest_file, new_filepath)
            print(f"✅ Processed and renamed to {new_filename}")

        except Exception as e:
            print(f"❌ Failed to process {dma_name}: {e}")
            continue
    
    driver.quit()
    return all_trends

def main():
    trends = scrape_and_process_trends()
    if trends:
        asyncio.run(mcp_client_main(trends))
    else:
        print("\nNo trends were scraped, so nothing to send to MCP server.")

if __name__ == "__main__":
    main() 