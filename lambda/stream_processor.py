import boto3
from decimal import Decimal

FACTOR_X = 3.5131
OFFSET_X = 3244
FACTOR_Y = -3.512
OFFSET_Y = 3061
IMAGE_SIZE = 6144
#number of columns and rows, not meters per grid square
GRID_W = 200
GRID_H = 200

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('fh6-heatmap-grid-table')

def handler(event, context):
  for record in event['Records']:
    if record["eventName"] != 'INSERT':
      continue
    x_pos = record['dynamodb']['NewImage']['x_pos']['N']
    z_pos = record['dynamodb']['NewImage']['z_pos']['N']
    car_ordinal = record['dynamodb']['NewImage']['car_ordinal']['N']
    car_class = int(record['dynamodb']['NewImage']['car_class']['N'])
    car_performance_index = int(record['dynamodb']['NewImage']['car_performance_index']['N'])
    col = int((float(x_pos) / FACTOR_X + OFFSET_X) / IMAGE_SIZE * GRID_W)
    row = int((float(z_pos) / FACTOR_Y + OFFSET_Y) / IMAGE_SIZE * GRID_H)
    if not (0 <= col < GRID_W and 0 <= row < GRID_H):
      continue
    
    table.update_item(
      Key={'col_row': f'{col}_{row}'},
      UpdateExpression='SET cars = if_not_exists(cars, :empty_map) ADD #count :one',
      ExpressionAttributeNames={'#count': 'count'},
      ExpressionAttributeValues={':one': Decimal('1'), ':empty_map': {}}
    )
    table.update_item(
      Key={'col_row': f'{col}_{row}'},
      UpdateExpression='SET cars.#ordinal = if_not_exists(cars.#ordinal, :empty_car)',
      ExpressionAttributeNames={'#ordinal': car_ordinal},
      ExpressionAttributeValues={':empty_car': {'count': Decimal('0'), 'car_class': car_class, 'car_performance_index': car_performance_index}}
    )
    table.update_item(
      Key={'col_row': f'{col}_{row}'},
      UpdateExpression='SET cars.#ordinal.#count = cars.#ordinal.#count + :one',
      ExpressionAttributeNames={'#count': 'count', '#ordinal': car_ordinal},
      ExpressionAttributeValues={':one': Decimal('1')}
    )
