import json
import datetime
import boto3

db = boto3.resource('dynamodb')
user_table = db.Table('user')
def lambda_handler(event, context):
    now = datetime.datetime.now()
    email = event['request']['userAttributes']['email']
    curr = {
        'email': email, 
        'name':  email.split('@')[0], 
        'event_list': [],
        'pending_event': [],
        'last_health_report_date': str(now),
        'consecutive_days': 0,
        'red_flag': False
    }
    user_table.put_item(Item = curr)
    
    event['response']['autoConfirmUser'] = True

    # Set the email as verified if it is in the request
    if 'email' in event['request']['userAttributes']:
        event['response']['autoVerifyEmail'] = True

    # Set the phone number as verified if it is in the request
    if 'phone_number' in event['request']['userAttributes']:
        event['response']['autoVerifyPhone'] = True
    
    return event

    
