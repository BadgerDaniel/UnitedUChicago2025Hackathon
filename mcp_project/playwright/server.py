#!/usr/bin/env python3

"""MCP Playwright Server - Browser automation tools using Playwright."""

import argparse
import asyncio
import base64
import logging
import os
import time
import pandas as pd
import glob
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Union

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from fastmcp import FastMCP

# Global browser state
playwright_instance = None
browser: Optional[Browser] = None
context: Optional[BrowserContext] = None
page: Optional[Page] = None

# --- Trends Scraping Configuration ---
cwd = os.getcwd()
download_dir = os.path.join(cwd, "..", "downloads")
os.makedirs(download_dir, exist_ok=True)

# --- Available DMA Targets ---
DMA_TARGETS = [
    {"dma_code": 807, "dma_name": "San Francisco (SFO)"},
    {"dma_code": 803, "dma_name": "Los Angeles (LAX)"},
    {"dma_code": 602, "dma_name": "Chicago (ORD)"},
    {"dma_code": 524, "dma_name": "Atlanta (ATL)"},
    {"dma_code": 623, "dma_name": "Dallas (DFW)"},
    {"dma_code": 751, "dma_name": "Denver (DEN)"},
    {"dma_code": 501, "dma_name": "New York (JFK)"},
    {"dma_code": 819, "dma_name": "Seattle (SEA)"},
    {"dma_code": 506, "dma_name": "Boston (BOS)"},
    {"dma_code": 528, "dma_name": "Miami (MIA)"},
]

BASE_URL = "https://trends.google.com/trending?geo={dma}&hours=24&sort=search-volume"

# --- Keyword Search Configuration ---
KEYWORD_SEARCH_BASE_URL = "https://trends.google.com/trends/explore?date={time_range}&geo=US&q={keyword}&hl=en"

TIME_RANGES = {
    "past_hour": "now 1-H",
    "past_4_hours": "now 4-H", 
    "past_day": "now 1-d",
    "past_7_days": "now 7-d",
    "past_30_days": "today 1-m",
    "past_90_days": "today 3-m",
    "past_12_months": "today 12-m",
    "past_5_years": "today 5-y",
    "all_time": "all"
}

# Create the FastMCP app
app = FastMCP(
    name="playwright"
)

async def ensure_browser(headless: bool = True, browser_type: str = "chromium"):
    """Ensure browser is initialized."""
    global playwright_instance, browser, context, page
    
    if playwright_instance is None:
        playwright_instance = await async_playwright().start()
    
    if browser is None:
        if browser_type == "firefox":
            browser = await playwright_instance.firefox.launch(headless=headless)
        elif browser_type == "webkit":
            browser = await playwright_instance.webkit.launch(headless=headless)
        else:  # chromium
            browser = await playwright_instance.chromium.launch(headless=headless)
    
    if context is None:
        context = await browser.new_context()
    
    if page is None:
        page = await context.new_page()

@app.tool()
async def navigate(
    url: str,
    headless: bool = True,
    browser_type: str = "chromium",
    wait_for: str = "load"
) -> str:
    """Navigate to a URL.
    
    Args:
        url: URL to navigate to
        headless: Run browser in headless mode (default: True)
        browser_type: Browser to use (chromium, firefox, webkit)
        wait_for: Wait condition (load, domcontentloaded, networkidle)
    
    Returns:
        Success message with page title or error
    """
    try:
        await ensure_browser(headless, browser_type)
        
        await page.goto(url, wait_until=wait_for)
        title = await page.title()
        
        return f"Successfully navigated to {url}. Page title: '{title}'"
        
    except Exception as e:
        return f"Error navigating to {url}: {str(e)}"

