#!/usr/bin/env python3
"""Explore the DuckDB data to understand available routes."""

import os
import sys
from pathlib import Path
import duckdb

# Database path
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "static.duckdb")
conn = duckdb.connect(db_path, read_only=True)

print("1. Cities in database:")
cities = conn.execute("SELECT id, city_name FROM city ORDER BY city_name").fetchall()
for city_id, city_name in cities:
    print(f"   {city_id}: {city_name}")

print("\n2. Airports:")
airports = conn.execute("""
    SELECT na.id, na.iata_code, c.city_name 
    FROM nearest_airport na
    JOIN city c ON na.city_id = c.id
    ORDER BY c.city_name
""").fetchall()
for airport_id, iata, city in airports:
    print(f"   {airport_id}: {iata} ({city})")

print("\n3. Available routes:")
routes = conn.execute("""
    SELECT 
        r.id as route_id,
        c1.city_name as origin,
        na1.iata_code as origin_code,
        c2.city_name as destination,
        na2.iata_code as dest_code
    FROM route r
    JOIN nearest_airport na1 ON r.depar_airport_id = na1.id
    JOIN nearest_airport na2 ON r.desti_airport_id = na2.id
    JOIN city c1 ON na1.city_id = c1.id
    JOIN city c2 ON na2.city_id = c2.id
    ORDER BY c1.city_name, c2.city_name
    LIMIT 20
""").fetchall()
for route_id, origin, origin_code, dest, dest_code in routes:
    print(f"   Route {route_id}: {origin} ({origin_code}) → {dest} ({dest_code})")

print("\n4. Sample flight prices (Los Angeles to Chicago):")
prices = conn.execute("""
    SELECT 
        f.departure_date,
        f.price_quartile_minimum as min_price,
        f.price_quartile_middle as avg_price,
        f.price_quartile_maximum as max_price
    FROM flight f
    JOIN route r ON f.route_id = r.id
    JOIN nearest_airport na1 ON r.depar_airport_id = na1.id
    JOIN nearest_airport na2 ON r.desti_airport_id = na2.id
    JOIN city c1 ON na1.city_id = c1.id
    JOIN city c2 ON na2.city_id = c2.id
    WHERE c1.city_name = 'los angeles' 
    AND c2.city_name = 'chicago'
    ORDER BY f.departure_date DESC
    LIMIT 5
""").fetchall()
if prices:
    print("   Date         Min    Avg    Max")
    for date, min_p, avg_p, max_p in prices:
        print(f"   {date}  ${min_p:>4}  ${avg_p:>4}  ${max_p:>4}")
else:
    print("   No flights found for this route")

conn.close()