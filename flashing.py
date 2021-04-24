from pysrc import Srecords
from udsoncan import client
from can.interfaces.pcan import PcanBus
from udsoncan.connections import PythonIsoTpConnection
from udsoncan.client import Client
import isotp
import udsoncan
import struct
from uds_config import *


src = Srecords("MASTER_A003.hex")
print(src.get_data_by_addr(0x4c00, 0x7000))


bus = PcanBus()                                          # Link Layer (CAN protocol)
tp_addr = isotp.Address(isotp.AddressingMode.Normal_11bits, txid=0x71d, rxid=0x71e) # Network layer addressing scheme
stack = isotp.CanStack(bus=bus, address=tp_addr, params=isotp_params)               # Network/Transport layer (IsoTP protocol)
conn = PythonIsoTpConnection(stack)                                                 # interface between Application and Transport layer
with Client(conn, request_timeout=1, config=client_config) as client:                                     # Application layer (UDS protocol)
   client.change_session(3)
   response = client.request_seed(1)
   #client.send_key(2, b'0001')
   response = client.read_data_by_identifier(0xd472)
   print(response)