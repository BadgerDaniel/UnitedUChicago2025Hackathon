#!/usr/bin/env python3
"""Test script to verify DuckDB connection and basic queries."""

import os
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.append(str(Path(__file__).parent.parent.parent))

# Test 1: Check if database exists
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "static.duckdb")
print(f"1. Checking database path: {db_path}")
print(f"   Database exists: {os.path.exists(db_path)}")

# Test 2: Try to connect to DuckDB directly
try:
    import duckdb
    print("\n2. Testing DuckDB connection...")
    conn = duckdb.connect(db_path, read_only=True)
    print("   ✓ Connected to DuckDB successfully")
    
    # Test 3: List tables
    print("\n3. Listing tables...")
    tables = conn.execute("SHOW TABLES").fetchall()
    for table in tables:
        print(f"   - {table[0]}")
    
    # Test 4: Check table schemas
    print("\n4. Checking table schemas...")
    for table_name in ['city', 'nearest_airport', 'route', 'flight', 'weather']:
        print(f"\n   Table: {table_name}")
        schema = conn.execute(f"DESCRIBE {table_name}").fetchall()
        for col in schema[:3]:  # Show first 3 columns
            print(f"     - {col[0]}: {col[1]}")
    
    # Test 5: Sample queries
    print("\n5. Testing sample queries...")
    
    # Count cities
    city_count = conn.execute("SELECT COUNT(*) FROM city").fetchone()[0]
    print(f"   - Number of cities: {city_count}")
    
    # Sample cities
    print("   - Sample cities:")
    cities = conn.execute("SELECT city_name FROM city LIMIT 5").fetchall()
    for city in cities:
        print(f"     • {city[0]}")
    
    # Count flights
    flight_count = conn.execute("SELECT COUNT(*) FROM flight").fetchone()[0]
    print(f"   - Number of flights: {flight_count}")
    
    # Sample route with prices
    print("\n6. Testing route query (Chicago to London)...")
    query = """
    SELECT 
        c1.city_name as origin,
        c2.city_name as destination,
        f.departure_date,
        f.price_quartile_middle as avg_price
    FROM flight f
    JOIN route r ON f.route_id = r.id
    JOIN nearest_airport na1 ON r.depar_airport_id = na1.id
    JOIN nearest_airport na2 ON r.desti_airport_id = na2.id
    JOIN city c1 ON na1.city_id = c1.id
    JOIN city c2 ON na2.city_id = c2.id
    WHERE c1.city_name = 'Chicago' 
    AND c2.city_name = 'London'
    ORDER BY f.departure_date DESC
    LIMIT 5
    """
    results = conn.execute(query).fetchall()
    if results:
        print("   Found routes:")
        for row in results:
            print(f"     {row[0]} → {row[1]} on {row[2]}: ${row[3]}")
    else:
        print("   No routes found for Chicago to London")
    
    conn.close()
    print("\n✅ All database tests passed!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()