@app.tool()
async def screenshot(
    name: str = "screenshot",
    selector: Optional[str] = None,
    encoded: bool = False,
    width: int = 1280,
    height: int = 720,
    full_page: bool = False
) -> str:
    """Take a screenshot of the current page or element.
    
    Args:
        name: Name for the screenshot file
        selector: CSS selector for element to screenshot (optional)
        encoded: Return as base64 encoded data URI (default: False)
        width: Viewport width (default: 1280)
        height: Viewport height (default: 720)
        full_page: Take full page screenshot (default: False)
    
    Returns:
        Screenshot data or file path or error message
    """
    global page
    
    if page is None:
        return "Error: No page loaded. Navigate to a URL first."
    
    try:
        # Set viewport size
        await page.set_viewport_size({"width": width, "height": height})
        
        # Take screenshot
        if selector:
            element = await page.query_selector(selector)
            if not element:
                return f"Error: Element with selector '{selector}' not found"
            screenshot_bytes = await element.screenshot()
        else:
            screenshot_bytes = await page.screenshot(full_page=full_page)
        
        if encoded:
            encoded_data = base64.b64encode(screenshot_bytes).decode()
            return f"data:image/png;base64,{encoded_data}"
        else:
            # Save to file
            filename = f"{name}.png"
            Path(filename).write_bytes(screenshot_bytes)
            return f"Screenshot saved as {filename}"
            
    except Exception as e:
        return f"Error taking screenshot: {str(e)}"

@app.tool()
async def click(selector: str, wait_for: str = "load") -> str:
    """Click an element on the page.
    
    Args:
        selector: CSS selector for element to click
        wait_for: Wait condition after click (load, domcontentloaded, networkidle, none)
    
    Returns:
        Success message or error
    """
    global page
    
    if page is None:
        return "Error: No page loaded. Navigate to a URL first."
    
    try:
        # Wait for element to be visible and enabled
        await page.wait_for_selector(selector, state="visible")
        
        if wait_for == "none":
            await page.click(selector)
        else:
            async with page.expect_load_state(wait_for):
                await page.click(selector)
        
        return f"Successfully clicked element: {selector}"
        
    except Exception as e:
        return f"Error clicking element '{selector}': {str(e)}"

@app.tool()
async def fill(selector: str, value: str, clear: bool = True) -> str:
    """Fill an input field.
    
    Args:
        selector: CSS selector for input field
        value: Value to fill
        clear: Clear field before filling (default: True)
    
    Returns:
        Success message or error
    """
    global page
    
    if page is None:
        return "Error: No page loaded. Navigate to a URL first."
    
    try:
        # Wait for element to be visible
        await page.wait_for_selector(selector, state="visible")
        
        if clear:
            await page.fill(selector, value)
        else:
            await page.type(selector, value)
        
        return f"Successfully filled '{selector}' with value"
        
    except Exception as e:
        return f"Error filling input '{selector}': {str(e)}"

@app.tool()
async def select_option(selector: str, value: str) -> str:
    """Select an option in a select element.
    
    Args:
        selector: CSS selector for select element
        value: Value or text to select
    
    Returns:
        Success message or error
    """
    global page
    
    if page is None:
        return "Error: No page loaded. Navigate to a URL first."
    
    try:
        await page.wait_for_selector(selector, state="visible")
        await page.select_option(selector, value)
        
        return f"Successfully selected '{value}' in {selector}"
        
    except Exception as e:
        return f"Error selecting option in '{selector}': {str(e)}"

@app.tool()
async def hover(selector: str) -> str:
    """Hover over an element.
    
    Args:
        selector: CSS selector for element to hover
    
    Returns:
        Success message or error
    """
    global page
    
    if page is None:
        return "Error: No page loaded. Navigate to a URL first."
    
    try:
        await page.wait_for_selector(selector, state="visible")
        await page.hover(selector)
        
        return f"Successfully hovered over {selector}"
        
    except Exception as e:
        return f"Error hovering over '{selector}': {str(e)}"

@app.tool()
async def evaluate(script: str) -> str:
    """Execute JavaScript in the browser.
    
    Args:
        script: JavaScript code to execute
    
    Returns:
        Result of the JavaScript execution or error
    """
    global page
    
    if page is None:
        return "Error: No page loaded. Navigate to a URL first."
    
    try:
        result = await page.evaluate(script)
        return str(result) if result is not None else "null"
        
    except Exception as e:
        return f"Error executing JavaScript: {str(e)}"

@app.tool()
async def get_text(selector: str) -> str:
    """Get text content of an element.
    
    Args:
        selector: CSS selector for element
    
    Returns:
        Text content or error
    """
    global page
    
    if page is None:
        return "Error: No page loaded. Navigate to a URL first."
    
    try:
        element = await page.query_selector(selector)
        if not element:
            return f"Error: Element with selector '{selector}' not found"
        
        text = await element.text_content()
        return text or ""
        
    except Exception as e:
        return f"Error getting text from '{selector}': {str(e)}"

