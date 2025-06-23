# run this script to call API and write out city, route, weather, flight and airport table
import os
from datetime import datetime, timedelta, timezone
import pandas as pd
from amadeus import Client, ResponseError
import time
import requests
from requests.exceptions import RequestException, ConnectionError
from itertools import permutations


# load env
weather_api = os.getenv('OpenWeatherMap_API')
price_api = os.getenv('AMADEUS_API_KEY')
price_secret = os.getenv('AMADEUS_SECRET')

## functions
def is_alert(code: int) -> bool:
    """
    Returns True if the weather condition code should trigger an alert, False otherwise.
    Optionally uses the description for more granularity.
    """

    # Thunderstorms (Group 2xx)
    if 200 <= code <= 232:
        return True  # All thunderstorms are potentially hazardous

    # Drizzle (Group 3xx)
    if 300 <= code <= 321:
        return False  # Generally light, not hazardous

    # Rain (Group 5xx)
    if code in {502, 503, 504, 511, 522, 531}:
        return True  # Heavy, extreme, or freezing rain
    elif 500 <= code <= 531:
        return False  # Light/moderate rain usually not alert-level

    # Snow (Group 6xx)
    if code in {602, 622, 616, 613, 620}:
        return True  # Heavy or mixed snow/ice conditions
    elif 600 <= code <= 622:
        return False  # Light snow/sleet usually advisory only

    # Atmosphere (Group 7xx)
    if code in {741, 762, 771, 781}:
        return True  # Fog, ash, squalls, tornado
    elif 700 <= code <= 781:
        return False  # Mist, haze, etc.

    # Clear & Clouds (Group 800-804)
    if code == 800:
        return False
    if 801 <= code <= 804:
        return False  # Cloud cover, no hazard

    return False  # Default to non-alert if unknown


def get_city_id(df):
    '''
    Find city based on coord
    '''
    def find_city(lat, lon, lookup):
        target = (lat, lon)
        return next((k for k, v in lookup.items() if v == target), None)
    
    city_to_id = dict(zip(df_city['city_name'], df_city['id']))
    df['city'] = df.apply(lambda row: find_city(row["lat"], row["lon"], city_coords), axis=1)
    df['city_id'] = df['city'].map(city_to_id)
    df = df.drop(columns='city')

    return df

def call_weather_api():
    '''
    Call weather api at a fair rate
    '''

    MAX_CALLS_PER_MINUTE = 60
    MAX_TOTAL_CALLS = 1000
    SECONDS_BETWEEN_CALLS = 60 / MAX_CALLS_PER_MINUTE  # 1.0 seconds

    total_calls = 0
    start_time = time.time()
    df_w = pd.DataFrame()  # Initialize your result dataframe

    try:
        for index, row in df_coord_time[501:514].iterrows():
            if total_calls >= MAX_TOTAL_CALLS:
                print("Reached total API call limit (1000).")
                break

            lat = row['lat']
            lon = row['lon']
            timestamp = row['timestamp']
            url = f"https://api.openweathermap.org/data/3.0/onecall/timemachine?lat={lat}&lon={lon}&dt={timestamp}&appid={weather_api}"

            try:
                response = requests.get(url, timeout=10)
                total_calls += 1

                if response.status_code == 200:
                    data_w = response.json()
                    print(index, data_w)

                    weather_list = data_w['data'][0]['weather']
                    records = [{
                        'lat': data_w['lat'],
                        'lon': data_w['lon'],
                        'date': data_w['data'][0]['dt'],
                        'weather_id': w['id'],
                        'weather': w['main']
                    } for w in weather_list]

                    df_w = pd.concat([df_w, pd.DataFrame(records)], ignore_index=True)

                else:
                    print("Error:", response.status_code, response.text)

                time.sleep(SECONDS_BETWEEN_CALLS)

            except (ConnectionError, RequestException) as e:
                print(f"⚠️ Request failed at index {index}: {e}")
                break

    except Exception as e:
        print(f"🚨 Fatal error during loop: {e}")
    
    return df_w


