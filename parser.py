import struct
import socket
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
  while True:
    data, _ = sock.recvfrom(1024)
    if len(data) != 324:
      continue
    pkt = parse(data)
    if not pkt.IsRaceOn:
      continue
    print(f'X={pkt.PositionX:10.1f} Z={pkt.PositionZ:10.1f} speed={pkt.Speed * 3.6:.1f} km/h')
if __name__ == '__main__':
  listen()


