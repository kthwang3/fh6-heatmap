import struct
import socket
import time
import uuid
import requests
from collections import namedtuple

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

def listen(port=5301):
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  sock.bind(('', port))
  print(f'Listening on UDP port {port}...')
  last_time = 0
  last_pos = (0.0, 0.0)
  lastState = 0
  my_uuid = uuid.uuid4()
  while True:
    data, _ = sock.recvfrom(1024)
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

    last_x, last_z = last_pos
    if time.time() - last_time >= 5 or (((last_x - pkt.PositionX)**2 + (last_z - pkt.PositionZ)**2)**0.5) >= 50:
      last_time = time.time()
      last_pos = (pkt.PositionX, pkt.PositionZ)
      timestamp = str(int(time.time() * 1000))
      url = 'https://s60170byjh.execute-api.us-east-1.amazonaws.com/prod/position'

      #POST to API Gateway URL
      requests.post(url, json={'timestamp': timestamp, 'session_id': str(my_uuid), 'x_pos': pkt.PositionX, 'z_pos': pkt.PositionZ})
      print(f'X={pkt.PositionX:10.1f} Z={pkt.PositionZ:10.1f} speed={pkt.Speed * 3.6:.1f} km/h')

if __name__ == '__main__':
  listen()