def process_weather(df_w):
    '''
    Edit weather table to desirable format
    '''
    df_weather = df_w.copy()
    df_weather['date'] = pd.to_datetime(df_w['date'], unit='s').dt.strftime('%Y-%m-%d')
    df_weather['alert'] = df_weather['weather_id'].apply(lambda x: is_alert(x))
    df_weather = get_city_id(df_weather)

    df_weather['id'] = range(1, len(df_weather)+1)

    df_weather = df_weather.drop(['lat', 'lon'], axis=1)

    # adjusted order
    desired_order = ['id', 'date', 'city_id', 'weather_id', 'weather', 'alert']
    df_weather = df_weather[desired_order]

    df_weather

def call_airport_api():
    # city - airport
    iata_results = []


    for city, (lat, lon) in city_coords.items():
        try:
            response = amadeus.reference_data.locations.airports.get(latitude=lat, longitude=lon)
            if response.data:
                nearest = response.data[0]
                iata_results.append({
                    "iata_code": nearest["iataCode"]
                })
            
        except Exception as e:
            print(f"Failed for {city}: {e}")

    return iata_results


def process_airport(iata_results):
    '''
    Convert response to correct format
    '''
    df_iata = pd.DataFrame(iata_results)
    df_iata['city_id'] = range(1, len(df_iata)+1)
    df_iata['id'] = range(1, len(df_iata)+1)
    desired_order = ['id', 'iata_code', 'city_id']
    df_iata = df_iata[desired_order]

    # encode dc airport to united hub
    df_iata.loc[6, 'iata_code'] = 'IAD'
    return df_iata


def create_routes():
    routes = list(permutations(df_iata["id"], 2))

    # Convert to DataFrame
    routes_df = pd.DataFrame(routes, columns=["depar_airport_id", "desti_airport_id"])

    # Optional: Add a unique route_id (if you'll insert into SQL table)
    routes_df["id"] = range(1, len(routes_df) + 1)
    desired_order = ['id', "depar_airport_id", "desti_airport_id"]
    routes_df = routes_df[desired_order]

    return routes_df


def airport_to_route(df):
    # Create mapping from IATA to airport ID
    iata_to_id = df_iata.set_index('iata_code')['id'].to_dict()

    # Map airport IDs to flights
    df['depar_airport_id'] = df['origin'].map(iata_to_id)
    df['arrival_airport_id'] = df['destination'].map(iata_to_id)

    # Create route lookup: {(depart_id, arrive_id): route_id}
    route_lookup = {
        (row['depar_airport_id'], row['desti_airport_id']): row['id']
        for _, row in routes_df.iterrows()
    }

    # Apply to get route_id
    df['route_id'] = df.apply(
        lambda row: route_lookup.get((row['depar_airport_id'], row['arrival_airport_id'])),
        axis=1
    )
    print(df)
    return(df)

def generate_routes_set(col):
    '''
    generate all routes combination based on airports
    
    '''
    airport_route = pd.DataFrame(list(permutations(col, 2)))
    # airport_route

    dates = pd.date_range(start="2025-01-01", end="2025-06-30", freq="M", tz="UTC")
    df_dates = pd.DataFrame(dates)

    route_dates = airport_route.merge(df_dates, how="cross")
    route_dates.columns = ['departure_iata', 'arrival_iata', 'departure_date']
    route_dates['departure_date'] = pd.to_datetime(route_dates['departure_date']).dt.strftime('%Y-%m-%d')
    route_dates['id'] = range(1, len(route_dates)+1)

    return route_dates


