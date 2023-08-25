# import boto3
# import json
# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/cw-example-events.html


# def put_rule():
#     # Create CloudWatchEvents client
#     cloudwatch_events = boto3.client('events')
#
#     # Put an event rule
#     response = cloudwatch_events.put_rule(
#         Name='DEMO_EVENT',
#         RoleArn='IAM_ROLE_ARN',
#         ScheduleExpression='rate(5 minutes)',
#         State='ENABLED'
#     )
#     print(response['RuleArn'])
#
#
# def put_target():
#     # Create CloudWatchEvents client
#     cloudwatch_events = boto3.client('events')
#
#     # Put target for rule
#     response = cloudwatch_events.put_targets(
#         Rule='DEMO_EVENT',
#         Targets=[
#             {
#                 'Arn': 'LAMBDA_FUNCTION_ARN',
#                 'Id': 'myCloudWatchEventsTarget',
#             }
#         ]
#     )
#     print(response)
#
#
# def send_events():
#     # Create CloudWatchEvents client
#     cloudwatch_events = boto3.client('events')
#
#     # Put an event
#     response = cloudwatch_events.put_events(
#         Entries=[
#             {
#                 'Detail': json.dumps({'key1': 'value1', 'key2': 'value2'}),
#                 'DetailType': 'appRequestSubmitted',
#                 'Resources': [
#                     'RESOURCE_ARN',
#                 ],
#                 'Source': 'com.company.myapp'
#             }
#         ]
#     )
#     print(response['Entries'])
#

# chatgpt

import boto3
import json

# Initialize the Boto3 client
events_client = boto3.client('events')
lambda_client = boto3.client('lambda')
function_name = 'calculate_charge_times'


def create_event(too_hours, time_adjust, aws_fields, input_json):
    hours, minutes = too_hours.split(':')
    hours = str(int(hours) + time_adjust)
    minutes = str(int(minutes))

    cron_expression = f'cron({minutes} {hours} * * ? *)'
    arn = f"arn:aws:lambda:{aws_fields['region']}:{aws_fields['account_id']}:function:{function_name}"

    # # Grant CloudWatch Events permission to invoke the Lambda function
    # lambda_client.add_permission(
    #     FunctionName=function_name,
    #     StatementId=f"{function_name}-Event",
    #     Action='lambda:InvokeFunction',
    #     Principal='events.amazonaws.com'
    # )
    send_update(cron_expression, 'ENABLED', aws_fields, input_json)


def send_update(cron_expression, state, aws_fields, input_json):
    # Create or update the CloudWatch Event rule
    response = events_client.put_rule(
        Name=function_name + "-trigger",
        ScheduleExpression=cron_expression,
        State=state
    )
    # rule_arn = response['RuleArn']

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


