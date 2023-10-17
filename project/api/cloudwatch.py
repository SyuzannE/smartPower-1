# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/cw-example-events.html

import json
import logging
from typing import Dict

import boto3


# Initialize the Boto3 client
events_client = boto3.client('events')
lambda_client = boto3.client('lambda')
function_name = 'calculate_charge_times'

logger = logging.getLogger(__name__)


def create_cron(set_time: str, time_adjust: int) -> str:
    """
    Create a cron schedule to run everyday at a specified time, with an optional adjustment.

    :param set_time: Time in 'H:M' format.
    :param time_adjust: Hour adjustment which can be positive or negative.
    :return: A cron schedule string.
    """
    hours, minutes = map(int, set_time.split(':'))  # Convert str to int directly after splitting

    # Adjust hours and handle wraparound
    hours = int((hours - time_adjust) % 24)

    logger.info(f"CloudWatch cron schedule set to {hours:02d}:{minutes:02d}")

    # Return the cron schedule string with zero-padded hours and minutes
    return f'cron({minutes:01d} {hours:01d} * * ? *)'


def create_event(too_hours: str,
                 time_adjust: int,
                 aws_fields: Dict[str, str],
                 input_json: Dict) -> None:
    """
    Creates a CloudWatch Event based on the specified hour and minute, adjusted
    by a time offset. This event then triggers an AWS Lambda function with the
    provided input JSON payload.
    """
    cron_expression = create_cron(too_hours, time_adjust)
    send_update(cron_expression, 'ENABLED', aws_fields, input_json)


def send_update(cron_expression: str,
                state: str,
                aws_fields: Dict[str, str],
                input_json: Dict) -> None:
    """
    Sends an update by creating or updating a CloudWatch Event rule and linking
    this rule to a specific Lambda function. The CloudWatch Event rule triggers
    based on a provided cron expression.

    Parameters:
    - cron_expression (str): The cron expression defining when the rule triggers.
                             Should be in valid cron format.
    - state (str): Desired state of the rule, either "ENABLED" or "DISABLED".
    - aws_fields (dict): Contains AWS-specific fields. Must include 'region' and 'account_id'.
        - region (str): The AWS region where the Lambda function resides.
        - account_id (str): The AWS account ID that owns the Lambda function.
    - input_json (dict): The input payload that will be passed to the Lambda
                         function when the rule triggers.

    Returns:
    None. But will cause side-effects in AWS resources (creating or updating rules).

    Note:
    This function assumes `events_client` is an initialized client for AWS CloudWatch Events
    and that `function_name` is globally defined or available in the surrounding context.
    """
    response = events_client.put_rule(
        Name=function_name + "-trigger",
        ScheduleExpression=cron_expression,
        State=state
    )
    # Link the CloudWatch Event rule to the Lambda function
    events_client.put_targets(
        Rule=function_name + "-trigger",
        Targets=[
            {
                'Id': function_name + "-target",
                'Arn': f"arn:aws:lambda:{aws_fields['region']}:{aws_fields['account_id']}:function:{function_name}",
                'Input': json.dumps(input_json)
            }
        ]
    )


