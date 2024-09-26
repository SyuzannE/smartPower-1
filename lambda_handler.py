import logging
import os

import boto3

from main import calculate_charge_windows, update_inverter_charge_time, update_cloud_watch, get_time_offsets

from project.api.cloudwatch import CloudWatch
from project.api.givenergy import GivEnergy
from project.secrets import get_secret_or_env
from project.api.sns_email import send_email

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
    offline_debug = True if os.environ.get("OFFLINE_DEBUG") == 'true' else False
    cloudwatch = CloudWatch(offline_debug)
    if msg == 'calculate':
        logger.info("event command: Calculate")
        charge_times, df_energy_insights = calculate_charge_windows(offline_debug, aws_fields, cloudwatch)
        logger.info(f"Calculated charge windows: {charge_times}")
        send_email(offline_debug, charge_times)

        return charge_times
    elif msg == 'update':
        logger.info("event command: Update")
        data = event["data"]
        giv_energy = GivEnergy(offline_debug, get_secret_or_env("GE_API_KEY"))
        update_inverter_charge_time(giv_energy, offline_debug,
                                    data[0]['from_hours_giv'],
                                    data[0]['too_hours_giv'])
        updated_charge_times = update_cloud_watch(cloudwatch, data, aws_fields)
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
