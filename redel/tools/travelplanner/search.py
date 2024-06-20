"""
Implementation of TravelPlanner tools.

Docstrings and parameter descriptions adapted from
https://github.com/OSU-NLP-Group/TravelPlanner/blob/main/agents/prompts.py#L4.

Implementations adapted from https://github.com/OSU-NLP-Group/TravelPlanner/tree/main/tools.
"""

import enum
import re
from pathlib import Path
from typing import Annotated

import numpy as np
import pandas as pd
from kani import AIParam, ai_function

from redel.base_kani import BaseKani

TRAVELPLANNER_DB_PATH = Path(__file__).parent / "db"


class GDMTransportationMethod(enum.Enum):
    self_driving = "self-driving"
    taxi = "taxi"


class TravelPlannerMixin(BaseKani):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.flight_data = pd.read_csv(TRAVELPLANNER_DB_PATH / "flights/clean_Flights_2022.csv").dropna()[[
            "Flight Number",
            "Price",
            "DepTime",
            "ArrTime",
            "ActualElapsedTime",
            "FlightDate",
            "OriginCityName",
            "DestCityName",
            "Distance",
        ]]
        self.gdm_data = pd.read_csv(TRAVELPLANNER_DB_PATH / "googleDistanceMatrix/distance.csv")
        self.accommodation_data = pd.read_csv(
            TRAVELPLANNER_DB_PATH / "accommodations/clean_accommodations_2022.csv"
        ).dropna()[[
            "NAME",
            "price",
            "room type",
            "house_rules",
            "minimum nights",
            "maximum occupancy",
            "review rate number",
            "city",
        ]]
        self.restaurant_data = pd.read_csv(TRAVELPLANNER_DB_PATH / "restaurants/clean_restaurant_2022.csv").dropna()[
            ["Name", "Average Cost", "Cuisines", "Aggregate Rating", "City"]
        ]
        self.attraction_data = pd.read_csv(TRAVELPLANNER_DB_PATH / "attractions/attractions.csv").dropna()[
            ["Name", "Latitude", "Longitude", "Address", "Phone", "Website", "City"]
        ]
        self.city_data = self.load_city_data()

    @staticmethod
    def load_city_data():
        with open(TRAVELPLANNER_DB_PATH / "background/citySet_with_states.txt", "r") as f:
            city_state_mapping = f.read().strip().split("\n")
        city_data = {}
        for unit in city_state_mapping:
            city, state = unit.split("\t")
            if state not in city_data:
                city_data[state] = [city]
            else:
                city_data[state].append(city)
        return city_data

    async def close(self):
        await super().close()
        self.flight_data = None
        self.gdm_data = None
        self.accommodation_data = None
        self.restaurant_data = None
        self.attraction_data = None
        self.city_data = None

    # methods
    @ai_function()
    def flight_search(
        self,
        departure_city: Annotated[str, AIParam("The city you'll be flying out from.")],
        destination_city: Annotated[str, AIParam("The city you aim to reach.")],
        date: Annotated[str, AIParam("The date of your travel in YYYY-MM-DD format.")],
    ):
        """
        A flight information retrieval tool.
        Example: flight_search("New York", "London", "2022-10-01") would fetch flights from New York to London on October 1, 2022.
        """
        results = self.flight_data[self.flight_data["OriginCityName"] == departure_city]
        results = results[results["DestCityName"] == destination_city]
        results = results[results["FlightDate"] == date]
        if len(results) == 0:
            return "There is no flight from {} to {} on {}.".format(departure_city, destination_city, date)
        return results.to_string(index=False)

    @ai_function()
    def google_distance_matrix(
        self,
        origin: Annotated[str, AIParam("The departure city of your journey.")],
        destination: Annotated[str, AIParam("The destination city of your journey.")],
        mode: Annotated[GDMTransportationMethod, AIParam("The method of transportation.")],
    ):
        """
        Estimate the distance, time and cost between two cities.
        Example: google_distance_matrix("Paris", "Lyon", "self-driving") would provide driving distance, time and cost between Paris and Lyon.
        """
        origin = extract_before_parenthesis(origin)
        destination = extract_before_parenthesis(destination)
        info = {"origin": origin, "destination": destination, "cost": None, "duration": None, "distance": None}
        response = self.gdm_data[(self.gdm_data["origin"] == origin) & (self.gdm_data["destination"] == destination)]
        if len(response) > 0:
            if (
                response["duration"].values[0] is None
                or response["distance"].values[0] is None
                or response["duration"].values[0] is np.nan
                or response["distance"].values[0] is np.nan
            ):
                return "No valid information."
            info["duration"] = response["duration"].values[0]
            info["distance"] = response["distance"].values[0]
            if "driving" in mode:
                info["cost"] = int(eval(info["distance"].replace("km", "").replace(",", "")) * 0.05)
            elif mode == "taxi":
                info["cost"] = int(eval(info["distance"].replace("km", "").replace(",", "")))
            if "day" in info["duration"]:
                return "No valid information."
            return (
                f"{mode}, from {origin} to {destination}, duration: {info['duration']}, distance: {info['distance']},"
                f" cost: {info['cost']}"
            )

        return f"{mode}, from {origin} to {destination}, no valid information."

    @ai_function()
    def accommodation_search(
        self, city: Annotated[str, AIParam("The name of the city where you're seeking accommodation.")]
    ):
        """
        Discover accommodations in your desired city.
        Example: accommodation_search("Rome") would present a list of hotel rooms in Rome.
        """
        results = self.accommodation_data[self.accommodation_data["city"] == city]
        if len(results) == 0:
            return "There is no attraction in this city."
        return results.to_string(index=False)

    @ai_function()
    def restaurant_search(
        self, city: Annotated[str, AIParam("The name of the city where you're seeking restaurants.")]
    ):
        """
        Explore dining options in a city of your choice.
        Example: restaurant_search("Tokyo") would show a curated list of restaurants in Tokyo.
        """
        results = self.restaurant_data[self.restaurant_data["City"] == city]
        if len(results) == 0:
            return "There is no restaurant in this city."
        return results.to_string(index=False)

    @ai_function()
    def attraction_search(
        self, city: Annotated[str, AIParam("The name of the city where you're seeking attractions.")]
    ):
        """
        Find attractions in a city of your choice.
        Example: attraction_search("London") would return attractions in London.
        """
        results = self.attraction_data[self.attraction_data["City"] == city]
        # the results should show the index
        results = results.reset_index(drop=True)
        if len(results) == 0:
            return "There is no attraction in this city."
        return results.to_string(index=False)

    @ai_function()
    def city_search(self, state: Annotated[str, AIParam("The name of the state where you're seeking cities.")]):
        """
        Find cities in a state of your choice.
        Example: city_search("California") would return cities in California.
        """
        if state not in self.city_data:
            raise ValueError("Invalid State")
        return self.city_data[state]


def extract_before_parenthesis(s):
    match = re.search(r"^(.*?)\([^)]*\)", s)
    return match.group(1) if match else s
