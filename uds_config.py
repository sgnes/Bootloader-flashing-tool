from can.interfaces.vector import VectorBus
from udsoncan.connections import PythonIsoTpConnection
from udsoncan.client import Client
import isotp
import udsoncan
import struct

# Refer to isotp documentation for full details about parameters
isotp_params = {
   'stmin' : 32,                          # Will request the sender to wait 32ms between consecutive frame. 0-127ms or 100-900ns with values from 0xF1-0xF9
   'blocksize' : 8,                       # Request the sender to send 8 consecutives frames before sending a new flow control message
   'wftmax' : 0,                          # Number of wait frame allowed before triggering an error
   'll_data_length' : 8,                  # Link layer (CAN layer) works with 8 byte payload (CAN 2.0)
   'tx_padding' : 0,                      # Will pad all transmitted CAN messages with byte 0x00. None means no padding
   'rx_flowcontrol_timeout' : 1000,       # Triggers a timeout if a flow control is awaited for more than 1000 milliseconds
   'rx_consecutive_frame_timeout' : 1000, # Triggers a timeout if a consecutive frame is awaited for more than 1000 milliseconds
   'squash_stmin_requirement' : False     # When sending, respect the stmin requirement of the receiver. If set to True, go as fast as possible.
}

class MyCustomCodecThatShiftBy4(udsoncan.DidCodec):
   def encode(self, val):
      val = (val << 4) & 0xFFFFFFFF # Do some stuff
      return struct.pack('<L', val) # Little endian, 32 bit value

   def decode(self, payload):
      val = struct.unpack('<L', payload)[0]  # decode the 32 bits value
      return val >> 4                        # Do some stuff (reversed)

   def __len__(self):
      return 4    # encoded paylaod is 4 byte long.

class MyCustomCodecHex(udsoncan.DidCodec):
   def encode(self, val):
      return bytes.fromhex(val)

   def decode(self, payload):
      return payload.hex()              # Do some stuff (reversed)

   def __len__(self):
      return 1    # encoded paylaod is 4 byte long.


def security_algo(level, seed):
    """
    :param level:  security level
            type: int
    :param seed: seed
            type: str
    :return:  the key to unlock the ECU
            type:bytes
    """
    numShift_u8 = 0
    return bytes([0xaa,0xaa,0xaa,0xaa])


client_config  = {
	'exception_on_negative_response'	: False,
	'exception_on_invalid_response'		: False,
	'exception_on_unexpected_response'	: False,
	'security_algo'				: security_algo,
	'security_algo_params'		: None,
	'tolerate_zero_padding' 	: True,
	'ignore_all_zero_dtc' 		: True,
	'dtc_snapshot_did_size' 	: 2,		# Not specified in standard. 2 bytes matches other services format.
	'server_address_format'		: None,		# 8,16,24,32,40
	'server_memorysize_format'	: None,		# 8,16,24,32,40
	'data_identifiers' 			: {0x0100:MyCustomCodecThatShiftBy4,
                                     0x0130:MyCustomCodecHex,
                                     0xD500:MyCustomCodecHex,
                                     0xFE01:MyCustomCodecHex,
                                     0xDF00:MyCustomCodecHex,
                                     0xd472:MyCustomCodecHex},
	'input_output' 				: {},
    'p2_timeout' :0.5,
    'p2_server_max':5,
    'request_timeout':5,
    'p2_star_timeout':5
}

class project_config():
    uds_req_phy_id = 0x71d
    uds_req_fun_id = 0x7df
    uds_res_id = 0x71e
    app_start_addr = 0x4c00
    app_size = 0x7000