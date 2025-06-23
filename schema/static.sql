CREATE TABLE city (
    id BIGINT NOT NULL PRIMARY KEY,
    city_name VARCHAR NOT NULL
);

CREATE TABLE nearest_airport (
    id BIGINT NOT NULL PRIMARY KEY,
    iata_code VARCHAR NOT NULL,
    city_id BIGINT NOT NULL,
    CONSTRAINT fk_city_id FOREIGN KEY (city_id) REFERENCES city(id)
);

CREATE TABLE route (
    id BIGINT NOT NULL PRIMARY KEY,
    depar_airport_id BIGINT NOT NULL,
    desti_airport_id BIGINT NOT NULL,
    CONSTRAINT fk_dep_id FOREIGN KEY (depar_airport_id) REFERENCES nearest_airport(id),
    CONSTRAINT fk_des_id FOREIGN KEY (desti_airport_id) REFERENCES nearest_airport(id)
);

CREATE TABLE weather (
    id BIGINT NOT NULL PRIMARY KEY,
    date DATE NOT NULL,
    city_id BIGINT NOT NULL,
    weather_id BIGINT NOT NULL,
    weather VARCHAR NOT NULL,
    alert BOOLEAN NOT NULL,
    CONSTRAINT fk_weather_city_id FOREIGN KEY (city_id) REFERENCES city(id)
);

CREATE TABLE flight (
    id BIGINT NOT NULL PRIMARY KEY,
    route_id BIGINT NOT NULL,
    departure_date DATE NOT NULL,
    price_quartile_minimum SMALLINT NOT NULL,
    price_quartile_low SMALLINT NOT NULL,
    price_quartile_middle SMALLINT NOT NULL,
    price_quartile_high SMALLINT NOT NULL,
    price_quartile_maximum SMALLINT NOT NULL,
    CONSTRAINT fk_flight_route_id FOREIGN KEY (route_id) REFERENCES route(id)
);