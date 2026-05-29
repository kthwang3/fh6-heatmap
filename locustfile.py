from locust import HttpUser, task, between
import time
import uuid

TEST_POSITIONS = [
  {'x_pos': -604.0, 'z_pos': -38.6, 'car_ordinal': 455,  'car_class': 2, 'car_performance_index': 550},
  {'x_pos': -604.0, 'z_pos': -38.6, 'car_ordinal': 461,  'car_class': 4, 'car_performance_index': 800},
  {'x_pos': -604.0, 'z_pos': -38.6, 'car_ordinal': 4114, 'car_class': 4, 'car_performance_index': 900},
  {'x_pos': -6000.0, 'z_pos': 5355.0, 'car_ordinal': 1314, 'car_class': 6, 'car_performance_index': 999},
  {'x_pos': 2658.0,  'z_pos': 3198.0, 'car_ordinal': 2034, 'car_class': 6, 'car_performance_index': 998},
]

HOT_POSITION  = TEST_POSITIONS[0]
COLD_POSITIONS = TEST_POSITIONS[1:]

class HeatmapUser(HttpUser):
  wait_time = between(4, 6)

  def on_start(self):
    self.session_id = str(uuid.uuid4())
    self.cold_index = 0

  def post(self, position):
    self.client.post('/prod/position', json={
      'timestamp': str(int(time.time() * 1000)),
      'session_id': self.session_id,
      'x_pos': position['x_pos'],
      'z_pos': position['z_pos'],
      'car_ordinal': position['car_ordinal'],
      'car_class': position['car_class'],
      'car_performance_index': position['car_performance_index'],
    })

  @task(5)
  def post_hot_position(self):
    self.post(HOT_POSITION)

  @task(1)
  def post_cold_position(self):
    cold_position = COLD_POSITIONS[self.cold_index % len(COLD_POSITIONS)]
    self.cold_index += 1
    self.post(cold_position)

# ── Old single-task version (equal distribution, causes all cells to blow out to white) ──
# class HeatmapUser(HttpUser):
#   wait_time = between(4, 6)
#
#   def on_start(self):
#     self.session_id = str(uuid.uuid4())
#     self.position_index = 0
#
#   @task
#   def post_position(self):
#     position = TEST_POSITIONS[self.position_index % len(TEST_POSITIONS)]
#     self.position_index += 1
#     self.client.post('/prod/position', json={
#       'timestamp': str(int(time.time() * 1000)),
#       'session_id': self.session_id,
#       'x_pos': position['x_pos'],
#       'z_pos': position['z_pos'],
#       'car_ordinal': position['car_ordinal'],
#       'car_class': position['car_class'],
#       'car_performance_index': position['car_performance_index'],
#     })
