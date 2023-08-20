# prices for Agile go live for next day at 4pm

"""
TODO:
    - programmatically workout difference between Local, Octopus and GivEnergy times
"""

from datetime import datetime, timedelta
import json
import os

import pandas as pd

from project.givenergy import GivEnergy
from project.octopus import Octopus
from project.forecast import Forecast
from tools.analysis import *


def save_json_file(filename, data):
    """
    Save dictionary data as a .json file in the example responses folder
    """
    with open(f'example_responses/{filename}.json', 'w') as f:
        json.dump(data, f)


def logic_index_to_time(index):
    """
    Convert a number that represents a count of half hour instances into hours
    """
    time = (index * 0.5) - 0.5
    return time


def analyse_energy_usage(giv_energy, weeks, time_offsets):
    """
    Get the average of the last 4 weekdays energy usage in half hour slots, for the following day
    Tidy data and insert into dataframe. Perform some basic analysis
    """
    previous_dates = get_x_weeks_previous_weekday_dates(weeks)
    data = get_energy_usage_days(giv_energy, previous_dates, [0, 3, 5])
    all_days = extract_half_hour_data(data)
    df = add_to_df(all_days, time_offsets)
    df = df.rename(columns={'avg': 'avg_consumption_kwh'})
    return df


def analyse_solar_production(giv_energy, days, time_offsets):
    """
    Get the average of the last x days solar production in half hour slots
    Tidy data and insert into dataframe. Perform some basic analysis
    """
    previous_dates = get_x_previous_days_dates(days)
    data = get_energy_usage_days(giv_energy, previous_dates, [0, 1, 2])
    all_days = extract_half_hour_data(data)
    df = add_to_df(all_days, time_offsets)
    df = df.rename(columns={'avg': 'avg_production_kwh'})
    return df


def analyse_forecast(forecast):
    """

    """
    data = forecast.get_forecast_location('320301')
    # Get values for today and tomorrows dates in format "2023-08-18Z"
    today = datetime.today()
    dates = [today.strftime('%Y-%m-%dZ'),
             (today + timedelta(days=1)).strftime('%Y-%m-%dZ')]
    # dates = ['2023-08-18Z', '2023-08-19Z']
    result = []
    for day in data['SiteRep']['DV']['Location']['Period']:
        for count, date in enumerate(dates):
        # for date in dates:
            if day['value'] == date:
                for predictions in day["Rep"]:
                    forecast = {'date': date,
                                'timer': count*24 + int(predictions['$']) / 60,
                                'solar_index': int(predictions['U']),
                                }
                    result.append(forecast)
    df_forecast = pd.DataFrame(result)

    # fill out for half hour slots
    # Choosing the row with index 1 (second row) to duplicate
    all_rows = []
    for row in range(df_forecast.shape[0]):
        chosen_row = df_forecast.loc[row].copy()

        # Duplicating the row 4 times and increasing the value in column 'A' by 0.5 each time
        duplicated_rows = []
        for i in range(5):
            chosen_row['timer'] += 0.5
            duplicated_rows.append(chosen_row.copy())
        all_rows = all_rows + duplicated_rows
        # Concatenate the duplicated rows to the original dataframe
    df_forecast = pd.concat([df_forecast, pd.DataFrame(all_rows)], ignore_index=True)
    df_forecast = df_forecast.sort_values(by=['date', 'timer'])

    # convert into a range to use as bias
    # NewValue = (((OldValue - OldMin) * NewRange) / OldRange) + NewMin
    # OldRange = (7 - 1)
    # NewRange = (2 - 0.1)
    # NewValue = (((5 - 1) * 1.9) / 6) + 0.1
    convert_solar_index_to_bias(df_forecast)
    return df_forecast


def convert_solar_index_to_bias(df_forecast):
    """
    Convert solar index number to a value that can be used to be multiplied against
    Solar index values: In the UK, 0 represents night time and 7 is a blue sky day with intense sun light
    Convert range 0 - 7 to new range 0 - 2
    """
    df_forecast['solar_bias'] = (((df_forecast['solar_index'] - 1) * 1.9 / 6) + 0.1)
    df_forecast.loc[df_forecast['solar_bias'] < 0, 'solar_bias'] = 0
    return df_forecast


def add_to_df(all_days, time_offsets):
    """
    Create dataframe from dictionary data
    """
    # Create dataframe
    df = pd.DataFrame(all_days).T
    # Add average column
    df["avg"] = df.mean(axis=1)
    # Add a time column as floats
    df["timer"] = [x*0.5 for x in range(df.shape[0])]
    # Filter df based from time now and time column
    time = datetime.today()
    time_offset = time_offsets['giv_energy_time'] - time_offsets['local_time']
    hours, mins = int(time.strftime('%H')) + time_offset, int(time.strftime('%M'))
    if mins > 30: hours += 0.5
    df = df.loc[df['timer'] > hours]
    return df


