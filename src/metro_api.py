import board
from datetime import datetime
from adafruit_matrixportal.network import Network

from config import config
from secrets import secrets

# Keeping a global reference for this
_network = Network(status_neopixel=board.NEOPIXEL)


class MetroApiOnFireException(Exception):
    pass


class MetroApi:
    def fetch_train_predictions(station_code: str, group: str) -> [dict]:
        return MetroApi._fetch_train_predictions(station_code, group, retry_attempt=0)

    def _fetch_train_predictions(
        station_code: str, group: str, retry_attempt: int
    ) -> [dict]:
        try:
            api_url = config["ps_api_url"].format(stop_id=config["ps_stop_id"])
            train_data = _network.fetch(
                api_url, params={"key": config["ps_api_key"]}
            ).json()

            print("Received response from OneBusAway api...")

            trains = train_data["data"]["entry"]["arrivalsAndDepartures"]

            normalized_results = list(map(MetroApi._normalize_train_response, trains))

            return normalized_results
        except RuntimeError:
            if retry_attempt < config["metro_api_retries"]:
                print("Failed to connect to WMATA API. Reattempting...")
                # Recursion for retry logic because I don't care about your stack
                return MetroApi._fetch_train_predictions(
                    station_code, group, retry_attempt + 1
                )
            else:
                raise MetroApiOnFireException()

    def arrival_minutes(epoch: str) -> int:
        epoch_s = int(epoch) / 1000
        diff = epoch_s - int(datetime.now().strftime("%s"))
        return diff // 60

    def _normalize_train_response(train: dict) -> dict:
        line = 0x00FF00  # train["routeShortName"]
        destination = train["tripHeadsign"]
        arrival = train["predictedArrivalTime"]
        return dict(
            line=line,
            destination=destination,
            arrival=MetroApi.arrival_minutes(arrival),
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
