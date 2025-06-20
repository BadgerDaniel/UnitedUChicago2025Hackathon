import sqlite3

conn = sqlite3.connect('MCP_ds/oil_prices.db')
cursor = conn.cursor()

# Check tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:", tables)

# Check schema for oil_prices table
cursor.execute("PRAGMA table_info(oil_prices)")
schema = cursor.fetchall()
print("Schema:", schema)

# Check sample data
cursor.execute("SELECT * FROM oil_prices LIMIT 5")
sample_data = cursor.fetchall()
print("Sample data:", sample_data)

conn.close() 