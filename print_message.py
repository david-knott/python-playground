# use slice and int.from_bytes to extract data from message
# array slice https://stackoverflow.com/questions/509211/understanding-slice-notation

def print_message(test):
    """prints out canbus message values"""
    hcvdec = int.from_bytes(test[0:2], byteorder='big')
    lcvdec = int.from_bytes(test[2:4], byteorder='big')
    pvdec = int.from_bytes(test[4:6], byteorder='big')
    sodec = int.from_bytes(test[6:7], byteorder='big')
    print('hv =', hcvdec * 0.0001, 'lv =', lcvdec * 0.0001, 'pv =', pvdec* 0.01, 'so =', sodec* 0.5)

# data = b'\xff\x00\xff\x00\xff\x00'
data = bytearray([0x7f,0x7f,0x7c,0xd7,0x13,0x0a,0x55,0xc3])
print_message(data)
