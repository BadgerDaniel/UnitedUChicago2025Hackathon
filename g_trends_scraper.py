# g_trends_scraper.py

import os
import time
import datetime
import requests
import glob
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException
import shutil
# import will2live


# PATH SETUPS
cwd = os.getcwd() # where script is 
dependencies_dir = os.path.join(cwd, "dependencies")  # dependencies folder

download_folder_name = "google_trends_downloads"  # Change folder name as needed
download_dir = os.path.join(cwd, download_folder_name)  # Full path inside CWD


os.makedirs(dependencies_dir, exist_ok=True)
os.makedirs(download_dir, exist_ok=True) 

# GECKODRIVER AND LOG PATHS
driver_path = os.path.join(dependencies_dir, "geckodriver.exe")
service_log_path = os.path.join(dependencies_dir, "geckodriver.log")

# firefox exe path (modify if necessary)
firefox_path = r"C:\Program Files\Mozilla Firefox\firefox.exe"

### FIREFOX OPTIONS
firefox_options = Options()
firefox_options.binary_location = firefox_path
firefox_options.set_preference("permissions.default.image", 2)
firefox_options.set_preference("dom.ipc.plugins.enabled.libflashplayer.so", "false")
firefox_options.set_preference("media.autoplay.default", 5)
firefox_options.set_preference("media.autoplay.blocking_policy", 2)
firefox_options.set_preference("media.autoplay.allow-muted", False)
firefox_options.set_preference("media.autoplay.enabled.user-gestures-needed", False)
firefox_options.log.level = "trace"

# --- 📌 Set Firefox to Auto-Download to Custom Folder (Inside CWD) ---
firefox_options.set_preference("browser.download.folderList", 2)  # 2 = Use custom download path
firefox_options.set_preference("browser.download.dir", download_dir)  # Set dynamic download folder
firefox_options.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/csv")  # Auto-save CSV files
firefox_options.set_preference("browser.download.manager.showWhenStarting", False)  # Hide download popup
firefox_options.set_preference("pdfjs.disabled", True)  # Disable built-in PDF viewer

# FF WEBDRIVER
firefox_service = FirefoxService(executable_path=driver_path, log_output=service_log_path)
driver = webdriver.Firefox(service=firefox_service, options=firefox_options)


def rename_latest_files(keyword):
    """Finds the latest downloaded files and renames them based on type."""
    files = glob.glob(os.path.join(download_dir, "*.csv"))  # Get all CSV files
    if not files:
        print("No new files detected, skipping rename.")
        return

    file_mapping = {
        "multiTimeline": "time",
        "geoMap": "geo",
        "relatedEntities": "ents",
        "relatedQueries": "quer"
    }

    # find and rename files
    for file in files:
        original_name = os.path.basename(file)
        for key, tag in file_mapping.items():
            if key in original_name:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
                new_filename = f"{keyword.replace(' ', '_')}_{tag}_{timestamp}.csv"
                new_filepath = os.path.join(download_dir, new_filename)

                os.rename(file, new_filepath)
                print(f" Renamed: {original_name} → {new_filename}")



# --- Keywords
keywords = ["united airlines",'protest','riot','march','demonstration','rally','strike']

# --- Base Google Trends URL ---
base_url = "https://trends.google.com/trends/explore?date=now%201-d&geo=US&q={}&hl=en"


time_ranges = {
    "past_day": "now 1-d",
    "past_hour": "now 1-H",
    "past_4_hours": "now 4-H",
    "past_7_days": "now 7-d",
    "past_30_days": "today 1-m",
    "past_90_days": "today 3-m",
    "past_12_months": "today 12-m",
    "past_5_years": "today 5-y",
    "all_time": "all"
}

print("\nAvailable Time Ranges:")
for key in time_ranges:
    print(f" - {key}")

custom_time = input("\nEnter a time range from the list OR type 'custom' to enter a date range (YYYY-MM-DD YYYY-MM-DD): ").strip()

if custom_time == "custom":
    start_date = input("Enter start date (YYYY-MM-DD): ").strip()
    end_date = input("Enter end date (YYYY-MM-DD): ").strip()
    date_range = f"{start_date} {end_date}"
else:
    #date_range = time_ranges.get(custom_time, "now 1-d")  # default if input is invalid
    date_range = time_ranges.get(custom_time, "now 7-d") 

print(f"\n📅 Using time range: {date_range}\n")


base_url = f"https://trends.google.com/trends/explore?date={date_range}&geo=US&q={{}}&hl=en"

## find buttons w/ retry logic 
for keyword in keywords:
    url = base_url.format(keyword.replace(" ", "%20"))
    print(f"Opening URL: {url}")
    
    driver.get(url)
    time.sleep(5) 
    
    driver.refresh()  
    time.sleep(15)  

    attempts = 0
    max_attempts = 2

    while attempts < max_attempts:
        try:
            export_buttons = WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.XPATH, "//button[contains(@class, 'widget-actions-item export')]"))
            )

            if len(export_buttons) < 4:
                print(f"⚠ Only found {len(export_buttons)} export buttons. Retrying ({attempts+1}/{max_attempts})...")
                attempts += 1
                time.sleep(5)  # Small delay
                driver.refresh()  # Refresh the page
                time.sleep(37)  
                continue  # Try again
            
            print(f" found {len(export_buttons)} export buttons for {keyword}, clicking..")

            for button in export_buttons:
                try:
                    WebDriverWait(driver, 10).until(EC.element_to_be_clickable(button))
                    button.click()
                    time.sleep(3)
                except Exception as e:
                    print(f"Error clicking export button: {e}")

            print(f"files for {keyword} should be downloaded.")

            # rename files after dl
            time.sleep(5)  
            rename_latest_files(keyword)
            break  # exit when it works

        except TimeoutException:
            print(f" Timeout: Couldn't find export buttons for {keyword} (Attempt {attempts+1}/{max_attempts})")
            attempts += 1
            time.sleep(5)  

    print(f" Moving on with available data for {keyword}.")


rename_latest_files(keywords[-1])

# Close browser
driver.quit()



today_str = datetime.datetime.now().strftime("%Y-%m-%d")
timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")  # ensures unique folder name
destination_folder = os.path.join(download_dir, timestamp) 

os.makedirs(destination_folder, exist_ok=True)

files_moved = 0
for file in glob.glob(os.path.join(download_dir, f"*{today_str}.csv")):
    shutil.move(file, os.path.join(destination_folder, os.path.basename(file)))
    files_moved += 1

if files_moved:
    print(f" Moved {files_moved} files to: {destination_folder}")
else:
    print(" Nothing moved.")




### deletes any empty folders created by the above

for folder in os.listdir(download_dir):
    folder_path = os.path.join(download_dir, folder)
    if os.path.isdir(folder_path) and not os.listdir(folder_path):
        os.rmdir(folder_path)