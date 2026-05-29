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

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('fh6-heatmap-table')
s3_client = boto3.client('s3')

def compute_grid(filtered_items):
  grid = [[0] * GRID_W for _ in range(GRID_H)]
  car_grid = [[{} for _ in range(GRID_W)] for _ in range(GRID_H)]

  for item in filtered_items:
    #change back from Decimal
    x = float(item['x_pos'])
    z = float(item['z_pos'])
    if 'car_ordinal' not in item:
      continue
    car_ordinal = int(item['car_ordinal'])
    car_class = int(item['car_class'])
    car_performance_index = int(item['car_performance_index'])
    col = int((x / FACTOR_X + OFFSET_X) / IMAGE_SIZE * GRID_W)
    row = int((z / FACTOR_Y + OFFSET_Y) / IMAGE_SIZE * GRID_H)
    if 0 <= col < GRID_W and 0 <= row < GRID_H:
      grid[row][col] += 1
      if car_ordinal not in car_grid[row][col]:
        car_grid[row][col][car_ordinal] = {'count': 1, 'car_class': car_class, 'car_performance_index': car_performance_index}
      else:
        car_grid[row][col][car_ordinal]['count'] += 1

  return grid, car_grid


def filter_items(items, cutoff_ms):
  filtered_items = []
  for item in items:
    if int(item['timestamp']) >= cutoff_ms:
      filtered_items.append(item)
  return filtered_items

def handler(event, context):
  
  items = []
  response = table.scan()
  items += response['Items']
  #bookmark last key and continue until all data is read
  while 'LastEvaluatedKey' in response:
    response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
    items += response['Items']
  current_time_ms = time.time() * 1000

  week_cutoff = current_time_ms - 7 * 24 * 60 * 60 * 1000
  month_cutoff = current_time_ms - 31 * 24 * 60 * 60 * 1000

  filtered_week = filter_items(items, week_cutoff)
  filtered_month = filter_items(items, month_cutoff)

  all_time_grid, all_time_car_grid = compute_grid(items)
  week_grid, week_car_grid = compute_grid(filtered_week)
  month_grid, month_car_grid = compute_grid(filtered_month)



  s3_client.put_object(
    Bucket='fh6-heatmap-s3-kthwang3',
    Key='all-time-grids.json',
    Body=json.dumps({'grid': all_time_grid, 'car_grid': all_time_car_grid}),
    ContentType='application/json'
  )
  s3_client.put_object(
    Bucket='fh6-heatmap-s3-kthwang3',
    Key='week-grids.json',
    Body=json.dumps({'grid': week_grid, 'car_grid': week_car_grid}),
    ContentType='application/json'
  )
  s3_client.put_object(
    Bucket='fh6-heatmap-s3-kthwang3',
    Key='month-grids.json',
    Body=json.dumps({'grid': month_grid, 'car_grid': month_car_grid}),
    ContentType='application/json'
  )
