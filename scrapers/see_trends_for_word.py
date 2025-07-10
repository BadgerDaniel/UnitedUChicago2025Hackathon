# BLOCK 1: Setup

import os
import time
import datetime
import requests
import glob
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException

# Paths and Directories
cwd = os.getcwd()
dependencies_dir = os.path.join(cwd, "dependencies")
download_folder_name = "google_trends_downloads"
download_dir = os.path.join(cwd, download_folder_name)
screenshot_dir = os.path.join(cwd, "screenshots")

os.makedirs(dependencies_dir, exist_ok=True)
os.makedirs(download_dir, exist_ok=True)
os.makedirs(screenshot_dir, exist_ok=True)

driver_path = os.path.join(dependencies_dir, "geckodriver.exe")
service_log_path = os.path.join(dependencies_dir, "geckodriver.log")
firefox_path = r"C:\Program Files\Mozilla Firefox\firefox.exe"

# Firefox options
firefox_options = Options()
firefox_options.binary_location = firefox_path
firefox_options.set_preference("permissions.default.image", 2)
firefox_options.set_preference("media.autoplay.default", 5)
firefox_options.set_preference("browser.download.folderList", 2)
firefox_options.set_preference("browser.download.dir", download_dir)
firefox_options.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/csv")
firefox_options.set_preference("browser.download.manager.showWhenStarting", False)
firefox_options.set_preference("pdfjs.disabled", True)

# WebDriver
firefox_service = FirefoxService(executable_path=driver_path, log_output=service_log_path)
driver = webdriver.Firefox(service=firefox_service, options=firefox_options)

def take_screenshot(driver, name):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join([c if c.isalnum() else "_" for c in name])
    screenshot_path = os.path.join(screenshot_dir, f"{safe_name}_{timestamp}.png")
    try:
        driver.save_screenshot(screenshot_path)
        print(f"📸 Screenshot saved to: {screenshot_path}")
    except Exception as e:
        print(f"Failed to take screenshot: {e}")

def rename_latest_files(keyword):
    files = glob.glob(os.path.join(download_dir, "*.csv"))
    if not files:
        print("No new files detected, skipping rename.")
        return

    file_mapping = {
        "multiTimeline": "time",
        "geoMap": "geo",
        "relatedEntities": "ents",
        "relatedQueries": "quer"
    }

    for file in files:
        original_name = os.path.basename(file)
        for key, tag in file_mapping.items():
            if key in original_name:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
                new_filename = f"{keyword.replace(' ', '_')}_{tag}_{timestamp}.csv"
                new_filepath = os.path.join(download_dir, new_filename)
                try:
                    os.replace(file, new_filepath)
                    print(f" Renamed: {original_name} → {new_filename}")
                except FileNotFoundError:
                    print(f"Warning: Could not find {original_name} to rename. It might have been moved already.")

def select_metro_resolution(driver):
    try:
        take_screenshot(driver, "before_metro_dropdown_click")
        
        # Click the dropdown to open it
        dropdown_xpath = "//md-select[contains(@class, 'resolution-select')]"
        dropdown = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, dropdown_xpath)))
        driver.execute_script("arguments[0].click();", dropdown)
        time.sleep(2) # Wait for animation
        
        take_screenshot(driver, "after_metro_dropdown_click")

        # Wait for the metro option to be present and then click it with JS
        # Using @value='metro' is more robust than a dynamic ID
        metro_option_xpath = "//md-option[@value='metro']"
        metro_option = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, metro_option_xpath)))
        driver.execute_script("arguments[0].click();", metro_option)
        
        print(" Metro resolution selected.")
        take_screenshot(driver, "after_metro_option_selected")
        time.sleep(7) # Wait for the graph to update
        
    except Exception as e:
        print(f"[ERROR] Error selecting Metro resolution: {e}")
        take_screenshot(driver, "metro_selection_error")
    finally:
        # If something went wrong, try to click the backdrop to close any open menus
        try:
            backdrop_xpath = "//md-backdrop[contains(@class, '_md-select-backdrop')]"
            backdrop = driver.find_element(By.XPATH, backdrop_xpath)
            if backdrop.is_displayed():
                driver.execute_script("arguments[0].click();", backdrop)
                print("Clicked backdrop to close dropdown.")
        except Exception:
            pass # Backdrop may not exist or be visible, which is fine.
