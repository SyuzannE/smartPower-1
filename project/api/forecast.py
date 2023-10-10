"""
https://www.metoffice.gov.uk/services/data/datapoint/api-reference
https://www.metoffice.gov.uk/binaries/content/assets/metofficegovuk/pdf/data/datapoint_api_reference.pdf
"""

import copy
import os

import pandas as pd
import requests
from requests.auth import HTTPBasicAuth


from project.example_responses.example_data_handler import (OctopusData)


class Forecast:
    def __init__(self, offline_debug, api_key):
        self.offline_debug = offline_debug
        self.api_key = api_key
        self.base_url = "http://datapoint.metoffice.gov.uk/public/data/"
        self.auth = HTTPBasicAuth(self.api_key, '')

    def get_location_data(self):
        if self.offline_debug:
            return copy.deepcopy(OctopusData.agile_tariff())
        else:
            url = f"{self.base_url}val/wxfcs/all/json/sitelist?res=3hourly&key={self.api_key}"
            response = requests.get(url)
            response.raise_for_status()
            return response.json()

    def get_forecast_location(self, location):
        if self.offline_debug:
            return copy.deepcopy(OctopusData.agile_tariff())
        else:
            url = f"{self.base_url}val/wxfcs/all/json/{location}?res=3hourly&key={self.api_key}"
            response = requests.get(url)
            response.raise_for_status()
            return response.json()


if __name__ == '__main__':
    offline_debug = True if os.environ.get("OFFLINE_DEBUG") == '1' else False
    forecast = Forecast(offline_debug, os.environ.get("DATAPOINT_API_KEY"))

    # data = forecast.get_location_data()
    data = forecast.get_forecast_location('320301')
    # save_json_file("lancaster_forecast", data)

    # Get values for today and tomorrows dates in format "2023-08-18Z"
    dates = ['2023-08-18Z', '2023-08-19Z']
    result = []
    for day in data['SiteRep']['DV']['Location']['Period']:
        for date in dates:
            if day['value'] == date:
                for predictions in day["Rep"]:
                    forecast = {'date': date,
                                'time': int(predictions['$']) / 60,
                                'solar_index': int(predictions['U']),
                                }
                    result.append(forecast)

    df_forecast = pd.DataFrame(result)
    # U: solar uv index, the higher the better
    # $: minutes past midnight

    # fill out for half hour slots
    # Choosing the row with index 1 (second row) to duplicate
    all_rows = []
    for row in range(df_forecast.shape[0]):
        chosen_row = df_forecast.loc[row].copy()

        # Duplicating the row 4 times and increasing the value in column 'A' by 0.5 each time
        duplicated_rows = []
        for i in range(5):
            chosen_row['time'] += 0.5
            duplicated_rows.append(chosen_row.copy())
        all_rows = all_rows + duplicated_rows
        # Concatenate the duplicated rows to the original dataframe
    df_forecast = pd.concat([df_forecast, pd.DataFrame(all_rows)], ignore_index=True)
    df_forecast = df_forecast.sort_values(by=['date', 'time'])
    print(1)