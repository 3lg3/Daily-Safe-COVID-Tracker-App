import json
import datetime
import boto3

db = boto3.resource('dynamodb')
user_table = db.Table('user')
event_table = db.Table('event')

def lambda_handler(event, context):
    # TODO implement
    result = []
    email = event['queryStringParameters']['q']
    user = user_table.get_item(Key={'email': email})['Item']
    event_list = user['event_list'].copy()
    for eid in event_list:
        curr = event_table.get_item(Key={'eventid': eid})['Item']
        # append incoming eventid to the result list
        if calculate_elapsed_hours(curr['date']) < 0:
            result.append(curr)
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
        },
        'body': json.dumps(result)
    }


# return elapsed hours from last health report date
# Input: String format "%Y-%m-%d %H:%M:%S.%f"
def calculate_elapsed_hours(recorded_time):
    input_time = datetime.datetime.strptime(recorded_time,"%Y-%m-%d %H:%M:%S.%f")
    now = datetime.datetime.now()
    return (now - input_time).total_seconds() // 3600