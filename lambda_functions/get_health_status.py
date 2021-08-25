import json
import datetime
import boto3

db = boto3.resource('dynamodb')
user_table = db.Table('user')
event_table = db.Table('event')

# event format: { "email": "ts01@columbia.edu"}
def lambda_handler(event, context):
    # TODO implement
    # email = event['email']
    email = event['queryStringParameters']['q']
    user = user_table.get_item(Key={'email': email})['Item']
    elapsed_hours = calculate_elapsed_hours(user['last_health_report_date'])
    print('elapsed_hours:', elapsed_hours)
    health_status = get_health_status(user)
    print('health_status:', health_status)
   
    # mark yellow events if user is yellow
    if health_status == 'yellow':
        event_list = user['event_list']
        for eid in event_list:
            curr = event_table.get_item(Key={'eventid': eid})['Item']
            if curr['status_color'] == 'green':
                event_table.update_item(
                    Key={'eventid': eid},
                    UpdateExpression="SET status_color = :newStatus",
                    ExpressionAttributeValues={
                        ':newStatus': 'yellow',
                    },
                    ReturnValues="UPDATED_NEW"
                )
        

    result = {'health_status': health_status, 'elapsed_hours': elapsed_hours}
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
        
    





def test_insert():
    now = datetime.datetime.now()
    ntime = now - datetime.timedelta(hours=12, minutes=23, seconds=10)
    curr = {
        'email': 'sr01@columbia.edu', 
        'name': 'Steven Rogers', 
        'event_list': [],
        'last_health_report_date': str(ntime),
        'consecutive_days': 8,
        'red_flag': False
    }
    user_table.put_item(Item = curr)