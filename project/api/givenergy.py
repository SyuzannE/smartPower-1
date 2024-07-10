import copy
import logging
import requests

from project.example_responses.example_data_handler import *

logger = logging.getLogger(__name__)

"""
https://givenergy.cloud/docs/api/v1#introduction
"""

class GivEnergy:
    def __init__(self, offline_debug, api_key):
        self.offline_debug = offline_debug
        self.base_url = 'https://api.givenergy.cloud'
        self.api_key = api_key
        self.system_specs_raw = self.get_system_specifications()
        self.system_specs = {}
        self.inverter_data = {}
        self.inverter_serial_number = self.extract_inverter_serial_number()

    def get_system_specifications(self):
        """
        https://givenergy.cloud/docs/api/v1#communication-device
        """
        if self.offline_debug:
            return copy.deepcopy(GivEnergyData.system_specification())
        else:
            url = f'{self.base_url}/v1/communication-device'
            params = {
                'page': '1',
            }
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            try:
                response = requests.request('GET', url, headers=headers, params=params)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as error:
                logger.error(f"Request error occurred: {error}")
                raise
            except Exception as general_error:
                logger.error(f"An unexpected error occurred: {general_error}")
                raise

    def extract_inverter_serial_number(self):
        # Extract inverter serial number
        if self.system_specs_raw is not None:
            return self.system_specs_raw['data'][0]['inverter']['serial']

    def get_inverter_systems_data(self):
        """
        https://givenergy.cloud/docs/api/v1#inverter-data-GETinverter--inverter_serial_number--system-data-latest
        """
        if self.offline_debug:
            return copy.deepcopy(GivEnergyData.inverter_systems())
        else:
            url = f'{self.base_url}/v1/inverter/{self.inverter_serial_number}/system-data/latest'
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            try:
                response = requests.request('GET', url, headers=headers)
                response.raise_for_status()
                self.inverter_data = response.json()
            except requests.exceptions.RequestException as error:
                logger.error(f"Request error occurred: {error}")
                raise
            except Exception as general_error:
                logger.error(f"An unexpected error occurred: {general_error}")
                raise

    def get_energy_usage(self, start_date, end_date, e_types):
        """
        https://givenergy.cloud/docs/api/v1#energy-flow-data-POSTinverter--inverter_serial_number--energy-flows
        """
        if self.offline_debug:
            return copy.deepcopy(GivEnergyData.energy_usage())
        else:
            payload = {"start_time": start_date,
                       "end_time": end_date,
                       "grouping": 0,
                       "types": e_types}

            url = f'{self.base_url}/v1/inverter/{self.inverter_serial_number}/energy-flows'
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            try:
                response = requests.request('POST', url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as error:
                logger.error(f"Request error occurred: {error}")
                raise
            except Exception as general_error:
                logger.error(f"An unexpected error occurred: {general_error}")
                raise

    def get_inverter_settings(self):
        """
        https://givenergy.cloud/docs/api/v1#inverter-control-GETinverter--inverter_serial_number--settings
        """
        if self.offline_debug:
            return copy.deepcopy(GivEnergyData.inverter_settings())
        else:
            url = f'{self.base_url}/v1/inverter/{self.inverter_serial_number}/settings'
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'}
            try:
                response = requests.request('GET', url, headers=headers)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as error:
                logger.error(f"Request error occurred: {error}")
                raise
            except Exception as general_error:
                logger.error(f"An unexpected error occurred: {general_error}")
                raise

    def read_inverter_setting(self, setting):
        """
        https://givenergy.cloud/docs/api/v1#inverter-control-POSTinverter--inverter_serial_number--settings--setting_id--read
        """
        if self.offline_debug:
            return copy.deepcopy(GivEnergyData.read_inverter_setting())
        else:
            url = f'{self.base_url}/v1/inverter/{self.inverter_serial_number}/settings/{setting}/read'
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            try:
                response = requests.request('POST', url, headers=headers)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as error:
                logger.error(f"Request error occurred: {error}")
                raise
            except Exception as general_error:
                logger.error(f"An unexpected error occurred: {general_error}")
                raise

    def update_inverter_setting(self, setting, value):
        """
        https://givenergy.cloud/docs/api/v1#inverter-control-POSTinverter--inverter_serial_number--settings--setting_id--write
        """
        url = f'{self.base_url}/v1/inverter/{self.inverter_serial_number}/settings/{setting}/write'
        payload = {"value": f"{value}"}
        if not self.offline_debug:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'}
            try:
                response = requests.request('POST', url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as error:
                logger.error(f"Request error occurred: {error}")
                raise
            except Exception as general_error:
                logger.error(f"An unexpected error occurred: {general_error}")
                raise
        else:
            print(f"URL: {url}")
            print(f"payload: {payload}")

    def extract_system_spec(self):
        battery_voltage = self.system_specs_raw['data'][0]['inverter']['info']['battery'][
            'nominal_voltage']
        battery_capacity_ah = self.system_specs_raw['data'][0]['inverter']['info']['battery'][
            'nominal_capacity']
        battery_capacity_wh = battery_voltage * battery_capacity_ah
        max_charge_rate = self.system_specs_raw['data'][0]['inverter']['info']['max_charge_rate']
        house_avg_base_load = 300

        hours_to_charge = round(battery_capacity_wh / (max_charge_rate - house_avg_base_load), 4)

        self.system_specs = {"battery_spec": {"voltage": battery_voltage,
                                              "amp_hour": battery_capacity_ah,
                                              "watt_hour": battery_capacity_wh,
                                              "max_charge_rate_watts": max_charge_rate,
                                              "hours_to_charge_full": hours_to_charge},
                             "inverter_spec": {},
                             "general_spec": {}
                             }


if __name__ == '__main__':
    offline_debug = False
    giv_energy = GivEnergy(offline_debug, os.environ.get("GE_API_KEY"))
    data = giv_energy.read_inverter_setting(64)

