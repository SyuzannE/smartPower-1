import json

import boto3


def send_email(offline_debug, email_content):
    if not offline_debug:
        sns_client = boto3.client('sns')
        SNS_TOPIC_ARN = 'arn:aws:sns:eu-west-2:664755504605:smartpower_calculated_windows_daily'

        # data = prepare_email_conent(email_content)

        response = sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject='Log Alert: Calculated windows Detected',
            Message=email_content
            # MessageStructure='raw'
        )
    else:
        print("Sent email with content;")
        print(str(email_content))


def prepare_email_conent(df):
    df = df.drop(columns=['timer', 'hours'])
    html_table = df.to_html(index=False, border=1, justify='left')

    # Define the complete HTML content with the table
    html_content = f"""
    <html>
    <head>
        <style>
            table, th, td {{
                border: 1px solid black;
                border-collapse: collapse;
            }}
            th, td {{
                padding: 5px;
                text-align: left;
            }}
        </style>
    </head>
    <body>
        <h2>Your Table Title</h2>
        {html_table}
    </body>
    </html>
    """
    message = {
        'default': 'This is the default message in case HTML is not supported.',
        'email': html_content
    }

    # Convert the message to JSON format
    return json.dumps(message)