# BLOCK 2: Core download logic — with Metro resolution selection

# --- SET TO TRUE TO USE DEFAULTS FOR TESTING ---
USE_DEFAULT_TIME_RANGE = True
# ---------------------------------------------

keywords = ["united airlines", "protest", "riot", "march", "demonstration", "rally", "strike"]

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

if USE_DEFAULT_TIME_RANGE:
    date_range = "now 1-d"
else:
    print("\nAvailable Time Ranges:")
    for key in time_ranges:
        print(f" - {key}")
    
    custom__time = input("\nEnter a time range from the list OR type 'custom' to enter a date range (YYYY-MM-DD YYYY-MM-DD): ").strip()
    if custom_time == "custom":
        start_date = input("Enter start date (YYYY-MM-DD): ").strip()
        end_date = input("Enter end date (YYYY-MM-DD): ").strip()
        date_range = f"{start_date} {end_date}"
    else:
        date_range = time_ranges.get(custom_time, "now 1-d")

print(f"\n Using time range: {date_range}\n")

base_url = f"https://trends.google.com/trends/explore?date={date_range}&geo=US&q={{}}&hl=en"

for keyword in keywords:
    url = base_url.format(keyword.replace(" ", "%20"))
    print(f" Opening URL: {url}")
    driver.get(url)
    time.sleep(5)
    driver.refresh()
    time.sleep(15)

    attempts = 0
    max_attempts = 2

    while attempts < max_attempts:
        try:
            select_metro_resolution(driver)

            export_buttons = WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.XPATH, "//button[contains(@class, 'widget-actions-item export')]"))
            )

            if len(export_buttons) < 4:
                print(f"⚠ Only found {len(export_buttons)} export buttons. Retrying ({attempts+1}/{max_attempts})...")
                take_screenshot(driver, f"not_enough_buttons_for_{keyword}")
                attempts += 1
                time.sleep(5)
                driver.refresh()
                time.sleep(37)
                continue

            print(f" Found {len(export_buttons)} export buttons for '{keyword}', clicking...")

            for button in export_buttons:
                try:
                    driver.execute_script("arguments[0].click();", button)
                    time.sleep(3)
                except Exception as e:
                    print(f"⚠ Error clicking export button: {e}")
                    take_screenshot(driver, f"export_button_click_error_for_{keyword}")

            time.sleep(5)
            rename_latest_files(keyword)
            break

        except TimeoutException:
            print(f" Timeout: Couldn't find export buttons for '{keyword}' (Attempt {attempts+1}/{max_attempts})")
            take_screenshot(driver, f"export_button_timeout_for_{keyword}")
            attempts += 1
            time.sleep(5)

    print(f"Finished attempting for '{keyword}'. Moving on...\n")
# BLOCK 3: File organization and cleanup

rename_latest_files(keywords[-1])
driver.quit()

today_str = datetime.datetime.now().strftime("%Y-%m-%d")
timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
destination_folder = os.path.join(download_dir, timestamp)

os.makedirs(destination_folder, exist_ok=True)

files_moved = 0
for file in glob.glob(os.path.join(download_dir, f"*{today_str}.csv")):
    shutil.move(file, os.path.join(destination_folder, os.path.basename(file)))
    files_moved += 1

if files_moved:
    print(f"Moved {files_moved} files to: {destination_folder}")
else:
    print("No files matched today’s date pattern.")

# Cleanup any empty leftover folders
for folder in os.listdir(download_dir):
    folder_path = os.path.join(download_dir, folder)
    if os.path.isdir(folder_path) and not os.listdir(folder_path):
        os.rmdir(folder_path)
