# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/cw-example-events.html

import json
import logging
from typing import Dict

import boto3

logger = logging.getLogger(__name__)


class CloudWatch:
    def __init__(self, offline_debug):
        self.offline_debug = offline_debug
        self.events_client = boto3.client('events')
        self.lambda_client = boto3.client('lambda')
        self.function_name = 'calculate_charge_times'

    def create_event(self,
                     too_hours: str,
                     aws_fields: Dict[str, str],
                     input_json: Dict) -> None:
        """
        Creates a CloudWatch Event based on the specified hour and minute, adjusted
        by a time offset. This event then triggers an AWS Lambda function with the
        provided input JSON payload.
        """
        cron_expression = self.create_cron(too_hours)
        self.send_update(cron_expression, 'ENABLED', aws_fields, input_json)

    def create_cron(self, set_time: str) -> str:
        """
        Create a cron schedule to run everyday at a specified time, with an optional adjustment.

        :param set_time: Time in 'H:M' format.
        :param time_adjust: Hour adjustment which can be positive or negative.
        :return: A cron schedule string.
        """
        hours, minutes = map(int, set_time.split(':'))  # Convert str to int directly after splitting

        # Adjust hours and handle wraparound
        hours = int((hours) % 24)

        logger.info(f"CloudWatch cron schedule set to {hours:02d}:{minutes:02d}")

        # Return the cron schedule string with zero-padded hours and minutes
        return f'cron({minutes:01d} {hours:01d} * * ? *)'

    def send_update(self,
                    cron_expression: str,
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
        if not self.offline_debug:
            response = self.events_client.put_rule(
                Name=self.function_name + "-trigger",
                ScheduleExpression=cron_expression,
                State=state
            )
            # Link the CloudWatch Event rule to the Lambda function
            self.events_client.put_targets(
                Rule=self.function_name + "-trigger",
                Targets=[
                    {
                        'Id': self.function_name + "-target",
                        'Arn': f"arn:aws:lambda:{aws_fields['region']}:{aws_fields['account_id']}:function:{self.function_name}",
                        'Input': json.dumps(input_json)
                    }
                ]
            )
        else:
            print(f"Sent updated event to cloudwatch: {input_json}")