@app.tool()
async def get_attribute(selector: str, attribute: str) -> str:
    """Get attribute value of an element.
    
    Args:
        selector: CSS selector for element
        attribute: Attribute name to get
    
    Returns:
        Attribute value or error
    """
    global page
    
    if page is None:
        return "Error: No page loaded. Navigate to a URL first."
    
    try:
        element = await page.query_selector(selector)
        if not element:
            return f"Error: Element with selector '{selector}' not found"
        
        value = await element.get_attribute(attribute)
        return value or ""
        
    except Exception as e:
        return f"Error getting attribute '{attribute}' from '{selector}': {str(e)}"

@app.tool()
async def wait_for_selector(selector: str, timeout: int = 30000, state: str = "visible") -> str:
    """Wait for an element to appear.
    
    Args:
        selector: CSS selector for element to wait for
        timeout: Timeout in milliseconds (default: 30000)
        state: State to wait for (visible, hidden, attached, detached)
    
    Returns:
        Success message or error
    """
    global page
    
    if page is None:
        return "Error: No page loaded. Navigate to a URL first."
    
    try:
        await page.wait_for_selector(selector, timeout=timeout, state=state)
        return f"Element '{selector}' is now {state}"
        
    except Exception as e:
        return f"Error waiting for '{selector}': {str(e)}"

@app.tool()
async def get_page_info() -> str:
    """Get current page information.
    
    Returns:
        Page title, URL, and basic info
    """
    global page
    
    if page is None:
        return "Error: No page loaded. Navigate to a URL first."
    
    try:
        title = await page.title()
        url = page.url
        viewport = page.viewport_size
        
        return f"Title: {title}\nURL: {url}\nViewport: {viewport['width']}x{viewport['height']}"
        
    except Exception as e:
        return f"Error getting page info: {str(e)}"

@app.tool()
async def close_browser() -> str:
    """Close the browser and clean up resources.
    
    Returns:
        Success message
    """
    global playwright_instance, browser, context, page
    
    try:
        if page:
            await page.close()
            page = None
        
        if context:
            await context.close()
            context = None
        
        if browser:
            await browser.close()
            browser = None
        
        if playwright_instance:
            await playwright_instance.stop()
            playwright_instance = None
        
        return "Browser closed successfully"
        
    except Exception as e:
        return f"Error closing browser: {str(e)}"

# --- Trends Scraping Functions ---
def get_available_locations() -> list:
    """Return list of available DMA locations for trends scraping."""
    return [{"code": target["dma_code"], "name": target["dma_name"]} for target in DMA_TARGETS]

async def scrape_trends_for_location(dma_code: int, dma_name: str) -> Dict[str, Any]:
    """Scrape Google Trends data for a specific DMA location using Playwright."""
    now = datetime.now()
    trends_data = []
    
    # Clean the download directory before starting
    for f in os.listdir(download_dir):
        try:
            os.remove(os.path.join(download_dir, f))
        except:
            pass  # Skip files that can't be removed
    
    try:
        # Ensure we have a browser instance
        await ensure_browser(headless=True, browser_type="chromium")
        
        url = BASE_URL.format(dma=dma_code)
        print(f"\n📡 Processing DMA: {dma_name}")
        await page.goto(url, wait_until="networkidle")
        
        # Wait for page to load and refresh
        await asyncio.sleep(5)
        await page.reload(wait_until="networkidle")
        await asyncio.sleep(10)
        
        # Click export button
        export_button_xpath = "//button[contains(@aria-label, 'Export')]"
        await page.wait_for_selector(export_button_xpath, timeout=20000)
        await page.click(export_button_xpath)
        await asyncio.sleep(2)
        
        # Click download CSV option
        download_csv_xpath = "/html/body/c-wiz/div/div[5]/div[1]/c-wiz/div/div[1]/div[3]/div[2]/div[2]/div/div[2]/div/div/ul/li[1]"
        await page.wait_for_selector(download_csv_xpath, timeout=10000)
        await page.click(download_csv_xpath)
        await asyncio.sleep(5)
        
        # Wait for download to complete
        list_of_files = glob.glob(os.path.join(download_dir, '*.csv'))
        if not list_of_files:
            return {"error": f"No CSV file found for {dma_name}"}
        
        latest_file = max(list_of_files, key=os.path.getctime)
        
        # Process the CSV data
        df = pd.read_csv(latest_file, skiprows=2)
        for index, row in df.iterrows():
            trend_topic = row.iloc[0] 
            trends_data.append({
                "dma_code": dma_code,
                "dma_name": dma_name,
                "trend": trend_topic,
                "run_time": now.strftime("%Y-%m-%d %H:%M")
            })
        
        # Rename for logical archiving
        new_filename = f"{dma_name.replace(' ', '_')}_{now.strftime('%Y%m%d')}.csv"
        new_filepath = os.path.join(download_dir, new_filename)
        os.rename(latest_file, new_filepath)
        print(f"✅ Processed and renamed to {new_filename}")
        
        return {
            "success": True,
            "location": dma_name,
            "trends_count": len(trends_data),
            "trends": trends_data,
            "timestamp": now.strftime("%Y-%m-%d %H:%M")
        }
        
    except Exception as e:
        return {"error": f"Failed to process {dma_name}: {str(e)}"}

