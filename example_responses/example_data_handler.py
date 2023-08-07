import json
import os


def get_data(file_name):
    """
    A function that corrects the file path, adds in the file name and returns a json file as a dict
    """
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name)
    with open(file_path) as file:
        data = json.load(file)
    return data


class GivEnergyData:
    @staticmethod
    def communication_device():
        return get_data('communication_device.json')

    @staticmethod
    def inverter_settings():
        return get_data('inverter_settings.json')

    @staticmethod
    def read_inverter_setting():
        return get_data('read_setting.json')


class OctopusData:
    @staticmethod
    def agile_tariff():
        return get_data('AGILE-18-02-21.json')