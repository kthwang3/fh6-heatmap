import json
import boto3
import calendar
from decimal import Decimal
from datetime import datetime, timezone
from botocore.exceptions import ClientError

def handler(event, context):
  try:
    body = json.loads(event['body'])
    machine_uuid = body.get('machine_uuid', 'unknown')

    if 'positions' in body:
      positions = body['positions']
    else:
      positions = [body]

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('fh6-heatmap-table')
    now = datetime.now(tz=timezone.utc)

    for position in positions:
      timestamp = position['timestamp']
      session_id = position['session_id']
      x_pos = Decimal(str(position['x_pos']))
      z_pos = Decimal(str(position['z_pos']))
      car_ordinal = position['car_ordinal']
      car_class = position['car_class']
      car_performance_index = position['car_performance_index']
      table.put_item(
        Item={
          'sessionId': session_id,
          'timestamp': timestamp,
          'x_pos': x_pos,
          'z_pos': z_pos,
          'car_ordinal': car_ordinal,
          'car_class': car_class,
          'car_performance_index': car_performance_index,
          'date': now.strftime('%Y-%m-%d')
        }
      )

    last_day = calendar.monthrange(now.year, now.month)[1]
    end_of_month = datetime(now.year, now.month, last_day, 23, 59, 59, tzinfo=timezone.utc)
    ttl = int(end_of_month.timestamp())

    users_table = dynamodb.Table('fh6-heatmap-users')
    try:
      users_table.put_item(
        Item={'machine_uuid': machine_uuid, 'ttl': ttl},
        ConditionExpression='attribute_not_exists(machine_uuid)'
      )
    except ClientError as my_error:
      if my_error.response['Error']['Code'] != 'ConditionalCheckFailedException':
        raise

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