def call_flight_api(route_dates):
    '''
    call flights based on parameter in route dates
    '''
    

    MAX_CALLS_PER_MIN = 20
    SECONDS_BETWEEN_CALLS = 60 / MAX_CALLS_PER_MIN  # 3 seconds
    MAX_TOTAL_CALLS = 2000

    response_data = []
    call_count = 0

    for index, route in route_dates.iterrows():
        if call_count >= MAX_TOTAL_CALLS:
            print("Reached monthly API call limit (2000). Stopping.")
            break

        departure_iata = route['departure_iata']
        arrival_iata = route['arrival_iata']
        departure_date = route['departure_date']

        try: 
            response = amadeus.analytics.itinerary_price_metrics.get(
                originIataCode=departure_iata, 
                destinationIataCode=arrival_iata,
                departureDate=departure_date,
                currencyCode="USD"
            )

            call_count += 1

            if response.data:
                response_data.append(response.data[0])
                print(index, response.data[0])
            else:
                print(f'No data for {departure_iata} to {arrival_iata} on {departure_date}')

            # Respect per-minute rate limit
            time.sleep(SECONDS_BETWEEN_CALLS)

        except ResponseError as error:
            if hasattr(error, 'response') and error.response.status_code == 429:
                retry_after = int(error.response.headers.get("Retry-After", 60))
                print(f"429 Rate Limit hit. Retrying after {retry_after} seconds.")
                time.sleep(retry_after)
            else:
                print(f"Error for {departure_iata} to {arrival_iata} on {departure_date}. ")
    
    # Quartile label mapping
    quartile_map = {
        "MINIMUM": "price_quantile_minimum",
        "FIRST": "price_quantile_low",
        "MEDIUM": "price_quantile_middle",
        "THIRD": "price_quantile_high",
        "MAXIMUM": "price_quantile_maximum"
    }

    rows = []
    for item in response_data:
        row = {
            "origin": item['origin']['iataCode'],
            "destination": item['destination']['iataCode'],
            "departure_date": item['departureDate']
        }
        for metric in item['priceMetrics']:
            key = quartile_map.get(metric['quartileRanking'])
            row[key] = float(metric['amount'])
            
        rows.append(row)

    df_f = pd.DataFrame(rows)

    return df_f


def process_flight(df_f):
    df_flight = airport_to_route(df_f)
    df_flight = df_flight.iloc[:, 2:]
    df_flight['departure_date'] = pd.to_datetime(df_flight['departure_date'])
    df_flight['id'] = range(1, len(df_flight)+1)
    desired_order = ['id', 'route_id', 'departure_date', 'price_quantile_minimum', 'price_quantile_low', 'price_quantile_middle', 'price_quantile_high', 'price_quantile_maximum']
    df_flight = df_flight[desired_order]
    # print(df_flight)
    return df_flight

# select cities range
city_coords = {
    "los angeles": (34.0522, -118.2437),
    "chicago": (41.8781, -87.6298),
    "houston": (29.7604, -95.3698),
    "denver": (39.7392, -104.9903),
    "newark": (40.7357, -74.1724),
    "san francisco": (37.7749, -122.4194),
    "washington dc": (38.9072, -77.0369),
 
}


## generate city 
df_city = pd.DataFrame({
    'id': range(1, len(city_coords)+1),
    'city_name': city_coords.keys()})


print(df_city)


# select time range 2025-01-01 to 2025-06-30
# Start and end dates
start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
end_date = datetime(2025, 6, 22, tzinfo=timezone.utc)

# Generate list of timestamps at 00:00:00 UTC each day
timestamps = []
current_date = start_date
while current_date <= end_date:
    timestamps.append(int(current_date.timestamp()))
    current_date += timedelta(days=1)

print(timestamps)

# Create DataFrames for city*date
# extract coords
coords = [value for key, value in city_coords.items()]

df_coords = pd.DataFrame(coords, columns=["lat", "lon"])
df_times = pd.DataFrame(timestamps, columns=["timestamp"])

# Add keys to enable cartesian join
df_coords["key"] = 1
df_times["key"] = 1

# Cartesian product via merge
df_coord_time = pd.merge(df_coords, df_times, on="key").drop("key", axis=1)

# Optional: convert timestamp to readable date
df_coord_time["datetime"] = pd.to_datetime(df_coord_time["timestamp"], unit="s")

print(df_coord_time)

## create weather table
df_w = call_weather_api()
df_weather = process_weather(df_w)

print(df_weather)

## create airport table
amadeus = Client(
    client_id=price_api,
    client_secret=price_secret
)

iata_results = call_airport_api()
df_iata = process_airport(iata_results)

print(df_iata)

## create routes table
routes_df = create_routes()
print(routes_df)


## create flight table

routes_date = generate_routes_set(df_iata["iata_code"])
df_f = call_flight_api(routes_date)
df_flight = process_airport(df_f)



# write out
df_city.to_csv('data/intermediate/city.csv', index=False)
df_weather.to_csv('data/intermediate/weather.csv', index=False)
df_iata.to_csv('data/intermediate/city_airport.csv', index=False)
routes_df.to_csv('data/intermediate/routes.csv', index=False)
df_flight.to_csv('data/intermediate/flight_month.csv', index=False)