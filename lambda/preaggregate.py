import json
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime, timezone, timedelta

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
counters_table = dynamodb.Table('fh6-heatmap-grid-table')

#use for all-time heatmap
def build_all_time(counters):
  grid = [[0] * GRID_W for _ in range(GRID_H)]
  car_grid = [[{} for _ in range(GRID_W)] for _ in range(GRID_H)]
  car_counts = {}
  for item in counters:
    col_str, row_str = item['col_row'].split('_')
    col = int(col_str)
    row = int(row_str)
    grid[row][col] = int(item['count'])
    if 'cars' in item:
      for ordinal_str, car_data in item['cars'].items():
        car_ordinal = int(ordinal_str)
        car_count = int(car_data['count'])
        car_grid[row][col][car_ordinal] = {
          'count': car_count,
          'car_class': int(car_data['car_class']),
          'car_performance_index': int(car_data['car_performance_index'])
        }
        car_counts[car_ordinal] = car_counts.get(car_ordinal, 0) + car_count
  sorted_ordinals = sorted(car_counts, key=car_counts.get, reverse=True)[:10]
  leaderboard = [{'ordinal': ordinal, 'count': car_counts[ordinal]} for ordinal in sorted_ordinals]
  return grid, car_grid, leaderboard

#use for day/week filters
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

def compute_leaderboard(items):
  car_counts = {}
  for item in items:
    if 'car_ordinal' not in item:
      continue
    car_ordinal = int(item['car_ordinal'])
    car_counts[car_ordinal] = car_counts.get(car_ordinal, 0) + 1
    
  sorted_car_counts = sorted(car_counts, key=car_counts.get, reverse=True)
  sorted_car_ordinals = sorted_car_counts[:10]
  leaderboard = []
  for ordinal in sorted_car_ordinals:
    leaderboard.append({'ordinal': ordinal, 'count': car_counts[ordinal]})
  return leaderboard

def query_gsi_days(num_days):
  today = datetime.now(tz=timezone.utc)
  items = []
  # subtract days from today up to num_days apart
  for i in range(num_days):
    date_str = (today - timedelta(days=i)).strftime('%Y-%m-%d')
    response = table.query(
      IndexName='date-index',
      KeyConditionExpression=Key('date').eq(date_str)
    )
    items += response['Items']
    while 'LastEvaluatedKey' in response:
      response = table.query(
        IndexName='date-index',
        KeyConditionExpression=Key('date').eq(date_str),
        ExclusiveStartKey=response['LastEvaluatedKey']
      )
      items += response['Items']
  return items

def handler(event, context):
  day_items = query_gsi_days(1)
  week_items = query_gsi_days(7)

  counters = []
  response = counters_table.scan()
  counters += response['Items']
  while 'LastEvaluatedKey' in response:
    response = counters_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
    counters += response['Items']

  all_time_grid, all_time_car_grid, all_time_leaderboard = build_all_time(counters)
  day_grid, day_car_grid = compute_grid(day_items)
  week_grid, week_car_grid = compute_grid(week_items)
  day_leaderboard = compute_leaderboard(day_items)
  week_leaderboard = compute_leaderboard(week_items)

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
    Key='day-grids.json',
    Body=json.dumps({'grid': day_grid, 'car_grid': day_car_grid}),
    ContentType='application/json'
  )
  s3_client.put_object(
    Bucket='fh6-heatmap-s3-kthwang3',
    Key='car-leaderboard-all-time.json',
    Body=json.dumps({'all-time-leaderboard': all_time_leaderboard}),
    ContentType='application/json'
  )
  s3_client.put_object(
    Bucket='fh6-heatmap-s3-kthwang3',
    Key='car-leaderboard-week.json',
    Body=json.dumps({'week-leaderboard': week_leaderboard}),
    ContentType='application/json'
  )
  s3_client.put_object(
    Bucket='fh6-heatmap-s3-kthwang3',
    Key='car-leaderboard-day.json',
    Body=json.dumps({'day-leaderboard': day_leaderboard}),
    ContentType='application/json'
  )
