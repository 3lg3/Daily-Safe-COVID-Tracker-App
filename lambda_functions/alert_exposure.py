import json
import boto3


sqs = boto3.client('sqs')
queue_url = 'https://sqs.us-east-1.amazonaws.com/905863309174/alert-exposure'

def lambda_handler(event, context):
    contacts = ['sr01@columbia.edu', 'ts01@columbia.edu']
    sendToSQS(contacts)
    receivers = pollContacts()
    print(receivers)
    ses = boto3.client('ses')
    ses.send_email(
        Source='zl3029@columbia.edu',
        Destination={
            'ToAddresses': receivers,
        },
        Message={
            'Subject': {
                'Data': 'DailySafe: Exposure Alert!',
                'Charset': "UTF-8"
            },
            'Body':{
                'Text': {
                    'Data': 'You might haven been exposed to COVID virus in the past events! Please login into the DailySafe and have a check!\n',
                    'Charset': "UTF-8"
                }
            }
        }
    )
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
    



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

def pollContacts():
    response = sqs.receive_message(
        QueueUrl=queue_url,
        AttributeNames=["test"],
        MaxNumberOfMessages=1,
        MessageAttributeNames=[
            'All'
        ],
        VisibilityTimeout=0,
        WaitTimeSeconds=0
    )
    if "Messages" in response.keys(): 
        message = response["Messages"][0]
        receipt_handle = message['ReceiptHandle']
        sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=receipt_handle
        )
        return json.loads(message["MessageAttributes"]['contacts']['StringValue'])
    else:
        return None