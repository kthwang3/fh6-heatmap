#Used for migrating historical data to DynamoDB stream
from datetime import datetime, timezone
import boto3
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor, as_completed

FACTOR_X = 3.5131
OFFSET_X = 3244
FACTOR_Y = -3.512
OFFSET_Y = 3061
IMAGE_SIZE = 6144
GRID_W = 200
GRID_H = 200

dynamodb = boto3.resource('dynamodb')
position_data = dynamodb.Table('fh6-heatmap-table')
grid_data = dynamodb.Table('fh6-heatmap-grid-table')

positions = []
response = position_data.scan()
positions += response['Items']
while 'LastEvaluatedKey' in response:
  response = position_data.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
  positions += response['Items']

print(f'Loaded {len(positions)} positions')

def process(position):
  if 'car_ordinal' not in position:
    return
  x = float(position['x_pos'])
  z = float(position['z_pos'])
  car_ordinal = str(position['car_ordinal'])
  car_class = int(position['car_class'])
  car_performance_index = int(position['car_performance_index'])
  date_str = datetime.fromtimestamp(int(position['timestamp']) / 1000, tz=timezone.utc).strftime('%Y-%m-%d')

  position_data.update_item(
    Key={'sessionId': position['sessionId'], 'timestamp': position['timestamp']},
    UpdateExpression='SET #d = :date_val',
    ExpressionAttributeNames={'#d': 'date'},
    ExpressionAttributeValues={':date_val': date_str}
  )

  col = int((x / FACTOR_X + OFFSET_X) / IMAGE_SIZE * GRID_W)
  row = int((z / FACTOR_Y + OFFSET_Y) / IMAGE_SIZE * GRID_H)
  if not (0 <= col < GRID_W and 0 <= row < GRID_H):
    return

  grid_data.update_item(
    Key={'col_row': f'{col}_{row}'},
    UpdateExpression='SET cars = if_not_exists(cars, :empty_map) ADD #count :one',
    ExpressionAttributeNames={'#count': 'count'},
    ExpressionAttributeValues={':one': Decimal('1'), ':empty_map': {}}
  )
  grid_data.update_item(
    Key={'col_row': f'{col}_{row}'},
    UpdateExpression='SET cars.#ordinal = if_not_exists(cars.#ordinal, :empty_car)',
    ExpressionAttributeNames={'#ordinal': car_ordinal},
    ExpressionAttributeValues={':empty_car': {'count': Decimal('0'), 'car_class': car_class, 'car_performance_index': car_performance_index}}
  )
  grid_data.update_item(
    Key={'col_row': f'{col}_{row}'},
    UpdateExpression='SET cars.#ordinal.#count = cars.#ordinal.#count + :one',
    ExpressionAttributeNames={'#count': 'count', '#ordinal': car_ordinal},
    ExpressionAttributeValues={':one': Decimal('1')}
  )

completed = 0
with ThreadPoolExecutor(max_workers=20) as executor:
  futures = [executor.submit(process, p) for p in positions]
  for future in as_completed(futures):
    future.result()
    completed += 1
    if completed % 1000 == 0:
      print(f'{completed} / {len(positions)}')

print('Done')
