# oil_mcp_client.py

import requests
import sqlite3
import time
from datetime import datetime
import asyncio

API_TOKEN = "113482992bb97eb41f34ca5cb227fe840631df5faa2eb4f11fc5deb6bfa078ef"
BASE_URL = "https://api.oilpriceapi.com/v1/prices/past_year"
CODES = ["WTI_USD", "BRENT_CRUDE_USD"]

HOST = '127.0.0.1'
PORT = 1234

def fetch_prices(code):
    headers = {"Authorization": f"Token {API_TOKEN}"}
    params = {"by_code": code}
    resp = requests.get(BASE_URL, headers=headers, params=params)
    resp.raise_for_status()
    return resp.json()["data"]["prices"]

def init_db(db_path="oil_prices.db"):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS oil_prices (
        id INTEGER PRIMARY KEY,
        code TEXT,
        price REAL,
        timestamp INTEGER,
        created_at TEXT
    )""")
    conn.commit()
    return conn

def save_prices(conn, code, prices):
    c = conn.cursor()
    for entry in prices:
        c.execute("""
        INSERT OR IGNORE INTO oil_prices (code, price, timestamp, created_at)
        VALUES (?, ?, ?, ?)
        """, (
            code,
            entry["price"],
            int(datetime.fromisoformat(entry["created_at"].rstrip('Z')).timestamp()),
            entry["created_at"]
        ))
    conn.commit()

async def send_mcp_message(writer, package, content):
    message = f"#$#{package} {content}\n"
    writer.write(message.encode())
    await writer.drain()

async def mcp_client(oil_data):
    reader, writer = await asyncio.open_connection(HOST, PORT)

    # Send MCP version negotiation
    await send_mcp_message(writer, "mcp", "version: 2.1 to: 2.1")

    # Send mock auth
    await send_mcp_message(writer, "mcp-auth", "type: client id: oil_script")

    # Send oil data
    for entry in oil_data:
        code = entry["code"]
        price = entry["price"]
        ts = entry["created_at"]
        await send_mcp_message(writer, "oil-data", f":code={code} :price={price} :created_at={ts}")

    writer.close()
    await writer.wait_closed()

def main():
    conn = init_db()
    all_data = []
    for code in CODES:
        print(f"Fetching {code}…")
        data = fetch_prices(code)
        print(f"  Retrieved {len(data)} records")
        save_prices(conn, code, data)
        for entry in data:
            entry["code"] = code
            all_data.append(entry)
        time.sleep(1)
    conn.close()

    asyncio.run(mcp_client(all_data))

if __name__ == "__main__":
    main()
