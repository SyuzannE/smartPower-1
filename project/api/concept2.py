import math
import numpy as np
import pandas as pd

from project.example_responses.example_data_handler import CalculatedData

"""
Problem is that may limit you to say 1 half hour slot every 5 slots. It might be cheaper to look at the day as a whole. 
Work out how many slots are going to be needed to keep the charge at 95% by the end of the day and never drop below 30%.
That gives you x amount of cheapest slots.
Once the cheapest slots are chosen, are there likely to be any slots where the battery charge depletes less than 3kwh?
If so, more slots should be added before that estimated time. Repeat until the battery stays above the 3kwh threshold
for the rest of the day

How much energy is needed on the average day
What is the current battery charge. 
Overall energy requirement = average day + (battery max charge - current battery charge)
Charge rate of 3.6kwh per hour.
How many hours are needed to charge the battery, *2 for half hour slots
Choose the x cheapest slots, subtract 1.8kwh to the estimated energy usage for each selected charging slot
Then cumulatively start at midnight with the current battery charge and take off the estimated energy usage until the
battery charge is less than 30%
If the battery charge drops below 30% at any point,
Filter the dataframe to only include the rows up to that point
Find the row with the minimum price that is not current selected for charging
Make it a charged slot and subtract 1.8kwh from the estimated energy usage
Repeat until the battery charge stays above 30% for the rest of the day
"""

# Your initial battery charge in kWh
# battery_charge = 4.0
# max_battery_charge = 8
battery_charge_rate_hourly = 3.6
lowest_charge_threshhold = 3.0

df = CalculatedData.read_energy_data()
df['charge'] = False


def add_additional_charging(df_energy_insights, battery_remaining_capacity):
    # Find the first row, i.e the lowest index row where the running energy drops below 2
    low_charge_index = df_energy_insights.loc[df_energy_insights['running_energy'] < lowest_charge_threshhold].index[0]

    # then filter the dataframe with that rows index
    df_first = df_energy_insights.loc[:low_charge_index].copy()
    df_second = df_energy_insights.loc[low_charge_index:].copy()

    # with the new filtered dataframe, find the row with the minimum price and charge = False
    min_price_index = df_first.loc[df_first['charge'] == False, 'value_inc_vat'].idxmin()

    # Subtract 1.8 from the 'charge_energy' of the row with the minimum price and change the 'charge' value to True
    df_first.at[min_price_index, 'charged_energy'] -= 1.8
    df_first.at[min_price_index, 'charge'] = True

    # Concatenate the two dataframes back together
    df_result = pd.concat([df_first, df_second])

    # Recalculate the running energy
    df_result['running_energy'] = battery_remaining_capacity - df_result['charged_energy'].cumsum()
    return df_result


def calculate_charging_times(df_energy_insights, battery_remaining_capacity, battery_max_capacity):
    # Calculate the overall energy requirement
    overall_energy_requirement = round(df_energy_insights['energy'].sum() +
                                       (battery_max_capacity - battery_remaining_capacity), 2)

    # Calculate the number of hours needed to charge the battery, rounding up whole number
    slots_to_charge = math.ceil((overall_energy_requirement / battery_charge_rate_hourly) * 2)

    # Sort the dataframe by price
    df_energy_insights = df_energy_insights.sort_values(by=['value_inc_vat'])

    # Change the first x rows to charge = True, where x = slots_to_charge
    df_energy_insights.iloc[:slots_to_charge, df_energy_insights.columns.get_loc('charge')] = True

    # Where charge = True, subtract 1.8 from the energy usage, creating a new column called 'charged_energy'
    df_energy_insights['charged_energy'] = np.where(df_energy_insights['charge'],
                                                    df_energy_insights['energy'] - 1.8, df_energy_insights['energy'])
    # Sort the dataframe by index
    df_energy_insights = df_energy_insights.sort_index()

    # Calculate the running energy
    df_energy_insights['running_energy'] = battery_remaining_capacity - df_energy_insights['charged_energy'].cumsum()

    # Does the running energy ever drop below lowest threshhold?
    while True:
        if df_energy_insights['running_energy'].min() < lowest_charge_threshhold:
            df_energy_insights = add_additional_charging(df_energy_insights)
        else:
            break


