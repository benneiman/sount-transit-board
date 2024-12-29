import board
import time

from config import config
from secrets import secrets


class MetroApiOnFireException(Exception):
    pass


class MetroApi:
    def __init__(self):
        pass

    def fetch_train_predictions(self, wifi, station_codes, groups, walks={}) -> [dict]:
        return self._fetch_train_predictions(
            wifi, station_codes, groups, walks, retry_attempt=0
        )

    def _fetch_train_predictions(
        self, wifi, station_codes, groups, walks, retry_attempt: int
    ) -> [dict]:
        try:
            print("Fetching...")
            start = time.time()

            api_url = "https://jsonplaceholder.typicode.com/todos/1"
            # api_url = (
            #     config["wmata_api_url"]
            #     + config["metro_station_codes"]
            #     + ".json?key="
            #     + config["wmata_api_key"]
            # )

            # response = _network.fetch(api_url)
            print("IM HERE")
            response = wifi.get(api_url, timeout=30)
            print("API Response:", response.status_code)

            train_data = response.json()

            trains = train_data["data"]["entry"]["arrivalsAndDepartures"]

            # normalized_results = list(
            #     map(
            #         lambda x: MetroApi._normalize_train_response(
            #             x, response["currentTime"]
            #         ),
            #         trains,
            #     )
            # )
            # trains = list(filter(lambda t: (t['LocationCode'], t['Group']) in groups, response['Trains']))
            print("Received response from " + config["source_api"] + " api...")
            TIME_BUFFER = round((time.time() - start) / 60) + 1
            trains = [
                self._normalize_train_response(
                    t, TIME_BUFFER, train_data["currentTime"]
                )
                for t in trains
            ]

            if walks != {}:
                trains = list(
                    filter(
                        lambda t: self.arrival_map(t["arrival"]) - walks[t["loc"]] >= 0,
                        trains,
                    )
                )

            if len(groups) > 1:
                trains = sorted(trains, key=lambda t: self.arrival_map(t["arrival"]))

            print("Trains returned by api: " + str(trains))
            print("Time to Update: " + str(time.time() - start))
            return trains

        except Exception as e:
            print(e)
            if retry_attempt < config["metro_api_retries"]:
                print("Failed to connect to API. Reattempting...")
                # Recursion for retry logic because I don't care about your stack
                return self._fetch_train_predictions(
                    wifi, station_codes, groups, walks, retry_attempt + 1
                )
            else:
                raise MetroApiOnFireException()

    def arrival_map(self, arr):
        if arr == "BRD":
            return 0
        elif arr == "ARR":
            return 1
        elif arr.isdigit():
            return int(arr)
        else:
            return 100  # DLY would fall into this case, but not sure how to handle it without storing what the previous time was

    def _normalize_train_response(self, train: dict, buff: int, current_time) -> dict:
        line = 0x00FF00  # train["routeShortName"]
        destination = train["tripHeadsign"]
        arrival = (train["predictedArrivalTime"] - current_time) // 60000
        return dict(
            line_color=line,
            destination=destination,
            arrival=arrival,  # MetroApi.arrival_minutes(arrival),
        )
        # line = train['Line']
        # destination = train['Destination']
        # loc = train['LocationCode']

        # if config['source_api'] == 'WMATA':
        #     arrival = train["Min"]
        # else:
        #     arrival = train['minutesAway']

        # if arrival.isdigit():
        #     arrival = int(arrival) - buff
        #     if arrival <= 0:
        #         arrival = 'ARR'
        #     else:
        #         arrival = str(arrival)

        # if destination in config["station_mapping"]:
        #     destination = config["station_mapping"][destination]

        # return {
        #     'line_color': self._get_line_color(line),
        #     'destination': destination[:config['destination_max_characters']],
        #     'arrival': arrival,
        #     'loc': loc
        # }

    def _get_line_color(self, line: str) -> int:
        if line == "RD":
            return 0xFF0000
        elif line == "OR":
            return 0xFF5500
        elif line == "YL":
            return 0xFFFF00
        elif line == "GR":
            return 0x00FF00
        elif line == "BL":
            return 0x0000FF
        else:
            return 0xAAAAAA
