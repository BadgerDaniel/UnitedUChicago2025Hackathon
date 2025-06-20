import os
import requests
import time
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

# DMA list with airport & DMA code
dma_targets = [
    {"dma_code": 524, "dma_name": "Atlanta (Hartsfield‑Jackson ATL)"},
    {"dma_code": 803, "dma_name": "Los Angeles (LAX)"},
    {"dma_code": 623, "dma_name": "Dallas–Fort Worth (DFW)"},
    {"dma_code": 751, "dma_name": "Denver (DEN)"},
    {"dma_code": 602, "dma_name": "Chicago (O’Hare)"},
    {"dma_code": 534, "dma_name": "Orlando (MCO)"},
    {"dma_code": 517, "dma_name": "Charlotte (CLT)"},
    {"dma_code": 839, "dma_name": "Las Vegas (LAS)"},
    {"dma_code": 819, "dma_name": "Seattle (SEA)"},
    {"dma_code": 528, "dma_name": "Miami (MIA)"},
    {"dma_code": 753, "dma_name": "Phoenix (PHX)"},
    {"dma_code": 807, "dma_name": "San Francisco (SFO)"},
    {"dma_code": 501, "dma_name": "New York Metro (EWR/JFK/LGA)"},
    {"dma_code": 618, "dma_name": "Houston (IAH)"},
    {"dma_code": 506, "dma_name": "Boston (BOS)"}
]


# Base URL
base_url = "https://trends.google.com/trending?geo={dma}&hours=24&sort=search-volume"

# Output list
all_trends = []

# Determine date + part of day (AM or PM)
now = datetime.now()
date_str = now.strftime("%Y-%m-%d")
part_of_day = "AM" if now.hour < 12 else "PM"

# Create folder path
folder_path = os.path.join("trends", date_str)
os.makedirs(folder_path, exist_ok=True)

# Start scraping
for target in dma_targets:
    dma_code = target["dma_code"]
    dma_name = target["dma_name"]
    url = base_url.format(dma=dma_code)

    print(f"Fetching for {dma_name} (DMA {dma_code})...")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Parse trending topics
        trends = soup.find_all("div", class_="title")

        for t in trends:
            all_trends.append({
                "DMA Code": dma_code,
                "DMA Name": dma_name,
                "Trend": t.get_text(strip=True),
                "Run Time": now.strftime("%Y-%m-%d %H:%M")
            })

        # Healthy, generous delay
        delay = 10 + (dma_code % 5)
        print(f"Sleeping {delay}s...\n")
        time.sleep(delay)

    except Exception as e:
        print(f"Failed to fetch {dma_name}: {e}")
        continue

# Save file with AM/PM tag
filename = os.path.join(folder_path, f"dma_trending_topics_{part_of_day}.csv")
pd.DataFrame(all_trends).to_csv(filename, index=False)
print(f"Done! Results saved to '{filename}'")
