## this script write out data to duckdb
import pandas as pd
import duckdb as dd



# load all data we need
df_city = pd.read_csv('data/intermediate/city.csv')
df_weather = pd.read_csv('data/intermediate/weather.csv')
df_iata = pd.read_csv('data/intermediate/city_airport.csv')
routes_df = pd.read_csv('data/intermediate/routes.csv')
df_flight = pd.read_csv('data/intermediate/flight_month.csv')

# create a duckdb object

con = dd.connect('data/static.duckdb')

# # optional: clear database
# drop_order = ["flight", "weather", "route", "nearest_airport", "city"]
# for table_name in drop_order:
#     con.execute(f"DROP TABLE IF EXISTS {table_name}")

# Read SQL schema from file
with open("schema/static.sql", "r") as f:
    sql_script = f.read()

# Execute the schema to build tables
con.execute(sql_script)
# drop a useless table
con.execute("DROP TABLE IF EXISTS location")

# Verify tables were created
print(con.execute("SHOW TABLES").fetchdf())


## insert city info
# Register and insert into the location table
con.register("df_city", df_city)
con.execute("INSERT INTO city (id, city_name) SELECT id, city_name FROM df_city")

con.execute("PRAGMA table_info('city')").fetchdf()

### insert weather data
con.register("df_weather", df_weather)
con.execute("INSERT INTO weather SELECT * FROM df_weather")
con.execute("PRAGMA table_info('weather')").fetchdf()

### insert airport data
con.register("df_iata", df_iata)
con.execute("INSERT INTO nearest_airport SELECT * FROM df_iata")
con.execute("PRAGMA table_info('nearest_airport')").fetchdf()

### insert route data
con.register("routes_df", routes_df)
con.execute("INSERT INTO route SELECT * FROM routes_df")
con.execute("PRAGMA table_info('route')").fetchdf()

### insert flight data
con.register("df_flight", df_flight)
con.execute("INSERT INTO flight SELECT * FROM df_flight")
con.execute("PRAGMA table_info('flight')").fetchdf()

# preview database
tables = con.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()

for (table_name,) in tables:
    print(f"Table: {table_name}")
    rows = con.execute(f"SELECT * FROM {table_name} LIMIT 3").fetchdf()
    print(rows)
    print("\n" + "-"*40 + "\n")

# end the database
con.commit()  # Optional, but ensures changes are flushed
con.close()   # Closes the DB and safely handles the WAL