# --- Keyword-Based Trend Scraping Functions ---

def get_available_time_ranges() -> dict:
    """Return available time ranges for keyword searches."""
    return TIME_RANGES

async def scrape_keyword_trends(keyword: str, time_range: str = "past_day") -> Dict[str, Any]:
    """Scrape Google Trends data for a specific keyword using the explore URL."""
    now = datetime.now()
    
    # Clean the download directory before starting
    for f in os.listdir(download_dir):
        try:
            os.remove(os.path.join(download_dir, f))
        except:
            pass  # Skip files that can't be removed
    
    try:
        # Ensure we have a browser instance
        await ensure_browser(headless=True, browser_type="chromium")
        
        # Format the URL
        formatted_time_range = TIME_RANGES.get(time_range, TIME_RANGES["past_day"])
        url = KEYWORD_SEARCH_BASE_URL.format(
            time_range=formatted_time_range,
            keyword=keyword.replace(" ", "%20")
        )
        
        print(f"\n🔍 Processing keyword: {keyword} (time range: {time_range})")
        await page.goto(url, wait_until="networkidle")
        
        # Wait for page to load and refresh
        await asyncio.sleep(5)
        await page.reload(wait_until="networkidle")
        await asyncio.sleep(15)
        
        # Select metro resolution (from the notebook)
        await select_metro_resolution()
        
        # Find and click export buttons
        export_buttons = await page.query_selector_all("//button[contains(@class, 'widget-actions-item export')]")
        
        if len(export_buttons) < 4:
            return {"error": f"Only found {len(export_buttons)} export buttons for '{keyword}'"}
        
        print(f"🟢 Found {len(export_buttons)} export buttons for '{keyword}', clicking...")
        
        for button in export_buttons:
            try:
                await button.click()
                await asyncio.sleep(3)
            except Exception as e:
                print(f"⚠ Error clicking export button: {e}")
        
        await asyncio.sleep(5)
        
        # Process downloaded files
        csv_files = glob.glob(os.path.join(download_dir, "*.csv"))
        if not csv_files:
            return {"error": f"No CSV files found for '{keyword}'"}
        
        # Process and rename files
        results = await process_keyword_csv_files(keyword, csv_files)
        
        return {
            "success": True,
            "keyword": keyword,
            "time_range": time_range,
            "files_processed": len(results),
            "data": results,
            "timestamp": now.strftime("%Y-%m-%d %H:%M")
        }
        
    except Exception as e:
        return {"error": f"Failed to process keyword '{keyword}': {str(e)}"}

async def select_metro_resolution():
    """Select metro resolution for geographic data (from the notebook)."""
    try:
        # Click the dropdown to open it
        dropdown_xpath = "//md-select[contains(@class, 'resolution-select')]"
        dropdown = await page.wait_for_selector(dropdown_xpath, timeout=10000)
        await dropdown.click()
        await asyncio.sleep(2)  # Wait for animation
        
        # Wait for the metro option and click it
        metro_option_xpath = "//md-option[@value='metro']"
        metro_option = await page.wait_for_selector(metro_option_xpath, timeout=10000)
        await metro_option.click()
        
        print("✅ Metro resolution selected.")
        await asyncio.sleep(7)  # Wait for the graph to update
        
    except Exception as e:
        print(f"⚠ Error selecting Metro resolution: {e}")
        # Try to close any open menus
        try:
            backdrop_xpath = "//md-backdrop[contains(@class, '_md-select-backdrop')]"
            backdrop = await page.query_selector(backdrop_xpath)
            if backdrop:
                await backdrop.click()
                print("Clicked backdrop to close dropdown.")
        except Exception:
            pass

