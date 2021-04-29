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

setup_logging()

src = Srecords("MASTER_A003.hex")
#print(src.get_data_by_addr(0x4c00, 0x7000))


bus = PcanBus()                                          # Link Layer (CAN protocol)
tp_addr = isotp.Address(isotp.AddressingMode.Normal_11bits, txid=project_config.uds_req_phy_id, rxid=project_config.uds_res_id) # Network layer addressing scheme
stack = isotp.CanStack(bus=bus, address=tp_addr, params=isotp_params)               # Network/Transport layer (IsoTP protocol)
conn = PythonIsoTpConnection(stack)                                                 # interface between Application and Transport layer
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
   memloc1 = MemoryLocation(address=project_config.app_start_addr, memorysize=project_config.app_size, address_format=24, memorysize_format=24)
   response = client.request_download(memloc1)
   print(binascii.hexlify(response.data))
   current_addr = project_config.app_start_addr

   printProgressBar(0, project_config.app_size, prefix='Progress:', suffix='Complete', length=50)

   while transfer_cnt < project_config.app_size:
      cnt = min(max_data_per_seq, project_config.app_size-transfer_cnt)
      data = src.get_data_by_addr(current_addr, cnt)
      response = client.transfer_data(seq,  bytes.fromhex(data))
      seq += 1
      current_addr += cnt
      transfer_cnt +=  cnt
      printProgressBar(transfer_cnt, project_config.app_size, prefix='Progress:', suffix='Complete', length=50)

   client.request_transfer_exit()
   response = client.start_routine(0x0202, bytes([3, 0, 0x4c, 0]))
   print(binascii.hexlify(response.data))
   response = client.start_routine(0xff01)
   print(binascii.hexlify(response.data))
   response = client.ecu_reset(1)
   print(binascii.hexlify(response.data))