import asyncio
import sqlite3
import os
import time
import pandas as pd
import glob
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException

clients = []

oil_db_path = os.path.join(os.path.dirname(__file__), '..', 'MCP_ds', 'oil_prices.db')

# --- Trends Scraping Configuration ---
cwd = os.getcwd()
dependencies_dir = os.path.join(cwd, "dependencies")
download_dir = os.path.join(cwd, "mcp_project", "downloads")
os.makedirs(download_dir, exist_ok=True)

driver_path = os.path.join(dependencies_dir, "geckodriver.exe")
service_log_path = os.path.join(dependencies_dir, "geckodriver.log")
firefox_path = os.path.join(dependencies_dir, 'FF_Portable', 'App', 'Firefox64', 'firefox.exe')

# --- Available DMA Targets ---
DMA_TARGETS = [
    {"dma_code": 524, "dma_name": "Atlanta (ATL)"},
    {"dma_code": 803, "dma_name": "Los Angeles (LAX)"},
    {"dma_code": 623, "dma_name": "Dallas (DFW)"},
    {"dma_code": 751, "dma_name": "Denver (DEN)"},
    {"dma_code": 602, "dma_name": "Chicago (ORD)"},
]

BASE_URL = "https://trends.google.com/trending?geo={dma}&hours=24&sort=search-volume"

def get_latest_oil_price(code):
    try:
        conn = sqlite3.connect(oil_db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT price, created_at FROM oil_prices
            WHERE code = ?
            ORDER BY timestamp DESC LIMIT 1
        """, (code,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return row[0], row[1]
        else:
            return None, None
    except Exception as e:
        print(f"DB error: {e}")
        return None, None

def get_available_locations():
    """Return list of available DMA locations for trends scraping."""
    return [{"code": target["dma_code"], "name": target["dma_name"]} for target in DMA_TARGETS]

def scrape_trends_for_location(dma_code, dma_name):
    """Scrape Google Trends data for a specific DMA location."""
    now = datetime.now()
    trends_data = []
    
    # Clean the download directory before starting
    for f in os.listdir(download_dir):
        try:
            os.remove(os.path.join(download_dir, f))
        except:
            pass  # Skip files that can't be removed
    
    # --- Selenium Setup ---
    firefox_options = Options()
    firefox_options.binary_location = firefox_path
    firefox_options.add_argument('--headless')
    firefox_options.set_preference("browser.download.folderList", 2)
    firefox_options.set_preference("browser.download.dir", os.path.abspath(download_dir))
    firefox_options.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/csv")
    
    firefox_service = FirefoxService(executable_path=driver_path, log_output=service_log_path)
    driver = webdriver.Firefox(service=firefox_service, options=firefox_options)
    
    try:
        url = BASE_URL.format(dma=dma_code)
        print(f"\n📡 Processing DMA: {dma_name}")
        driver.get(url)

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
            return {"error": f"No CSV file found for {dma_name}"}

        latest_file = max(list_of_files, key=os.path.getctime)
        
        # --- Data Cleaning and Processing ---
        df = pd.read_csv(latest_file, skiprows=1)
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
    finally:
        driver.quit()

async def handle_client(reader, writer):
    addr = writer.get_extra_info('peername')
    clients.append(writer)
    print(f"🟢 Client connected: {addr}")

    while True:
        data = await reader.readline()
        if not data:
            break

        message = data.decode().strip()
        print(f"📨 {addr} → {message}")

        if message.startswith("#$#"):
            await handle_mcp(message, writer)
        else:
            for client in clients:
                if client != writer:
                    client.write(f"{addr}: {message}\n".encode())
                    await client.drain()

    print(f"🔴 Client disconnected: {addr}")
    clients.remove(writer)
    writer.close()

async def handle_mcp(message, writer):
    # Remove #$# prefix and split package from params
    parts = message[3:].strip().split(" ", 1)
    package = parts[0]
    params_str = parts[1] if len(parts) > 1 else ""

    if package in ["mcp", "mcp-auth"]:
        # Acknowledge control messages
        print(f"📦 MCP control message: {package} | {params_str}")

    elif package in ["oil-data", "trend-data"]:
        # Handle ":key=value" format, which is more complex
        fields = {}
        # A simple parsing logic for this specific format
        # It splits by space and then by '='
        pairs = params_str.strip().split(" ")
        for pair in pairs:
            if '=' in pair:
                # remove leading colon if it exists
                if pair.startswith(':'):
                    pair = pair[1:]
                key, value = pair.split('=', 1)
                # Remove quotes from value if they exist
                fields[key] = value.strip('"')

        if package == "oil-data":
            print(f"🛢️ OIL → {fields}")
        elif package == "trend-data":
            print(f"🔥 TREND → {fields}")

    elif package == "get-oil-price":
        # Parse params for code
        code = None
        pairs = params_str.strip().split(" ")
        for pair in pairs:
            if pair.startswith(":code="):
                code = pair.split("=", 1)[1]
        if code:
            price, timestamp = get_latest_oil_price(code)
            if price is not None:
                response = f"#$#oil-price-result :code={code} :price={price} :timestamp={timestamp}\n"
            else:
                response = f"#$#oil-price-result :code={code} :error=not_found\n"
            writer.write(response.encode())
            await writer.drain()
        else:
            response = f"#$#oil-price-result :error=missing_code\n"
            writer.write(response.encode())
            await writer.drain()
    
    elif package == "get-available-locations":
        # Return list of available DMA locations
        locations = get_available_locations()
        locations_str = " ".join([f":code={loc['code']} :name=\"{loc['name']}\"" for loc in locations])
        response = f"#$#available-locations {locations_str}\n"
        writer.write(response.encode())
        await writer.drain()
    
    elif package == "scrape-trends":
        # Parse params for dma_code
        dma_code = None
        dma_name = None
        pairs = params_str.strip().split(" ")
        for pair in pairs:
            if pair.startswith(":dma_code="):
                dma_code = pair.split("=", 1)[1]
            elif pair.startswith(":dma_name="):
                dma_name = pair.split("=", 1)[1].strip('"')
        
        if dma_code and dma_name:
            print(f"🔥 Starting trends scrape for {dma_name} (DMA: {dma_code})")
            result = scrape_trends_for_location(int(dma_code), dma_name)
            
            if "error" in result:
                response = f"#$#trends-result :error=\"{result['error']}\"\n"
            else:
                # Send the trends data
                trends_str = ""
                for trend in result["trends"]:
                    trends_str += f" :dma_code={trend['dma_code']} :dma_name=\"{trend['dma_name']}\" :trend=\"{trend['trend']}\" :run_time=\"{trend['run_time']}\""
                
                response = f"#$#trends-result :success=true :location=\"{result['location']}\" :trends_count={result['trends_count']} :timestamp=\"{result['timestamp']}\"{trends_str}\n"
            
            writer.write(response.encode())
            await writer.drain()
        else:
            response = f"#$#trends-result :error=missing_dma_code_or_name\n"
            writer.write(response.encode())
            await writer.drain()
    
    else:
        print(f"❓ Unrecognized MCP package: {package} | Params: {params_str}")

async def main():
    server = await asyncio.start_server(handle_client, '0.0.0.0', 1234)
    addr = server.sockets[0].getsockname()
    print(f"🌐 MCP Server running on {addr}")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main()) 