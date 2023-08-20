from main import calculate_charge_windows, update_inverter_charge_time


def handler(event, context):
    # print(event)
    # if event is not None:
    #     msg, data = event['message'], event['data']
    #     if msg == "calculate":
    #         calculate_charge_windows()
    #     #      update cloud watch
    #     elif msg == 'send updates':
    #         # unpack data
    #         update_inverter_charge_time(1, 2)
    calculate_charge_windows()
    return 'Hello from AWS Lambda using Python'


if __name__ == '__main__':
    calculate_charge_windows()