def get_x_weeks_previous_weekday_dates(weeks):
    """
    Using today's and tomorrow's day of the week, return the previous x weeks dates for that same weekday
    e.g. Saturday today, so get the previous 4 Saturday and Sunday dates
    """
    today = datetime.today()
    tomorrow = today + timedelta(days=1)
    last_same_weekday = tomorrow - timedelta(days=7)
    previous_dates = []
    # Get the 4 previous dates
    for i in range(weeks):
        weekday_date = last_same_weekday - timedelta(days=i * 7)
        previous_dates.append({'start_date': (weekday_date + timedelta(days=-1)).strftime('%Y-%m-%d'),
                               'end_date': (weekday_date + timedelta(days=1)).strftime('%Y-%m-%d')})
    return previous_dates


def get_x_previous_days_dates(days):
    """
    Get the dates for the previous x days
    """
    day_b4_yesterday = datetime.today() - timedelta(days=2)
    previous_dates = []
    # Get the 4 previous dates
    for i in range(days):
        previous_day = day_b4_yesterday - timedelta(days=i)
        previous_dates.append({'start_date': previous_day.strftime('%Y-%m-%d'),
                               'end_date': (previous_day + timedelta(days=2)).strftime('%Y-%m-%d')})
    return previous_dates


def get_energy_usage_days(giv_energy, previous_dates, e_types):
    """
    Request energy usage data for the given dates
    """
    data = []
    for dates in previous_dates:
        # filter the data
        raw_data = giv_energy.get_energy_usage(dates['start_date'], dates['end_date'], e_types)
        data.append(raw_data['data'])
    return data


def extract_half_hour_data(data):
    """
    Average each half hour time slot between the number of weeks
    """
    all_days = []
    for day in data:
        day.popitem()
        day_total = []
        for half_hour in day.values():
            day_total.append(sum(half_hour["data"].values()))
        all_days.append(day_total)
    return all_days


def calculate_battery_depletion_time(giv_energy, forecast, time_offsets):
    """
    Request all needed data and estimate how long until the battery will be depleted
    """
    # get renewable system specs
    giv_energy.extract_system_spec()

    # get average energy consumption
    df_house_consumption = analyse_energy_usage(giv_energy, 4, time_offsets)

    # get watt hour capacity remaining in battery
    inverter_data = giv_energy.get_inverter_systems_data()
    battery_watt_hours_remaining = ((inverter_data["data"]["battery"]["percent"] / 100) * \
                                    giv_energy.system_specs["battery_spec"]["watt_hour"]) / 1000

    # get weather forecast in half hour slots
    df_forecast = analyse_forecast(forecast)

    # get average production of panels in half hour slots for last 30 days
    df_solar_production = analyse_solar_production(giv_energy, 40, time_offsets)

    df_result = df_solar_production[["avg_production_kwh", "timer"]].merge(df_forecast[["solar_bias", "timer"]], how='left', on="timer")

    # sum solar data to historic consumption data
    df_result = df_result.merge(df_house_consumption[["avg_consumption_kwh", "timer"]], how='left', on="timer")

    # multiply solar production with bias
    df_result['energy'] = df_result['avg_consumption_kwh'] - (df_result['avg_production_kwh'] * df_result['solar_bias'])

    # compare against half hour historic time slot data to get an estimated hours left until depleted, tolerance this?
    total_energy_consumed = 0
    no_half_hour_slots = 0
    for energy in df_result['energy']:
        if total_energy_consumed + energy < battery_watt_hours_remaining:
            total_energy_consumed += energy
            no_half_hour_slots += 1
        else:
            break

    time_taken_until_empty = logic_index_to_time(no_half_hour_slots)
    return df_result, no_half_hour_slots


def get_agile_data(octopus, est_bat_depletion_time, time_offsets):
    """
    Request Agile data from Octopus, add to dataframe and do some basic analysis
    """
    agile_data = octopus.get_tariff_data()
    df = pd.DataFrame(agile_data["results"])

    now = datetime.now()
    # convert time now to the last 30 minutes hole number
    minutes_to_subtract = now.minute % 30
    # Factor in that Octopus time, GMT without daylight savings. Reset seconds and ms
    time_offset = time_offsets['octopus_time'] - time_offsets['local_time']
    rounded_time = (now - timedelta(hours=time_offset, minutes=minutes_to_subtract)).replace(second=0, microsecond=0)
    time = rounded_time.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Filter start of data so first row represents current half hour time slot
    idx = (df['valid_from'] == time).idxmax()
    df = df.loc[:idx]
    df = df.iloc[::-1].reset_index(drop=True)

    # Filter end of data, using the estimated battery depletion time
    df = df.iloc[:est_bat_depletion_time]
    return df


