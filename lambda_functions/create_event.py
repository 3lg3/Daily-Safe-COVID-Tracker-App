import json
import datetime
import boto3
import uuid

db = boto3.resource('dynamodb')
user_table = db.Table('user')
event_table = db.Table('event')


def lambda_handler(event, context):
    # TODO implement
    body = json.loads(event["body"])
    # body = event
    email = body['email']
    user = user_table.get_item(Key={'email': email})['Item']
    # check health status: only allow green people to create event
    color = get_health_status(user)
    date = body['date']
    if color != 'green' or calculate_elapsed_hours(date) > 0:
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
                "Content-Type":"application/json",
            },
            'body': json.dumps('Failed')
        }
    
    # Green people continue to create event
    people = body['people']
    location = body['location']
    name = body['name']
    detail = body['detail']
    eventid = str(uuid.uuid4())   #create a new random eventid for this new event.
    organize_event(eventid, name, email, location, date, people, detail)
    invite_people(people, eventid)
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
            "Content-Type":"application/json",
        },
        'body': json.dumps('Success!')
        }


# Organize the event and populate the new event into event table
# put the eventid into the event list of host (email)
def organize_event(eventid, name, email, location, date, people, detail):
    user_table.update_item(
        Key={'email': email},
        UpdateExpression= "SET event_list = list_append(event_list, :newEvent)",
        ExpressionAttributeValues={
            ':newEvent': [eventid]
            
        },
        ReturnValues="UPDATED_NEW"
    )
    
    nevent = {'eventid': eventid, 
        'host': email, 
        'name': name,
        'location': location, 
        'date': date, 
        'invited_people': people, 
        'joined_people': [email],
        'detail': detail,
        'status_color': 'green'
    }
    response = event_table.put_item(Item = nevent)
    
    return response


# Invite the people to attend the event.
# put the eventid into the pending_event list of invited people
def invite_people(people, eventid):
    for person in people:
        user_table.update_item(
            Key={'email': person},
            UpdateExpression= "SET pending_event = list_append(pending_event, :newEvent)",
            ExpressionAttributeValues={
                ':newEvent': [eventid]
                
            },
            ReturnValues="UPDATED_NEW"
    )
    

# return the health status : green / yellow / red
# Input: JSON object of current user with primary key equal to input email 
def get_health_status(user):
    elapsed_hours = calculate_elapsed_hours(user['last_health_report_date'])
    if user['consecutive_days'] >= 7 and elapsed_hours <= 48:
        return 'green'
    elif user['red_flag']:
        return 'red'
    # elapsed hour larger than 48 and clear the previous consecutive_days
    elif elapsed_hours > 48:
        user_table.update_item(
            Key={'email': user['email']},
            UpdateExpression="SET consecutive_days = :newDays",
            ExpressionAttributeValues={
                ':newDays': 0,
            },
            ReturnValues="UPDATED_NEW"
        )
        return 'yellow'
    # less thant 7 consecutive days but elapsed hour smaller than 48 hours.
    else:
        return 'yellow'


# return elapsed hours from last health report date
# Input: String format "%Y-%m-%d %H:%M:%S.%f"
def calculate_elapsed_hours(recorded_time):
    input_time = datetime.datetime.strptime(recorded_time,"%Y-%m-%d %H:%M:%S.%f")
    now = datetime.datetime.now()
    return (now - input_time).total_seconds() // 3600