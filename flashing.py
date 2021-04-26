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

def setup_logging(default_path='logging.json', default_level=logging.INFO, env_key='LOG_CFG'):
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
with Client(conn, request_timeout=5, config=client_config) as client:                                     # Application layer (UDS protocol)
   response = client.change_session(3)
   print(response)
   print(binascii.hexlify(response.data))
   # Application layer (UDS protocol)
   response = client.change_session(2)
   print(response)
   print(binascii.hexlify(response.data))
   response = client.unlock_security_access(0x11)
   print(response)
   response = client.start_routine(1, bytes([0]))
   print(response)
