import json
import datetime
import json
import boto3
import datetime
import uuid

db = boto3.resource('dynamodb')
user_table = db.Table('user')
event_table = db.Table('event')
location_table=db.Table('location')

def lambda_handler(event, context):
    # TODO implement
    body = json.loads(event["body"])
    # body = event
    email = body['email']
    time = body['time']
    # Start create location
    location_name = body['location']
    user = user_table.get_item(Key={'email': email})['Item']
    location = location_table.get_item(Key={'name': location_name})['Item']
    # If there is no past event for this location or elapsed time longer than 4 hours
    # create a new 4-hour interval event for this location
    location_events = location['location_events']
    event_found = check_events(location_events, time)
    if event_found is None:
        eventid = str(uuid.uuid4())
        eventname = location_name + ' * CHECKIN'
        eventtime = time
        eventdetail = 'People checkin within 4-hour window in the same public location would be treated as in one event.'
        organize_event(eventid, eventname, email, location['address'] + ', New York', eventtime, [], eventdetail)
        location_table.update_item(
            Key={'name': location_name},
            UpdateExpression="SET location_events = list_append(location_events, :newEvent)",
            ExpressionAttributeValues={
                ':newEvent': [eventid],
            },
            ReturnValues="UPDATED_NEW"
        )
    # If there is a past event for this location and the elasped time is within 4 hours
    # join the found event
    else:
        # update user event_list
        event_list = user['event_list']
        for eventid in event_found:
            if eventid not in event_list:
                event_list.append(eventid)
                user_table.update_item(
                    Key={'email': email},
                    UpdateExpression="SET event_list = :newEventList",
                    ExpressionAttributeValues={
                        ':newEventList': event_list
                    },
                    ReturnValues="UPDATED_NEW"
                )
                
                # update event joined_people
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
        'body': json.dumps('Success!')
    }     
 



def check_events(location_events, time):
    if len(location_events) == 0:
        return None
    
    result = []
    for eid in location_events:
        curr = event_table.get_item(Key={'eventid': eid})['Item'] 
        time_gap = abs(calculate_elapsed_hours(time, curr['date']))
        if time_gap <= 4:
            result.append(eid)
    
    if len(result) > 0:
        return result

    return None
    
            







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

# return elapsed hours from prevTime to currTime
# Input: String format "%Y-%m-%d %H:%M:%S.%f"
def calculate_elapsed_hours(currTime, prevTime):
    currTime = datetime.datetime.strptime(currTime,"%Y-%m-%d %H:%M:%S.%f")
    prevTime = datetime.datetime.strptime(prevTime,"%Y-%m-%d %H:%M:%S.%f")
    return (currTime - prevTime).total_seconds() // 3600