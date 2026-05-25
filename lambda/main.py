import json
import boto3
from decimal import Decimal

def handler(event, context):
  try:
    eventDict = json.loads(event['body'])
    timestamp = eventDict['timestamp']
    session_id = eventDict['session_id']
    x_pos = Decimal(str(eventDict['x_pos']))
    z_pos = Decimal(str(eventDict['z_pos']))

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('fh6-heatmap-table')
    
    response = table.put_item(
      Item = {
        'sessionId': session_id,
        'timestamp': timestamp,
        'x_pos': x_pos,
        'z_pos': z_pos
      }
    )
    return {
      "statusCode": 200,
      "body": json.dumps({"message": "Success"})
    }
  except(KeyError, json.JSONDecodeError):
    return{
      "statusCode": 400,
      "body": json.dumps({"message": "Invalid Request"})
    }