async def process_keyword_csv_files(keyword: str, csv_files: list) -> list:
    """Process and rename CSV files for keyword searches."""
    results = []
    timestamp = datetime.now().strftime("%Y-%m-%d")
    
    file_mapping = {
        "multiTimeline": "time",
        "geoMap": "geo", 
        "relatedEntities": "ents",
        "relatedQueries": "quer"
    }
    
    for file_path in csv_files:
        try:
            original_name = os.path.basename(file_path)
            
            # Determine file type and create new name
            for key, tag in file_mapping.items():
                if key in original_name:
                    new_filename = f"{keyword.replace(' ', '_')}_{tag}_{timestamp}.csv"
                    new_filepath = os.path.join(download_dir, new_filename)
                    
                    # Read and process the CSV data
                    df = pd.read_csv(file_path, skiprows=2)
                    
                    # Store the data
                    results.append({
                        "file_type": tag,
                        "filename": new_filename,
                        "data": df.to_dict('records'),
                        "row_count": len(df)
                    })
                    
                    # Rename the file
                    os.rename(file_path, new_filepath)
                    print(f"✅ Renamed: {original_name} → {new_filename}")
                    break
                    
        except Exception as e:
            print(f"⚠ Error processing file {file_path}: {e}")
    
    return results

# --- Trends Scraping Tools ---
@app.tool()
async def get_available_trends_locations() -> str:
    """Get list of available DMA locations for Google Trends scraping.
    
    This tool is for LOCATION-BASED trending topics - it shows what locations
    are available to get current trending topics from.
    
    Returns:
        JSON string with available locations and their DMA codes
    """
    try:
        locations = get_available_locations()
        return f"Available locations: {locations}"
    except Exception as e:
        return f"Error getting available locations: {str(e)}"

@app.tool()
async def scrape_google_trends(
    dma_code: int,
    dma_name: str
) -> str:
    """Scrape Google Trends data for a specific DMA location.
    
    This tool is for LOCATION-BASED trending topics - it gets current trending
    topics for a specific geographic location.
    
    Args:
        dma_code: DMA code for the location (e.g., 602 for Chicago)
        dma_name: Name of the location (e.g., "Chicago (ORD)")
    
    Returns:
        JSON string with trends data or error message
    """
    try:
        print(f"🔥 Starting trends scrape for {dma_name} (DMA: {dma_code})")
        result = await scrape_trends_for_location(dma_code, dma_name)
        
        if "error" in result:
            return f"Error: {result['error']}"
        else:
            # Format the trends data nicely
            trends_list = [trend["trend"] for trend in result["trends"]]
            trends_text = "\n".join([f"{i+1}. {trend}" for i, trend in enumerate(trends_list)])
            
            return f"""Successfully scraped trends for {result['location']}:
            
Trending topics:
{trends_text}

Total: {result['trends_count']} trending topics
Scraped at: {result['timestamp']}"""
        
    except Exception as e:
        return f"Error scraping trends: {str(e)}"

@app.tool()
async def scrape_all_trends_locations() -> str:
    """Scrape Google Trends data for all available DMA locations.
    
    This tool is for LOCATION-BASED trending topics - it gets current trending
    topics for all available geographic locations.
    
    Returns:
        JSON string with trends data for all locations
    """
    try:
        all_results = []
        locations = get_available_locations()
        
        for location in locations:
            print(f"🔥 Scraping trends for {location['name']}...")
            result = await scrape_trends_for_location(location['code'], location['name'])
            all_results.append(result)
            await asyncio.sleep(2)  # Small delay between requests
        
        # Format results
        formatted_results = []
        for result in all_results:
            if "error" in result:
                formatted_results.append(f"❌ {result['location']}: {result['error']}")
            else:
                trends_list = [trend["trend"] for trend in result["trends"][:5]]  # Show top 5
                trends_text = ", ".join(trends_list)
                formatted_results.append(f"✅ {result['location']}: {trends_text}...")
        
        return f"Scraping completed for all locations:\n\n" + "\n".join(formatted_results)
        
    except Exception as e:
        return f"Error scraping all locations: {str(e)}"

