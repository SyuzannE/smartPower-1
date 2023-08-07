# A script that connects to both giv energy and octopus
# Get next days rates
# Checks battery percentage
# Checks prices
# Controls when inverter charges battery

# First get Octopus prices

# prices for Agile go live for next day at 4pm

"""
TODO:
    - make services use example data sets (ability to run offline on same json files)
    - if the service needs to be triggered 2 to 3 times a day, how to design the architecture
    - the service needs to set when it next needs to run.
    - could trigger a cronjob programatically
    - trigger the service every 5/15/30 minutes to check if it should run. TICK
    - lock the function out with a loop until the time wanted comes around

    - get inverter specs (battery capacity, max grid charge)
    - calculate how many hours would be required to charge the batterys to full from empty
    - filter for next days data
    - find x many cheapest time slots for that day
"""
import os

from givenergy import GivEnergy
from octopus import Octopus

offline_debug = True if os.environ.get("OFFLINE_DEBUG") == '1' else False

giv_energy = GivEnergy(offline_debug, os.environ.get("GE_API_KEY"))

system_specifications = giv_energy.system_specs

giv_energy.battery_capacity_voltage = system_specifications['data'][0]['inverter']['info']['battery'][
    'nominal_voltage']
giv_energy.battery_capacity_amp_h = system_specifications['data'][0]['inverter']['info']['battery'][
    'nominal_capacity']
giv_energy.battery_capacity_wh = giv_energy.battery_capacity_voltage * giv_energy.battery_capacity_amp_h

giv_energy.max_charge_rate = system_specifications['data'][0]['inverter']['info']['max_charge_rate']
giv_energy.house_avg_base_load = 300

hours_to_charge = giv_energy.battery_capacity_wh / (giv_energy.max_charge_rate - giv_energy.house_avg_base_load)
print(round(hours_to_charge, 2))

octopus = Octopus(offline_debug, os.environ.get("OCTOPUS_API_KEY"))
agile_data = octopus.get_tariff_data()

print('complete')
# data = giv_energy.get_inverter_systems_data()
# inverter_settings = giv_energy.read_inverter_setting(64)
# print(inverter_settings)
# octopus.save_json_file("agile-18-july", agile_data)

