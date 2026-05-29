from locust import HttpUser, task, between
import time
import uuid

class HeatmapUser(HttpUser):
  # mock ~5 second sampling interval from parser.py
  wait_time = between(4, 6)
  
  def on_start(self):
    self.session_id = str(uuid.uuid4())
    
  @task
  def post_position(self):
    # POST a fake position to /prod/position
    self.client.post('/prod/position', json={
      'timestamp': str(int(time.time() * 1000)),
      'session_id': self.session_id,
      'x_pos': 994.1,
      'z_pos': -5535.9
    })
  