import copy
import requests
from requests.auth import HTTPBasicAuth

from project.example_responses.example_data_handler import (OctopusData)


class Octopus:
    def __init__(self, offline_debug, api_key):
        self.offline_debug = offline_debug
        self.api_key = api_key
        self.base_url = "https://api.octopus.energy"
        self.auth = HTTPBasicAuth(self.api_key, '')

    def get_tariff_data(self):
        if self.offline_debug:
            return copy.deepcopy(OctopusData.agile_tariff())
        else:
            product_code = "AGILE-FLEX-22-11-25"
            tariff_code = f"E-1R-{product_code}-G"
            tariff_url = f"{self.base_url}/v1/products/{product_code}/electricity-tariffs/{tariff_code}/standard-unit-rates/"
            response = requests.get(tariff_url, auth=self.auth)
            return response.json()