# --- Keyword-Based Trend Scraping Tools ---

@app.tool()
async def get_available_time_ranges() -> str:
    """Get list of available time ranges for keyword-based trend searches.
    
    This tool is for KEYWORD-BASED trend searches - it shows what time ranges
    are available for searching specific keywords.
    
    Returns:
        JSON string with available time ranges
    """
    try:
        time_ranges = get_available_time_ranges()
        return f"Available time ranges: {time_ranges}"
    except Exception as e:
        return f"Error getting available time ranges: {str(e)}"

@app.tool()
async def search_keyword_trends(
    keyword: str,
    time_range: str = "past_day"
) -> str:
    """Search Google Trends data for a specific keyword.
    
    This tool is for KEYWORD-BASED trend searches - it searches for trends
    related to a specific keyword over a specified time period.
    
    Args:
        keyword: The keyword to search for (e.g., "united airlines", "protest")
        time_range: Time range for the search (default: "past_day")
                   Options: past_hour, past_4_hours, past_day, past_7_days,
                   past_30_days, past_90_days, past_12_months, past_5_years, all_time
    
    Returns:
        JSON string with trend data for the keyword or error message
    """
    try:
        print(f"🔍 Starting keyword search for '{keyword}' (time range: {time_range})")
        result = await scrape_keyword_trends(keyword, time_range)
        
        if "error" in result:
            return f"Error: {result['error']}"
        else:
            # Format the results nicely
            summary = f"""Successfully scraped trends for keyword '{result['keyword']}':

Time Range: {result['time_range']}
Files Processed: {result['files_processed']}
Scraped at: {result['timestamp']}

Data Summary:"""
            
            for data_file in result['data']:
                summary += f"\n• {data_file['file_type'].upper()}: {data_file['row_count']} rows"
                if data_file['row_count'] > 0:
                    # Show first few rows as preview
                    preview_data = data_file['data'][:3]
                    summary += f"\n  Preview: {preview_data}"
            
            return summary
        
    except Exception as e:
        return f"Error searching keyword trends: {str(e)}"

@app.tool()
async def search_multiple_keywords(
    keywords: list,
    time_range: str = "past_day"
) -> str:
    """Search Google Trends data for multiple keywords.
    
    This tool is for KEYWORD-BASED trend searches - it searches for trends
    related to multiple keywords over a specified time period.
    
    Args:
        keywords: List of keywords to search for (e.g., ["united airlines", "protest", "strike"])
        time_range: Time range for the search (default: "past_day")
                   Options: past_hour, past_4_hours, past_day, past_7_days,
                   past_30_days, past_90_days, past_12_months, past_5_years, all_time
    
    Returns:
        JSON string with trend data for all keywords or error message
    """
    try:
        print(f"🔍 Starting multi-keyword search for {len(keywords)} keywords (time range: {time_range})")
        all_results = []
        
        for keyword in keywords:
            print(f"🔥 Searching trends for '{keyword}'...")
            result = await scrape_keyword_trends(keyword, time_range)
            all_results.append(result)
            await asyncio.sleep(2)  # Small delay between requests
        
        # Format results
        summary = f"Multi-keyword search completed for {len(keywords)} keywords:\n\n"
        
        for i, result in enumerate(all_results):
            if "error" in result:
                summary += f"❌ {keywords[i]}: {result['error']}\n"
            else:
                summary += f"✅ {result['keyword']}: {result['files_processed']} files processed\n"
        
        return summary
        
    except Exception as e:
        return f"Error searching multiple keywords: {str(e)}"

async def cleanup():
    """Clean up browser resources on shutdown."""
    await close_browser()

def setup_server_config():
    """Setup server configuration from command line args."""
    parser = argparse.ArgumentParser(description="MCP Playwright Server")
    parser.add_argument(
        "--port",
        type=int,
        default=8003,
        help="Port to run server on (default: 8003)"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to run server on (default: 127.0.0.1)"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    return args

if __name__ == "__main__":
    print("Starting MCP Playwright server...")
    print("Browser automation tools ready")
    
    try:
        args = setup_server_config()
        print(f"Server starting on {args.host}:{args.port}")
        
        # Run the server with SSE transport
        app.run(transport="sse")
        
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        # Ensure cleanup happens
        asyncio.run(cleanup())