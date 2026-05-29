import json
import boto3
import time

FACTOR_X = 3.5131
OFFSET_X = 3244
FACTOR_Y = -3.512
OFFSET_Y = 3061
IMAGE_SIZE = 6144
#number of columns and rows, not meters per grid square
GRID_W = 200
GRID_H = 200

def handler(event, context):
  dynamodb = boto3.resource('dynamodb')
  table = dynamodb.Table('fh6-heatmap-table')

  paramsDict = event['queryStringParameters'] or {}
  timeFilter = paramsDict.get('range')

  items = []
  response = table.scan()
  items += response['Items']
  #bookmark last key and continue until all data is read
  while 'LastEvaluatedKey' in response:
    response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
    items += response['Items']
  
  current_time_ms = time.time() * 1000  
  if timeFilter == 'week':
    cutoff = current_time_ms - 7 * 24 * 60 * 60 * 1000
    filtered_items = []
    for item in items:
      if int(item['timestamp']) >= cutoff:
        filtered_items.append(item)
  elif timeFilter == 'month':
    cutoff = current_time_ms - 31 * 24 * 60 * 60 * 1000
    filtered_items = []
    for item in items:
      if int(item['timestamp']) >= cutoff:
        filtered_items.append(item)
  else: 
    filtered_items = items
  
  grid = [[0] * GRID_W for _ in range(GRID_H)]

  for item in filtered_items:
    x = float(item['x_pos'])
    z = float(item['z_pos'])
    col = int((x / FACTOR_X + OFFSET_X) / IMAGE_SIZE * GRID_W)
    row = int((z / FACTOR_Y + OFFSET_Y) / IMAGE_SIZE * GRID_H)
    if 0 <= col < GRID_W and 0 <= row < GRID_H:
      grid[row][col] += 1
  
  return {
    'statusCode': 200,
    'headers':{'Access-Control-Allow-Origin': '*'},
    'body': json.dumps({'grid': grid})
  }