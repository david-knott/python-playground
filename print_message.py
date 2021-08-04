#!/usr/bin/env python

# use slice and int.from_bytes to extract data from message
# array slice https://stackoverflow.com/questions/509211/understanding-slice-notation
# https://www.rapidtables.com/convert/number/hex-to-decimal.html
# https://www.programiz.com/python-programming/online-compiler/
# https://docs.python.org/3/library/stdtypes.html#bytes
# https://github.com/hardbyte/python-can/blob/faed6e9cef02b427d386515c2d12cebb72a5717d/examples/receive_all.py
# data = b'\xff\x00\xff\x00\xff\x00'
# data = bytearray([0x7f,0x7f,0x7c,0xd7,0x13,0x0a,0x55,0xc3])
# print_message(data)



from __future__ import print_function

import can
# from can.bus import BusState

def print_message(test):
    """prints out canbus message values"""
    hcvdec = int.from_bytes(test[0:2], byteorder='big')
    lcvdec = int.from_bytes(test[2:4], byteorder='big')
    pvdec = int.from_bytes(test[4:6], byteorder='big')
    sodec = int.from_bytes(test[6:7], byteorder='big')
    print('hv =', hcvdec * 0.0001, 'lv =', lcvdec * 0.0001, 'pv =', pvdec* 0.01, 'so =', sodec* 0.5)

    
def receive_all():
    bus = can.interface.Bus(channel='can0', bustype='socketcan_native')
    # bus.state = BusState.ACTIVE  # or BusState.PASSIVE
    try:
        while True:
            msg = bus.recv(1)
            if msg is not None:
                print_message(msg.data)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    receive_all()

    


