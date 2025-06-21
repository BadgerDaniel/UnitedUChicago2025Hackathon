# Google Trends Integration with Playwright MCP Server

## Overview

I've successfully integrated Google Trends scraping functionality into the Playwright MCP server. This allows Claude to use Playwright's powerful browser automation capabilities to scrape Google Trends data for different DMA (Designated Market Area) locations.

## What Was Added

### 1. **New Imports and Configuration**
```python
import os
import time
import pandas as pd
import glob
from datetime import datetime

# Trends scraping configuration
cwd = os.getcwd()
download_dir = os.path.join(cwd, "..", "downloads")
os.makedirs(download_dir, exist_ok=True)

# Available DMA locations
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
```

### 2. **Core Scraping Function**
```python
async def scrape_trends_for_location(dma_code: int, dma_name: str) -> Dict[str, Any]:
    """Scrape Google Trends data for a specific DMA location using Playwright."""
```

**Key Features:**
- Uses Playwright's async browser automation
- Handles page loading, refreshing, and element interaction
- Downloads CSV files automatically
- Processes and cleans the data
- Returns structured results

### 3. **Three New Tools for Claude**

#### Tool 1: `get_available_trends_locations()`
**Purpose:** Get list of available DMA locations
**Usage:** Claude can call this to see what locations are available
**Returns:** List of locations with their DMA codes

#### Tool 2: `scrape_google_trends(dma_code, dma_name)`
**Purpose:** Scrape trends for a specific location
**Parameters:**
- `dma_code`: Integer DMA code (e.g., 602 for Chicago)
- `dma_name`: String location name (e.g., "Chicago (ORD)")
**Returns:** Formatted trends data or error message

#### Tool 3: `scrape_all_trends_locations()`
**Purpose:** Scrape trends for all available locations
**Returns:** Summary of trends data for all locations

## How It Works - Step by Step

### 1. **Browser Setup**
```python
await ensure_browser(headless=True, browser_type="chromium")
```
- Creates a headless Chromium browser instance
- No visible browser window (runs in background)

### 2. **Page Navigation**
```python
url = BASE_URL.format(dma=dma_code)
await page.goto(url, wait_until="networkidle")
```
- Navigates to Google Trends URL for the specific DMA
- Waits for network to be idle (page fully loaded)

### 3. **Page Interaction**
```python
# Wait and refresh
await asyncio.sleep(5)
await page.reload(wait_until="networkidle")
await asyncio.sleep(10)

# Click export button
export_button_xpath = "//button[descendant::span[contains(text(), 'Export')]]"
await page.wait_for_selector(export_button_xpath, timeout=20000)
await page.click(export_button_xpath)
```
- Waits for page to stabilize
- Refreshes to ensure fresh data
- Clicks the export button

### 4. **Download CSV**
```python
download_csv_xpath = "/html/body/c-wiz/div/div[5]/div[1]/c-wiz/div/div[1]/div[3]/div[2]/div[2]/div/div[2]/div/div/ul/li[1]"
await page.wait_for_selector(download_csv_xpath, timeout=10000)
await page.click(download_csv_xpath)
```
- Clicks the CSV download option
- Automatically downloads to the configured directory

### 5. **Data Processing**
```python
df = pd.read_csv(latest_file, skiprows=1)
for index, row in df.iterrows():
    trend_topic = row.iloc[0] 
    trends_data.append({
        "dma_code": dma_code,
        "dma_name": dma_name,
        "trend": trend_topic,
        "run_time": now.strftime("%Y-%m-%d %H:%M")
    })
```
- Reads the downloaded CSV file
- Extracts trending topics
- Structures the data

## How Claude Uses These Tools

### Example Conversation Flow:

1. **Claude asks for available locations:**
   ```
   "What locations can I get Google Trends data for?"
   ```

2. **Claude calls the tool:**
   ```python
   result = await get_available_trends_locations()
   ```

