import serial

# Example console session:
# import serial
# s = serial.Serial('COM4', 19200)
# s.write(b'Q?')
# 2
# s.read_all()
# b''
# s.read_all()
# b''
# s.write(b"\n")
# 1
# s.read_all()
# b'Command>\n\rCommand error\n\r'
# s.write(b"Q?\n")
# 3
# s.read_all()
# b'q,1200,0000\nCommand>\n\r'
# s.read_all()
# b''

# TODO: COM1 is the port used on the lab PC, so match this later
with serial.Serial('COM4', timeout=2) as s:
    s.read_all()
