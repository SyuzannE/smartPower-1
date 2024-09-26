import time
from datetime import datetime, timedelta
import logging
import json
import math
import os
from typing import Tuple, Any

import numpy as np
import pandas as pd
import pytz

from project.api.givenergy import GivEnergy
from project.api.forecast import Forecast
from project.api.octopus import Octopus
from project.secrets import get_secret_or_env

logger = logging.getLogger(__name__)

# lowest_charge_threshold in kwh, lowest charge point before adding additional charge
lowest_charge_threshold = 2


def get_time_offsets():
    # Calculate between CET and London
    # Define the CET timezone
    cet = pytz.timezone('CET')

    # Get the current time in UTC
    utc_now = pytz.utc.localize(datetime.utcnow())

    # Convert the current time to CET
    cet_now = utc_now.astimezone(cet)

    # Get the current local time, and make it timezone-aware
    local_now = datetime.now()
    local_tz = pytz.timezone('Europe/London')  # replace with your local timezone
    local_now = local_tz.localize(local_now)

    # Calculate the difference in hours
    cet_time_diff = (cet_now - local_now).total_seconds() // 3600  # difference in hours, as an integer

    # Calculate between London and UTC
    # Current time in London
    london_now = utc_now.astimezone(pytz.timezone('Europe/London'))

    # Calculate the offset in hours
    offset_seconds = (london_now.utcoffset().total_seconds())
    utc_time_diff = int(offset_seconds // 3600)  # Convert to integer hours
    utc_time_diff = -utc_time_diff # make negative as were interest in London time compared to UTC not UTC compared to London

    local = datetime.now()

    if local.hour == utc_now.hour:
        local_time = 1
    else:
        local_time = 0


    return {'local_time': local_time,
            'octopus_time': utc_time_diff,
            'giv_energy_time': 0,
            'aws': utc_time_diff}


def save_json_file(filename, data):
    """
    Save dictionary data as a .json file in the example responses folder
    """
    with open(f'example_responses/{filename}.json', 'w') as f:
        json.dump(data, f)


def analyse_energy_usage(giv_energy, weeks, time_offsets):
    """
    Get the average of the last 4 weekdays energy usage in half hour slots, for the following day
    Tidy data and insert into dataframe. Perform some basic analysis
    """
    previous_dates = get_x_weeks_previous_weekday_dates(weeks)
    data = get_energy_usage_days(giv_energy, previous_dates, [0, 3, 5])
    all_days, times = extract_half_hour_data(data)
    df = add_to_df(all_days, times, time_offsets)
    df = df.rename(columns={'avg': 'avg_consumption_kwh'})
    return df


def analyse_solar_production(giv_energy, days, time_offsets):
    """
    Get the average of the last x days solar production in half hour slots
    Tidy data and insert into dataframe. Perform some basic analysis
    """
    previous_dates = get_x_previous_days_dates(days)
    data = get_energy_usage_days(giv_energy, previous_dates, [0, 1, 2])
    all_days, times = extract_half_hour_data(data)
    df = add_to_df(all_days, times, time_offsets)
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
            if day['value'] == date:
                for predictions in day["Rep"]:
                    forecast = {'date': date,
                                'timer': count * 24 + int(predictions['$']) / 60,
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


def add_to_df(all_days, times, time_offsets):
    """
    Create dataframe from dictionary data
    """
    # Create dataframe
    df = pd.DataFrame(all_days).T
    # Add average column
    df["avg"] = df.mean(axis=1)
    # Add a time column as floats
    df["timer"] = [x * 0.5 for x in range(df.shape[0])]
    df["hours"] = times
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

    convert first day times into date times
    """
    all_days = []
    for day in data:
        day.popitem()
        day_total = []
        times = []
        for half_hour in day.values():
            times.append((datetime.strptime(half_hour["start_time"], '%Y-%m-%d %H:%M')).time())
            day_total.append(sum(half_hour["data"].values()))
        all_days.append(day_total)
    return all_days, times


def calculate_battery_depletion_time(giv_energy: Any, forecast: Any, time_offsets: Any) -> Tuple[pd.DataFrame, Any]:
    """
    Estimates the battery depletion time by analyzing various parameters including
    energy consumption, weather forecast, and solar production.

    This function fetches the system specifications, calculates the average energy consumption,
    determines the remaining battery capacity, retrieves weather forecast data,
    and assesses solar panel productivity based on historical data. It then merges
    these data points to calculate the expected energy consumption and production,
    thereby estimating the time until the battery is fully depleted.
    """
    # get renewable system specs
    giv_energy.extract_system_spec()

    # get average energy consumption
    df_house_consumption = analyse_energy_usage(giv_energy, 4, time_offsets)

    # get watt hour capacity remaining in battery
    giv_energy.get_inverter_systems_data()
    giv_energy.system_specs["battery_spec"]["battery_kwatt_hours_remaining"] = ((giv_energy.inverter_data["data"][
                                                                                     "battery"]["percent"] / 100) * \
                                                                                giv_energy.system_specs["battery_spec"][
                                                                                    "watt_hour"]) / 1000

    # get weather forecast in half hour slots
    df_forecast = analyse_forecast(forecast)

    # get average production of panels in half hour slots for last 30 days
    df_solar_production = analyse_solar_production(giv_energy, 40, time_offsets)

    df_result = df_solar_production[["avg_production_kwh", "timer"]].merge(df_forecast[["solar_bias", "timer"]],
                                                                           how='left', on="timer")

    # sum solar data to historic consumption data
    df_result = df_result.merge(df_house_consumption[["avg_consumption_kwh", "timer", "hours"]], how='left', on="timer")

    # multiply solar production with bias
    df_result['energy'] = df_result['avg_consumption_kwh'] - (df_result['avg_production_kwh'] * df_result['solar_bias'])

    return df_result, giv_energy


def get_agile_data(octopus, time_offsets):
    """
    Request Agile data from Octopus, add to dataframe and do some basic analysis
    """
    agile_data = octopus.get_tariff_data()
    df = pd.DataFrame(agile_data["results"])

    now = datetime.now()
    local_time = time_offsets['local_time']
    giv_time = time_offsets['giv_energy_time']
    octopus_time = time_offsets['octopus_time']

    # convert time to the next 30 minute hole number
    minutes_to_add = 30 - now.minute % 30

    # Adjust local time to match octopus time according to time_offsets
    now = now + timedelta(hours=local_time + octopus_time)

    # reset seconds and ms
    rounded_time = (now - timedelta(minutes=-minutes_to_add)).replace(second=0, microsecond=0)
    time = rounded_time.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Filter start of data so first row represents current half hour time slot
    idx = (df['valid_from'] == time).idxmax()
    df = df.loc[:idx]
    df = df.iloc[::-1].reset_index(drop=True)

    # Filter end of data for 24 hours period
    df = df.iloc[:48]

    # Adjust octopus agile api times to match giv time
    df['valid_from_octopus'] = pd.to_datetime(df['valid_from'])
    df['valid_to_octopus'] = pd.to_datetime(df['valid_to'])

    time_delta = pd.Timedelta(hours=giv_time-octopus_time)
    df['valid_from_giv'] = df['valid_from_octopus'] + time_delta
    df['valid_to_giv'] = df['valid_to_octopus'] + time_delta
    return df


def prepare_time_windows_for_givenergy(df_result, time_offsets):
    # df_result['valid_from_dt'] = (pd.to_datetime(df_result['valid_from']))
    # df_result['valid_to_dt'] = (pd.to_datetime(df_result['valid_to']))
    df_result = df_result.sort_values(by=['valid_from_giv']).reset_index(drop=True)
    df_time_windows = merge_consecutive_rows(df_result)

    df_time_windows['from_hours_giv'] = df_time_windows['valid_from_giv'].dt.strftime('%H:%M')
    df_time_windows['too_hours_giv'] = df_time_windows['valid_to_giv'].dt.strftime('%H:%M')

    aws_time = time_offsets['aws']
    giv_time = time_offsets['giv_energy_time']
    time_delta = pd.Timedelta(hours=aws_time-giv_time)
    df_time_windows['valid_from_aws'] = df_time_windows['valid_from_giv'] + time_delta
    df_time_windows['valid_to_aws'] = df_time_windows['valid_to_giv'] + time_delta

    df_time_windows['from_hours_aws'] = df_time_windows['valid_from_aws'].dt.strftime('%H:%M')
    df_time_windows['too_hours_aws'] = df_time_windows['valid_to_aws'].dt.strftime('%H:%M')
    return df_time_windows


def merge_consecutive_rows(df_result):
    """
    Some time windows lead onto the next window,
    this logic checks for these consecutive rows and merges them together
    """
    # Initialize empty list to store the merged rows
    merged_rows = []

    # Initialize current start and end values
    start = df_result.loc[0, 'valid_from_giv']
    end = df_result.loc[0, 'valid_to_giv']

    # Loop through rows
    for i in range(1, len(df_result)):
        if df_result.loc[i, 'valid_from_giv'] == end:
            # If consecutive, update the end value
            end = df_result.loc[i, 'valid_to_giv']
        else:
            # If not consecutive, append the merged row and reset start and end values
            merged_rows.append({'valid_from_giv': start, 'valid_to_giv': end})
            start = df_result.loc[i, 'valid_from_giv']
            end = df_result.loc[i, 'valid_to_giv']

    # Append the last merged row
    merged_rows.append({'valid_from_giv': start, 'valid_to_giv': end})

    # Create the result dataframe
    return pd.DataFrame(merged_rows)


def update_inverter_charge_time(giv_energy, offline_debug, from_time, to_time):
    """
    Send commands to GivEnergy inverter to charge battery from mains
    """
    if giv_energy is None:
        giv_energy = GivEnergy(offline_debug, os.environ.get("GE_API_KEY"))

    set_and_check_setting(giv_energy, 64, from_time)
    set_and_check_setting(giv_energy, 65, to_time)
    # giv_energy.update_inverter_setting(64, from_time)
    # giv_energy.update_inverter_setting(65, to_time)    logger.info(f"Inverter set to charge from {from_time} too {to_time}")


def set_and_check_setting(giv_energy, setting, value):
    # Try setting and reading back the inverter setting 3 times
    for _ in range(3):
        giv_energy.update_inverter_setting(setting, value)
        time.sleep(1)
        result = giv_energy.read_inverter_setting(setting)
        if result:
            if result['data']['value'] == value:
                break
    return None



def update_cloud_watch(cloudwatch, cloud_watch_times, aws_fields):
    if cloud_watch_times and len(cloud_watch_times) > 1:
        last_time = cloud_watch_times[0]['too_hours_aws']
        cloud_watch_times = cloud_watch_times[1:]
        event_json = {'msg': 'update',
                      'data': cloud_watch_times}
        cloudwatch.create_event(last_time, aws_fields, event_json)
    else:
        event_json = {'msg': 'update',
                      'data': ''}
        cloudwatch.send_update('cron(0 1 1 1 ? 2050)', 'DISABLED', aws_fields, event_json)
        logger.info(f"CloudWatch cron schedule DISABLED")

    return cloud_watch_times


def concat_data_sources(df_energy_result, df_agile_data):
    # concat dataframes but I don't want any nan values, so don't merge passed the minimum rows
    min_length = min(len(df_energy_result), len(df_agile_data))
    df_agile_data = df_agile_data.iloc[:min_length].copy()
    df_energy_result = df_energy_result.iloc[:min_length].copy()
    df_energy_insights = pd.concat(
        [df_energy_result[["timer", "hours", "energy"]], df_agile_data[["value_inc_vat", "valid_from_giv", "valid_to_giv"]]],
        axis=1)

    return df_energy_insights


def optimize_charging_for_low_capacity(df_energy_insights: pd.DataFrame, battery_remaining_capacity: float,
                                       lowest_charge_threshold: float, battery_max_capacity,
                                       battery_charge_rate_hourly) -> pd.DataFrame:
    """
    Adjusts charging schedule by adding additional charging when battery capacity drops below a specified threshold.

    This function identifies the point where the running battery capacity falls below the specified threshold,
    then within the time before this point, it finds the time with the minimum energy price and adjusts the
    charging schedule to charge at this time. The function then recalculates the running battery capacity
    based on the new charging schedule.
    """
    # Find the first row, i.e the lowest index row where the running energy drops below 2
    # are first 2 rows already charging?
    if df_energy_insights['charge'].iloc[0] == True and df_energy_insights['charge'].iloc[1] == True:
        low_charge_index = \
        df_energy_insights.iloc[2:].loc[df_energy_insights['running_battery_capacity'] < lowest_charge_threshold].index[
            0]
    else:
        low_charge_index = \
        df_energy_insights.loc[df_energy_insights['running_battery_capacity'] < lowest_charge_threshold].index[0]

    low_charge_index = 1 if low_charge_index == 0 else low_charge_index

    # then filter the dataframe with that rows index
    df_first = df_energy_insights.loc[:low_charge_index].copy()
    df_second = df_energy_insights.loc[low_charge_index+1:].copy()

    # are there any non charged slots?
    if (df_first['charge'] == False).any():
        # with the new filtered dataframe, find the row with the minimum price and charge = False
        min_price_index = df_first.loc[df_first['charge'] == False, 'value_inc_vat'].idxmin()

        # Subtract 1.8 from the 'charge_energy' of the row with the minimum price and change the 'charge' value to True
        df_first.at[min_price_index, 'charged_energy'] -= 1.8
        df_first.at[min_price_index, 'charge'] = True

        # Concatenate the two dataframes back together
        df_result = pd.concat([df_first, df_second])

        # Recalculate the running energy
        df_result = calculate_running_battery_capacity(df_result, battery_remaining_capacity,
                                                                battery_max_capacity, battery_charge_rate_hourly)
        return df_result
    else:
        return df_energy_insights


def calculate_running_battery_capacity(df_energy_insights, battery_remaining_capacity,
                                       battery_max_capacity, battery_charge_rate_hourly):
    df_energy_insights['running_battery_capacity'] = 0.0
    df_energy_insights['_new_charged_energy'] = df_energy_insights['charged_energy']
    for i in range(df_energy_insights.shape[0]):
        if i == 0:
            running_battery_capacity = \
                battery_remaining_capacity - df_energy_insights.loc[i, '_new_charged_energy']
        else:
            diff_from_max = battery_max_capacity - df_energy_insights["running_battery_capacity"][i - 1]

            if diff_from_max < battery_charge_rate_hourly / 2:
                df_energy_insights.loc[i,'_new_charged_energy'] = df_energy_insights['_new_charged_energy'][i] + \
                                                              ((battery_charge_rate_hourly / 2) - diff_from_max)
            running_battery_capacity = df_energy_insights.loc[i - 1, "running_battery_capacity"] - \
                                       df_energy_insights.loc[i, '_new_charged_energy']
        df_energy_insights.loc[i, "running_battery_capacity"] = 0 if running_battery_capacity < 0 else running_battery_capacity
    df_energy_insights = df_energy_insights.drop('_new_charged_energy', axis=1)
    return df_energy_insights


def determine_optimal_charging_periods(df_energy_insights: pd.DataFrame, battery_remaining_capacity: float,
                                       battery_max_capacity: float, lowest_charge_threshold: float,
                                       battery_charge_rate_hourly: float) -> pd.DataFrame:
    """
    Calculates optimal times for charging based on energy costs, battery capacity, and charging rate.

    This function determines the overall energy requirement based on current battery capacity and projected energy usage.
    It calculates the number of charging slots needed based on the energy requirement and the battery's hourly charge rate.
    The function then selects the most cost-effective times for charging and adjusts the charging schedule accordingly.
    It continues to adjust the schedule until the lowest battery capacity threshold is maintained.
    """
    df_energy_insights['charge'] = False
    # Calculate the overall energy requirement
    overall_energy_requirement = round(df_energy_insights['energy'].sum() +
                                       (battery_max_capacity - battery_remaining_capacity), 2)

    # Calculate the number of hours needed to charge the battery, rounding up whole number
    slots_to_charge = math.ceil((overall_energy_requirement / battery_charge_rate_hourly) * 2)

    # Sort the dataframe by price
    df_energy_insights = df_energy_insights.sort_values(by=['value_inc_vat'])

    # Change the first x rows to charge = True, where x = slots_to_charge
    df_energy_insights.iloc[:slots_to_charge, df_energy_insights.columns.get_loc('charge')] = True

    # charge all negative priced slots. Slots that energy company pays customer to use energy
    df_energy_insights.loc[df_energy_insights['value_inc_vat'] < 0, 'charge'] = True

    # Where charge = True, subtract 1.8 from the energy usage, creating a new column called 'charged_energy'
    df_energy_insights['charged_energy'] = np.where(df_energy_insights['charge'],
                                                    df_energy_insights['energy'] - 1.8, df_energy_insights['energy'])

    # Sort the dataframe by index
    df_energy_insights = df_energy_insights.sort_index()

    # Calculate the running energy
    df_energy_insights = calculate_running_battery_capacity(df_energy_insights, battery_remaining_capacity,
                                       battery_max_capacity, battery_charge_rate_hourly)
    for _ in range(30):
        if df_energy_insights['running_battery_capacity'][2:].min() < lowest_charge_threshold:
            df_energy_insights = optimize_charging_for_low_capacity(df_energy_insights, battery_remaining_capacity,
                                                                    lowest_charge_threshold, battery_max_capacity,
                                                                    battery_charge_rate_hourly)
        else:
            break
    return df_energy_insights


def calculate_charge_windows(offline_debug, aws_fields, cloudwatch):
    """
    The core calculation function
    """
    giv_energy = GivEnergy(offline_debug, get_secret_or_env("GE_API_KEY"))
    forecast = Forecast(offline_debug, get_secret_or_env("DATAPOINT_API_KEY"))
    time_offsets = get_time_offsets()

    df_energy_result, giv_energy = calculate_battery_depletion_time(giv_energy,
                                                                    forecast,
                                                                    time_offsets)

    # filter Octopus data to find the cheapest value in time frame available
    octopus = Octopus(offline_debug, get_secret_or_env("OCTOPUS_API_KEY"))
    df_agile_data = get_agile_data(octopus, time_offsets)

    df_energy_insights = concat_data_sources(df_energy_result, df_agile_data)
    df_energy_insights = determine_optimal_charging_periods(df_energy_insights,
                                                  giv_energy.system_specs["battery_spec"][
                                                      "battery_kwatt_hours_remaining"],
                                                  giv_energy.system_specs["battery_spec"]["watt_hour"] / 1000,
                                                  lowest_charge_threshold,
                                                  giv_energy.system_specs["battery_spec"][
                                                      "max_charge_rate_watts"] / 1000
                                                  )

    df_energy_insight_windows = df_energy_insights[df_energy_insights['charge'] == True].copy()

    if len(df_energy_insight_windows.index) > 0:
        df_energy_insight_windows = prepare_time_windows_for_givenergy(df_energy_insight_windows, time_offsets)

        # Set the first time window, send the following windows to cloudwatch
        update_inverter_charge_time(giv_energy, offline_debug,
                                    df_energy_insight_windows.iloc[0]["from_hours_giv"],
                                    df_energy_insight_windows.iloc[0]["too_hours_giv"])

        cloud_watch_times = df_energy_insight_windows[['from_hours_giv', 'too_hours_giv', 'from_hours_aws', 'too_hours_aws']].to_dict('records')
        cloud_watch_times = update_cloud_watch(cloudwatch, cloud_watch_times, aws_fields)

        # analyse_data(df_house_consumption, df_solar_production)
        times = df_energy_insight_windows[['from_hours_giv', 'too_hours_giv', 'from_hours_aws', 'too_hours_aws']].to_json(orient='records')
        return times, df_energy_insights
    else:
        return None, df_energy_insights


if __name__ == '__main__':
    aws_fields = {"region": 'eu-west-2',
                  "account_id": '1'}
    calculate_charge_windows(aws_fields)
    # update_inverter_charge_time()
