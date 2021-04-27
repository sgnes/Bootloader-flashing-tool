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

setup_logging()

src = Srecords("MASTER_A003.hex")
#print(src.get_data_by_addr(0x4c00, 0x7000))


bus = PcanBus()                                          # Link Layer (CAN protocol)
tp_addr = isotp.Address(isotp.AddressingMode.Normal_11bits, txid=0x71d, rxid=0x71e) # Network layer addressing scheme
stack = isotp.CanStack(bus=bus, address=tp_addr, params=isotp_params)               # Network/Transport layer (IsoTP protocol)
conn = PythonIsoTpConnection(stack)                                                 # interface between Application and Transport layer
seq = 1
transfer_cnt = 0
max_data_per_seq = 0x100
with Client(conn, request_timeout=5, config=client_config) as client:                                     # Application layer (UDS protocol)
   response = client.change_session(3)
   response = client.change_session(2)
   response = client.unlock_security_access(0x11)
   response = client.start_routine(0xff00, bytes([1, 0]))
   memloc1 = MemoryLocation(address=0x4c00, memorysize=0x7000, address_format=24, memorysize_format=24)
   response = client.request_download(memloc1)
   current_addr = 0x4c00
   while transfer_cnt < 0x7000:
      cnt = min(max_data_per_seq, 0x7000-transfer_cnt)
      data = src.get_data_by_addr(current_addr, cnt)
      response = client.transfer_data(seq,  bytes.fromhex(data))
      seq += 1
      current_addr += cnt
      transfer_cnt +=  cnt

   client.request_transfer_exit()
   response = client.start_routine(0x0202, bytes([3, 0, 0x4c, 0]))
   print(binascii.hexlify(response.data))
   response = client.start_routine(0xff01)
   print(binascii.hexlify(response.data))
   response = client.ecu_reset(1)
   print(binascii.hexlify(response.data))