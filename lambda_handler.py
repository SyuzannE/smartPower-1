import logging
import os

from main import calculate_charge_windows, update_inverter_charge_time, update_cloud_watch, get_time_offsets

from project.api.givenergy import GivEnergy
from project.secrets import get_secret_or_env

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    if context:
        arn = context.invoked_function_arn
    else:
        arn = "a:b:c:d:e:f"
    aws_fields = {"region": arn.split(":")[3],
                  "account_id": arn.split(":")[4]}
    msg = event["msg"]
    if msg == 'calculate':
        charge_times = calculate_charge_windows(aws_fields)
        logger.info(f"Calculated charge windows: {charge_times}")
        return charge_times
    elif msg == 'update':
        data = event["data"]
        offline_debug = True if os.environ.get("OFFLINE_DEBUG") == 'true' else False
        giv_energy = GivEnergy(offline_debug, get_secret_or_env("GE_API_KEY"))
        update_inverter_charge_time(giv_energy, offline_debug,
                                    data[0]['from_hours'],
                                    data[0]['too_hours'])
        updated_charge_times = update_cloud_watch(data, get_time_offsets(), aws_fields)
        logger.info(updated_charge_times)
        return updated_charge_times
    else:
        return {
            'message': 'unknown command'
        }


if __name__ == '__main__':
    # event = {
    #     "msg": "update",
    #     "data": [
    #         {
    #             "from_hours": "05:30",
    #             "too_hours": "06:00"
    #         },
    #         {
    #             "from_hours": "22:30",
    #             "too_hours": "23:00"
    #         }
    #     ]
    # }
    event = {
        "msg": "calculate",
        "data": ""
    }
    handler(event, None)
