import struct
import socket
import time
import uuid
import requests
import asyncio
import json
import websockets
import sys
import os
import threading
import http.server
import webbrowser
from collections import namedtuple

#help find livemap/ regardless of python script or bundled .exe
def get_base_path():
  #Check sys.frozen
  if getattr(sys,'frozen', False):
    return sys._MEIPASS
  else:
    return os.path.dirname(os.path.abspath(__file__))

#starts http server in a background thread by passsing livemap directly to the handler
def start_livemap_server(base_path):
  livemap_path = os.path.join(base_path, 'livemap')
  
  #Reuse SimpleHTTPRequestHandler but serve from livemap_path directory
  class LivemapHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, request, client_address, server):
      super().__init__(request, client_address, server, directory=livemap_path)
    
    def log_message(self, format, *args):
      pass
  
  def run():
    server = http.server.HTTPServer(('', 5500), LivemapHandler)
    server.serve_forever()
  thread = threading.Thread(target=run)
  #Stop http after user closes .exe
  thread.daemon = True
  thread.start()

#Livemap feature: broadcast position on every packet
clients = set()

async def ws_handler(websocket):
  clients.add(websocket)
  try:
    await websocket.wait_closed()
  finally:
    clients.remove(websocket)

async def broadcast(x, z, speed):
  if not clients:
    return
  message = json.dumps({"x": x, "z": z, "speed": round(speed * 3.6, 1)})
  #make a copy to prevent runtime error if ws_handler closes client
  for client in clients.copy():
    #try/except so closed client doesn't throw
    #send json string over the WebSocket connection to that browser tab
    try:
      await client.send(message)
    except Exception:
      pass


FMT = '<iIfff' + 'f' * 24 + 'i' * 8 + 'f' * 16 + 'i' * 5  + 'I' + 'f' * 19 + 'H' + 'B' * 6 + 'bbbx'
FIELDS = (
  'IsRaceOn', 'TimestampMS',
  'EngineMaxRpm', 'EngineIdleRpm', 'CurrentEngineRpm',
  'AccelerationX', 'AccelerationY', 'AccelerationZ',
  'VelocityX', 'VelocityY', 'VelocityZ',
  'AngularVelocityX', 'AngularVelocityY', 'AngularVelocityZ',
  'Yaw', 'Pitch', 'Roll',
  'NormalizedSuspensionTravelFrontLeft', 'NormalizedSuspensionTravelFrontRight',
  'NormalizedSuspensionTravelRearLeft', 'NormalizedSuspensionTravelRearRight',
  'TireSlipRatioFrontLeft', 'TireSlipRatioFrontRight',
  'TireSlipRatioRearLeft', 'TireSlipRatioRearRight',
  'WheelRotationSpeedFrontLeft', 'WheelRotationSpeedFrontRight',
  'WheelRotationSpeedRearLeft', 'WheelRotationSpeedRearRight',
  'WheelOnRumbleStripFrontLeft', 'WheelOnRumbleStripFrontRight',
  'WheelOnRumbleStripRearLeft', 'WheelOnRumbleStripRearRight',
  'WheelInPuddleFrontLeft', 'WheelInPuddleFrontRight',
  'WheelInPuddleRearLeft', 'WheelInPuddleRearRight',
  'SurfaceRumbleFrontLeft', 'SurfaceRumbleFrontRight',
  'SurfaceRumbleRearLeft', 'SurfaceRumbleRearRight',
  'TireSlipAngleFrontLeft', 'TireSlipAngleFrontRight',
  'TireSlipAngleRearLeft', 'TireSlipAngleRearRight',
  'TireCombinedSlipFrontLeft', 'TireCombinedSlipFrontRight',
  'TireCombinedSlipRearLeft', 'TireCombinedSlipRearRight',
  'SuspensionTravelMetersFrontLeft', 'SuspensionTravelMetersFrontRight',
  'SuspensionTravelMetersRearLeft', 'SuspensionTravelMetersRearRight',
  'CarOrdinal', 'CarClass', 'CarPerformanceIndex', 'DrivetrainType', 'NumCylinders',
  'CarGroup',
  'SmashableVelDiff', 'SmashableMass',
  'PositionX', 'PositionY', 'PositionZ',
  'Speed', 'Power', 'Torque',
  'TireTempFrontLeft', 'TireTempFrontRight',
  'TireTempRearLeft', 'TireTempRearRight',
  'Boost', 'Fuel', 'DistanceTraveled',
  'BestLap', 'LastLap', 'CurrentLap', 'CurrentRaceTime',
  'LapNumber', 'RacePosition',
  'Accel', 'Brake', 'Clutch', 'HandBrake', 'Gear',
  'Steer', 'NormalizedDrivingLine', 'NormalizedAIBrakeDifference',
)
Packet = namedtuple('Packet', FIELDS)

def parse(data: bytes) -> Packet:
  values = struct.unpack(FMT, data)
  return Packet(*values)

def udp_loop(event_loop, port=5301):
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  sock.bind(('', port))
  last_time = 0
  last_pos = (0.0, 0.0)
  lastState = 0
  my_uuid = uuid.uuid4()
  while True:
    data, sender_address = sock.recvfrom(1024)
    if len(data) != 324:
      continue
    pkt = parse(data)
    currentState = pkt.IsRaceOn

    #Check state
    if lastState != currentState:
      my_uuid = uuid.uuid4()
      lastState = currentState

    #State guard
    if not pkt.IsRaceOn:
      continue

    asyncio.run_coroutine_threadsafe(broadcast(pkt.PositionX, pkt.PositionZ, pkt.Speed), event_loop)
    last_x, last_z = last_pos
    if time.time() - last_time >= 10 or (((last_x - pkt.PositionX)**2 + (last_z - pkt.PositionZ)**2)**0.5) >= 50:
      last_time = time.time()
      last_pos = (pkt.PositionX, pkt.PositionZ)
      timestamp = str(int(time.time() * 1000))
      url = 'https://s60170byjh.execute-api.us-east-1.amazonaws.com/prod/position'

      #POST to API Gateway URL
      requests.post(url, json={'timestamp': timestamp, 'session_id': str(my_uuid), 'x_pos': pkt.PositionX, 'z_pos': pkt.PositionZ, 'car_ordinal': pkt.CarOrdinal, 'car_class': pkt.CarClass, 'car_performance_index': pkt.CarPerformanceIndex})

# 1. Start websocket server -> browsers
# 2. Launch udp_loop in a background threat -> FH6 packets
# 3. call start and open http server
async def main():
  base_path = get_base_path()
  start_livemap_server(base_path)
  time.sleep(0.5)
  #Return False if cannot find a browser, or opens automatically for windows/desktop linux
  url = 'http://localhost:5500/livemap.html'
  if not webbrowser.open(url):
    print(f'Open {url} in your browser')
  event_loop = asyncio.get_running_loop()
  websocket_server = await websockets.serve(ws_handler, 'localhost', 8765)
  # keep main alive and run udp_loop in background of event_loop
  await event_loop.run_in_executor(None, udp_loop, event_loop)
  websocket_server.close()

if __name__ == '__main__':
  # create an event loop that runs until program is closed
  asyncio.run(main())


