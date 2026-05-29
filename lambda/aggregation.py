import json
import boto3

FACTOR_X = 3.5131
OFFSET_X = 3244
FACTOR_Y = -3.512
OFFSET_Y = 3061
IMAGE_SIZE = 6144
GRID_W = 100
GRID_H = 100

def handler(event, context):
  dynamodb = boto3.resource('dynamodb')
  table = dynamodb.Table('fh6-heatmap-table')

  items = []
  response = table.scan()
  items += response['Items']
  #bookmark last key and continue until all data is read
  while 'LastEvaluatedKey' in response:
    response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
    items += response['Items']
  
  grid = [[0] * GRID_W for _ in range(GRID_H)]

  for item in items:
    x = float(item['x_pos'])
    z = float(item['z_pos'])
    col = int((x - X_MIN) / (X_MAX - X_MIN) * GRID_W)
    row = int((z- Z_MIN) / (Z_MAX - Z_MIN) * GRID_H)
    if 0 <= col < GRID_W and 0 <= row < GRID_H:
      grid[row][col] += 1
  
  return {
    'statusCode': 200,
    'headers':{'Access-Control-Allow-Origin': '*'},
    'body': json.dumps({'grid': grid, 'x_min': X_MIN, 'x_max': X_MAX, 'z_min': Z_MIN, 'z_max': Z_MAX})
  }