def extract_time_windows(df_agile_data, no_half_hour_slots, time_offsets):
    """
    Choose most suitable time windows, for cost and time left to depletion.
    Modify time ready for GivEnergy time (+2?) and get into correct format
    """
    df_result = None
    grade_dict = {
        (0, 8): 10,
        (8, 16): 8,
        (16, 24): 6,
        (24, 32): 4,
        (32, 1000): 2
    }
    windows_to_charge = 10
    for (low, high), grade in grade_dict.items():
        if low <= logic_index_to_time(no_half_hour_slots) < high:
            windows_to_charge = grade
            break
    df_result = df_agile_data.nsmallest(windows_to_charge, 'value_inc_vat')

    # time value format: HH:MM
    time_offset = time_offsets['giv_energy_time'] - time_offsets['octopus_time']
    df_result['valid_from_dt'] = (pd.to_datetime(df_result['valid_from'])) + pd.Timedelta(hours=time_offset)
    df_result['valid_to_dt'] = (pd.to_datetime(df_result['valid_to'])) + pd.Timedelta(hours=time_offset)
    df_result = df_result.sort_values(by=['valid_from_dt']).reset_index(drop=True)
    df_time_windows = merge_consecutive_rows(df_result)

    df_time_windows['from_hours'] = df_time_windows['valid_from_dt'].dt.strftime('%H:%M')
    df_time_windows['too_hours'] = df_time_windows['valid_to_dt'].dt.strftime('%H:%M')
    return df_time_windows


def merge_consecutive_rows(df_result):
    """
    Some time windows lead onto the next window,
    this logic checks for these consecutive rows and merges them together
    """
    # Initialize empty list to store the merged rows
    merged_rows = []

    # Initialize current start and end values
    start = df_result.loc[0, 'valid_from_dt']
    end = df_result.loc[0, 'valid_to_dt']

    # Loop through rows
    for i in range(1, len(df_result)):
        if df_result.loc[i, 'valid_from_dt'] == end:
            # If consecutive, update the end value
            end = df_result.loc[i, 'valid_to_dt']
        else:
            # If not consecutive, append the merged row and reset start and end values
            merged_rows.append({'valid_from_dt': start, 'valid_to_dt': end})
            start = df_result.loc[i, 'valid_from_dt']
            end = df_result.loc[i, 'valid_to_dt']

    # Append the last merged row
    merged_rows.append({'valid_from_dt': start, 'valid_to_dt': end})

    # Create the result dataframe
    return pd.DataFrame(merged_rows)

def update_inverter_charge_time(giv_energy, offline_debug, from_time, to_time):
    """
    Send commands to GivEnergy inverter to charge battery from mains
    """
    if giv_energy is None:
        giv_energy = GivEnergy(offline_debug, os.environ.get("GE_API_KEY"))
    giv_energy.update_inverter_setting(64, from_time)
    giv_energy.update_inverter_setting(65, to_time)


def calculate_charge_windows():
    """
    The core calculation function
    """
    time_offsets = {'local_time': 0,
                    'octopus_time': -1,
                    'giv_energy_time': 1}

    offline_debug = True if os.environ.get("OFFLINE_DEBUG") == '1' else False
    giv_energy = GivEnergy(offline_debug, os.environ.get("GE_API_KEY"))
    forecast = Forecast(offline_debug, os.environ.get("DATAPOINT_API_KEY"))

    df_energy_result, est_no_half_hour_windows_bat_depletion = calculate_battery_depletion_time(giv_energy, forecast, time_offsets)

    # filter Octopus data to find the cheapest value in time frame available
    octopus = Octopus(offline_debug, os.environ.get("OCTOPUS_API_KEY"))
    df_agile_data = get_agile_data(octopus, est_no_half_hour_windows_bat_depletion, time_offsets)
    df_time_windows = extract_time_windows(df_agile_data, est_no_half_hour_windows_bat_depletion, time_offsets)

    # Set the first time window, send the following windows to cloudwatch
    update_inverter_charge_time(giv_energy, offline_debug,
                                df_time_windows.iloc[0]["from_hours"],
                                df_time_windows.iloc[0]["too_hours"])
    df_time_windows = df_time_windows.drop(df_time_windows.index[0]).reset_index(drop=True)

    # Add each row's values to cloudwatch
    for _, row in df_time_windows[['from_hours', 'too_hours']].iterrows():
        print(row)

    # analyse_data(df_house_consumption, df_solar_production)
    print('complete')


if __name__ == '__main__':
    calculate_charge_windows()
    # update_inverter_charge_time()


