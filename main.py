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
    - trigger the service every 5/15/30 minutes to check if it should run. TICK

    - get inverter specs (battery capacity, max grid charge)
    - calculate how many hours would be required to charge the batterys to full from empty
    - filter for next days data
    - find x many cheapest time slots for that day

Charging logic
    - e.g. 10.10pm, 65% charge, cheapest rate is following day between lunch 1.30 - 2, and 2.30 - 3.
    - what would be the expected battery charge by the time we get to 1.30 tomorrow
    - how long would it take to charge to full
    - if additional charge is going to be needed in order to get to the cheapest rate, what cheaper rates are available before hand
    - perhaps better to calculate the latest estimated time that will need to charge from grid, factor in time of year, day of week, solar estimation etc
    - compare with agile rates

    - get the last 4 weekday electricity houe usage and average per half hour slot
    - e.g. the last 4 Tuesday usage in half hour slots
    - 2 week holiday is going to produce outliers. how to deal with this?
"""
import os

from givenergy import GivEnergy
from octopus import Octopus

offline_debug = True if os.environ.get("OFFLINE_DEBUG") == '1' else False

giv_energy = GivEnergy(offline_debug, os.environ.get("GE_API_KEY"))

giv_energy.extract_system_spec()

print(giv_energy.system_specs)



octopus = Octopus(offline_debug, os.environ.get("OCTOPUS_API_KEY"))
agile_data = octopus.get_tariff_data()

print('complete')
# data = giv_energy.get_inverter_systems_data()
# inverter_settings = giv_energy.read_inverter_setting(64)
# print(inverter_settings)
# octopus.save_json_file("agile-18-july", agile_data)

