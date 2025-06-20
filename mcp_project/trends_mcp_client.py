import os
import requests
import time
from bs4 import BeautifulSoup
from datetime import datetime
import asyncio
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

HOST = '127.0.0.1'
PORT = 1234

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

async def send_trends(all_trends):
    reader, writer = await asyncio.open_connection(HOST, PORT)

    await send_mcp_message(writer, "mcp", "version: 2.1 to: 2.1")
    await send_mcp_message(writer, "mcp-auth", "type: client id: trend_scraper")

    for trend in all_trends:
        await send_mcp_message(writer, "trend-data",
            f":dma_code={trend['dma_code']} :dma_name=\"{trend['dma_name']}\" :trend=\"{trend['Trend']}\" :run_time=\"{trend['Run Time']}\"")

    writer.close()
    await writer.wait_closed()

def scrape_trends():
    now = datetime.now()
    all_trends = []

    for target in dma_targets:
        dma_code = target["dma_code"]
        dma_name = target["dma_name"]
        url = base_url.format(dma=dma_code)

        print(f"📡 Fetching for {dma_name} (DMA {dma_code})...")

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            trends = soup.find_all("div", class_="title")

            for t in trends:
                all_trends.append({
                    "dma_code": dma_code,
                    "dma_name": dma_name,
                    "Trend": t.get_text(strip=True),
                    "Run Time": now.strftime("%Y-%m-%d %H:%M")
                })
            
            delay = 10 + (dma_code % 5)
            print(f"⏳ Sleeping {delay}s...\n")
            time.sleep(delay)

        except Exception as e:
            print(f"⚠️ Failed to fetch {dma_name}: {e}")
            continue
            
    if not all_trends:
        print("⚠️ No trends were scraped. The Google Trends page structure may have changed or the request was blocked.")
        
    return all_trends

def main():
    trends = scrape_trends()
    asyncio.run(send_trends(trends))

if __name__ == "__main__":
    main() 