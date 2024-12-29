import board

from time import time
from adafruit_matrixportal.network import Network

from config import config
from secrets import secrets

# Keeping a global reference for thi
_network = Network(status_neopixel=board.NEOPIXEL)


class MetroApiOnFireException(Exception):
    pass


class MetroApi:
    def fetch_train_predictions(station_code: str) -> [dict]:
        return MetroApi._fetch_train_predictions(station_code, retry_attempt=0)

    def _fetch_train_predictions(
        station_code: str, group: str, retry_attempt: int
    ) -> [dict]:
        try:
            api_url = (
                config["oba_api_url"]
                + config["metro_station_code"]
                + ".json?key="
                + config["oba_api_key"]
            )
            req = _network.fetch(api_url)
            print(api_url)

            train_data = req.json()

            #     print("Received response from OneBusAway api...")

            trains = train_data["data"]["entry"]["arrivalsAndDepartures"]

            normalized_results = list(
                map(
                    lambda x: MetroApi._normalize_train_response(
                        x, train_data["currentTime"]
                    ),
                    trains,
                )
            )

            return [x for x in normalized_results if x.get("arrival") > 0]
        except RuntimeError:
            if retry_attempt < config["metro_api_retries"]:
                print("Failed to connect to WMATA API. Reattempting...")
                # Recursion for retry logic because I don't care about your stack
                return MetroApi._fetch_train_predictions(
                    station_code, group, retry_attempt + 1
                )
            else:
                raise MetroApiOnFireException()

    def _normalize_train_response(train: dict, current_time: int) -> dict:
        line = 0x00FF00  # train["routeShortName"]
        destination = train["tripHeadsign"]
        arrival = (train["predictedArrivalTime"] - current_time) // 60000
        return dict(
            line_color=line,
            destination=destination,
            arrival=arrival,  # MetroApi.arrival_minutes(arrival),
        )

    def _get_line_color(line: str) -> int:
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