3. **System responds:**
   ```
   Available locations: [
     {'code': 807, 'name': 'San Francisco (SFO)'},
     {'code': 803, 'name': 'Los Angeles (LAX)'},
     {'code': 602, 'name': 'Chicago (ORD)'},
     {'code': 524, 'name': 'Atlanta (ATL)'},
     {'code': 623, 'name': 'Dallas (DFW)'},
     {'code': 751, 'name': 'Denver (DEN)'},
     {'code': 501, 'name': 'New York (JFK)'},
     {'code': 819, 'name': 'Seattle (SEA)'},
     {'code': 506, 'name': 'Boston (BOS)'},
     {'code': 528, 'name': 'Miami (MIA)'}
   ]
   ```

4. **Claude requests trends for Chicago:**
   ```
   "Please get the current trending topics for Chicago."
   ```

5. **Claude calls the scraping tool:**
   ```python
   result = await scrape_google_trends(602, "Chicago (ORD)")
   ```

6. **System returns formatted data:**
   ```
   Successfully scraped trends for Chicago (ORD):
   
   Trending topics:
   1. Taylor Swift
   2. NFL Playoffs
   3. Chicago Bears
   4. Weather Alert
   5. Local News
   ...
   
   Total: 25 trending topics
   Scraped at: 2025-01-20 15:30
   ```

## Advantages of Using Playwright

### 1. **Better Reliability**
- Playwright is more modern and reliable than Selenium
- Better handling of dynamic content
- Built-in waiting mechanisms

### 2. **Async/Await Support**
- Native async support for better performance
- Non-blocking operations
- Better resource management

### 3. **Multiple Browser Support**
- Can use Chromium, Firefox, or WebKit
- Better cross-browser compatibility
- More stable automation

### 4. **Built-in Tools**
- Screenshot capabilities
- Network monitoring
- Better error handling

## File Structure

```
mcp_project/
├── playwright/
│   ├── server.py                    # Main Playwright server with trends tools
│   └── TRENDS_INTEGRATION_GUIDE.md  # This guide
├── downloads/                       # Downloaded CSV files
└── dependencies/                    # Browser dependencies
```

## Testing the Integration

### 1. **Start the Playwright Server:**
```bash
cd mcp_project/playwright
python server.py
```

### 2. **Test Individual Tools:**
```python
# Test getting available locations
result = await get_available_trends_locations()
print(result)

# Test scraping for Chicago
result = await scrape_google_trends(602, "Chicago (ORD)")
print(result)

# Test scraping all locations
result = await scrape_all_trends_locations()
print(result)
```

## Error Handling

The integration includes comprehensive error handling:

1. **Network Timeouts:** Waits for elements with timeouts
2. **Missing Files:** Checks if CSV files were downloaded
3. **Browser Issues:** Handles browser initialization errors
4. **Data Processing:** Handles CSV parsing errors

## Performance Considerations

1. **Headless Mode:** Runs without visible browser for speed
2. **Async Operations:** Non-blocking for better performance
3. **Resource Cleanup:** Properly closes browser instances
4. **Rate Limiting:** Small delays between requests

## Security and Privacy

1. **Headless Operation:** No visible browser activity
2. **Temporary Files:** CSV files are cleaned up after processing
3. **Public Data Only:** Only accesses publicly available Google Trends data
4. **No User Data:** No personal information is collected

## Future Enhancements

1. **More Locations:** Easy to add new DMA locations
2. **Custom Time Ranges:** Could add support for different time periods
3. **Data Storage:** Could integrate with databases
4. **Real-time Updates:** Could add scheduling capabilities

## Troubleshooting

### Common Issues:

1. **"No CSV file found"**
   - Check download directory permissions
   - Verify browser automation is working
   - Check network connectivity

2. **"TimeoutException"**
   - Google Trends might be slow
   - Increase timeout values
   - Check internet connection

3. **"Failed to process"**
   - Verify DMA code is valid
   - Check Playwright installation
   - Review error logs

This integration provides Claude with powerful, reliable tools for scraping Google Trends data using modern browser automation technology. 