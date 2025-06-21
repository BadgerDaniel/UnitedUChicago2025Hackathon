from reddit_server import process_city

if __name__ == "__main__":
    for city in ["chicago"]:
        events_json = process_city(city)
        print(f"\nEvents in {city.title()}:\n{events_json}\n")