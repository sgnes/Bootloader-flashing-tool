from pysrc import Srecords
from udsoncan import client
from can.interfaces.pcan import PcanBus
from udsoncan.connections import PythonIsoTpConnection
from udsoncan.client import Client
import isotp
import udsoncan
import struct
from uds_config import *
import binascii
import logging
import os
import json
from udsoncan import Request, MemoryLocation
import argparse
import time
import sys


def setup_logging(default_path='logging.json', default_level=logging.DEBUG, env_key='LOG_CFG'):
   """Setup logging configuration
   """
   path = default_path
   value = os.getenv(env_key, None)
   if value:
      path = value
   if os.path.exists(path):
      with open(path, 'rt') as f:
         config = json.load(f)
      logging.config.dictConfig(config)
   else:
      logging.basicConfig(level=default_level)

# Print iterations progress
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total:
        print()

def reprogramming(conn, args):
   setup_logging()

   src = Srecords(args.file)
   seq = 1
   transfer_cnt = 0
   max_data_per_seq = 0x100
   with Client(conn, request_timeout=5, config=client_config) as client:                                     # Application layer (UDS protocol)
      response = client.change_session(3)
      print(binascii.hexlify(response.data))
      response = client.change_session(2)
      print(binascii.hexlify(response.data))
      response = client.unlock_security_access(0x11)
      print(binascii.hexlify(response.data))
      response = client.start_routine(0xff00, bytes([1, 0]))
      print(binascii.hexlify(response.data))
      memloc1 = MemoryLocation(address=args.app_start_addr, memorysize=args.app_size, address_format=24, memorysize_format=24)
      response = client.request_download(memloc1)
      print(binascii.hexlify(response.data))
      current_addr = args.app_start_addr

      printProgressBar(0, args.app_size, prefix='Progress:', suffix='Complete', length=50)

      while transfer_cnt < args.app_size:
         cnt = min(max_data_per_seq, args.app_size-transfer_cnt)
         data = src.get_data_by_addr(current_addr, cnt)
         response = client.transfer_data(seq,  bytes.fromhex(data))
         seq += 1
         current_addr += cnt
         transfer_cnt +=  cnt
         printProgressBar(transfer_cnt, args.app_size, prefix='Progress:', suffix='Complete', length=50)

      client.request_transfer_exit()
      response = client.start_routine(0x0202, bytes([3, 0, 0x4c, 0]))
      print(binascii.hexlify(response.data))
      if response.data[3]!=0x00:
         testresult = "Flash Failed"
      else:
         response = client.start_routine(0xff01)
         print(binascii.hexlify(response.data))
         if response.data[3] != 0x01:
            testresult = "Flash Failed"
         else:
            testresult = "Flash Success"
      response = client.ecu_reset(1)
      print(binascii.hexlify(response.data))
      print(testresult)

if __name__ == '__main__':
   parser = argparse.ArgumentParser(description='test')

   parser.add_argument('--can_interface', default='PCAN', help='The CAN interface used for programming, PCAN, Vector...')
   parser.add_argument('--can_channel', default=0, help='The CAN interface channel used for programming, 0,1.')
   parser.add_argument('--baud_rate', type=int, default=500, help='CAN baud rate.')
   parser.add_argument('--file', type=str, default="MASTER.srec", help='The file to be reprogrammed')
   parser.add_argument('--app_start_addr', type=int, default=0x4c00, help='The start address of app')
   parser.add_argument('--app_size', type=int, default=0x7000, help='The size of app')

   args = parser.parse_args()

   if args.can_interface == "Vector":
      bus = VectorBus(args.can_channel)
   elif args.can_interface == "PCAN":
      bus = PcanBus()  # Link Layer (CAN protocol)
   tp_addr = isotp.Address(isotp.AddressingMode.Normal_11bits, txid=project_config.uds_req_phy_id,
                           rxid=project_config.uds_res_id)  # Network layer addressing scheme
   stack = isotp.CanStack(bus=bus, address=tp_addr, params=isotp_params)  # Network/Transport layer (IsoTP protocol)
   stack.set_sleep_timing(0.001, 0.001)
   conn = PythonIsoTpConnection(stack)
   reprogramming(conn, args)

   start = time.time()
   max_limit=5 #5s timeout
   for msg in bus:
      if msg.arbitration_id == 0x664:
         print ("The current SW version is:")
         swversion=msg.data[7:5:-1]
         print(binascii.hexlify(swversion))
         sys.exit(0)
      if time.time() - start > max_limit:
         print("Fail, No APP msg received, Can not read out SW version")
         sys.exit(0)