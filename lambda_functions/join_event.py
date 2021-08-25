import json
import datetime
import boto3

db = boto3.resource('dynamodb')
user_table = db.Table('user')
event_table = db.Table('event')

def lambda_handler(event, context):
    # TODO implement
    body = json.loads(event["body"])
    # body = event
    email = body['email']
    eventid = body['eventid']
    user = user_table.get_item(Key={'email': email})['Item']
    # check health status: only allow green people to join event
    color = get_health_status(user)
    if color != 'green':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
            },
            'body': json.dumps('Failed')
        }
        
    # update the user
    pending_event = user['pending_event']
    pending_event.remove(eventid)
    event_list = user['event_list']
    event_list.append(eventid)
    user_table.update_item(
        Key={'email': email},
        UpdateExpression="SET pending_event = :newPendingevent, event_list = :newEventList",
        ExpressionAttributeValues={
            ':newPendingevent': pending_event,
            ':newEventList': event_list
        },
        ReturnValues="UPDATED_NEW"
    )
    
    # update the event
    event_table.update_item(
        Key={'eventid': eventid},
        UpdateExpression= "SET joined_people = list_append(joined_people, :newPerson)",
        ExpressionAttributeValues={
            ':newPerson': [email]
        },
        ReturnValues="UPDATED_NEW"
    )
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
        },
        'body': json.dumps('Success')
    }

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