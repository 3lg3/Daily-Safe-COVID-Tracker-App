import json
import datetime
import requests
import boto3
import uuid

db = boto3.resource('dynamodb')
user_table = db.Table('user')
event_table = db.Table('event')


sqs = boto3.client('sqs')
queue_url = 'https://sqs.us-east-1.amazonaws.com/905863309174/alert-exposure'


# event input format: { "email": "ts01@columbiaedu", "answers": [true, true]}
def lambda_handler(event, context):
    body = json.loads(event["body"])
    # body = event
    email = body['email']
    answers = body['answers']
    user = user_table.get_item(Key={'email': email})['Item']
    if any(answers):
        # if the user turns from green(red_flag = false) to red (red_flag = true), then mark all his events as red
        if not user['red_flag']:
            mark_events(user)
        
        response = submit_red_report(user)
    else:
        response = submit_green_report(user)
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
        },
        'body': json.dumps("success")
        }


def mark_events(user):
    events_to_red = user['event_list']
    direct_contacts = []
    for eid in events_to_red:
        curr = event_table.get_item(Key={'eventid': eid})['Item']
        elapsed_hours = calculate_elapsed_hours(curr['date'])
        if elapsed_hours > 0 and elapsed_hours <= 336:
            print('eventid:', eid, 'turnss to red!')
            event_table.update_item(
                Key={'eventid': eid},
                UpdateExpression="SET status_color = :newStatus",
                ExpressionAttributeValues={
                    ':newStatus': 'red',
                },
                ReturnValues="UPDATED_NEW"
            )
            direct_contacts += curr['joined_people']
    
    # remove himself from direct contacts and the duplicates
    direct_contacts = list(set(direct_contacts))
    if user['email'] in direct_contacts:
        direct_contacts.remove(user['email'])
        
    indirect_contacts = []
    print('direct contacts:', direct_contacts)
    for pid in direct_contacts:
        person = user_table.get_item(Key={'email': pid})['Item']
        events_to_pink = person['event_list']
        for eid in events_to_pink:
            curr = event_table.get_item(Key={'eventid': eid})['Item']
            elapsed_hours = calculate_elapsed_hours(curr['date'])
            if curr['status_color'] != 'red' and elapsed_hours > 0 and elapsed_hours <= 336:
                print('eventid:', eid, 'turnss to pink!')
                event_table.update_item(
                    Key={'eventid': eid},
                    UpdateExpression="SET status_color = :newStatus",
                    ExpressionAttributeValues={
                        ':newStatus': 'pink',
                    },
                    ReturnValues="UPDATED_NEW"
                )
                indirect_contacts += curr['joined_people']
                
    # all user contacts(email) that needs to alert
    contacts = list(set(direct_contacts + indirect_contacts))
    sendToSQS(contacts)
            
def submit_green_report(user):
    email = user['email']
    days = user['consecutive_days'] + 1
    flag = user['red_flag']
    if days >= 7:
        flag = False
    now = str(datetime.datetime.now())
    response = user_table.update_item(
        Key={'email': email},
        UpdateExpression="SET consecutive_days = :newDays, last_health_report_date = :newDate, red_flag = :newFlag",
        ExpressionAttributeValues={
            ':newDays': days,
            ':newDate': now,
            ':newFlag': flag
            
        },
        ReturnValues="UPDATED_NEW"
    )
    return response

def submit_red_report(user):
    email = user['email']
    now = str(datetime.datetime.now())
    response = user_table.update_item(
        Key={'email': email},
        UpdateExpression="SET consecutive_days = :newDays, last_health_report_date = :newDate, red_flag = :newFlag",
        ExpressionAttributeValues={
            ':newDays': 0,
            ':newDate': now,
            ':newFlag': True
            
        },
        ReturnValues="UPDATED_NEW"
    )
    return response

def calculate_elapsed_hours(recorded_time):
    input_time = datetime.datetime.strptime(recorded_time,"%Y-%m-%d %H:%M:%S.%f")
    now = datetime.datetime.now()
    return (now - input_time).total_seconds() // 3600


def sendToSQS(contacts):
    # Send message to SQS queue
    response = sqs.send_message(
        QueueUrl=queue_url,
        DelaySeconds=10,
        MessageAttributes={
            'contacts': {
                'DataType': 'String',
                'StringValue': json.dumps(contacts)
            }
        },
        MessageBody=(
            'sending contacts to alert'
        )
    )
    return response