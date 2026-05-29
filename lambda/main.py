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
    car_ordinal = eventDict['car_ordinal']
    car_class = eventDict['car_class']
    car_performance_index = eventDict['car_performance_index']

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('fh6-heatmap-table')
    
    response = table.put_item(
      Item = {
        'sessionId': session_id,
        'timestamp': timestamp,
        'x_pos': x_pos,
        'z_pos': z_pos,
        'car_ordinal': car_ordinal,
        'car_class': car_class,
        'car_performance_index': car_performance_index
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
  except Exception as error:
    print(error)
    return {
        "statusCode": 500,
        "body": json.dumps({"message": str(error)})
    }
