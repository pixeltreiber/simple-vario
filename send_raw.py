import time
import array
import os
from timeit import default_timer as timer
import ms5611spi
import threading
import string
import socket

UDP_IP = '192.168.1.248'
UDP_PORT = 4353

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

stop_event = threading.Event()
reader = ms5611spi.MS5611SPI(stop_event)
try:
    reader.start()
    while True:
        values = reader.readVario()
        s = str.format("$POV,E,{:.2f},P,{:.2f}", values[0], values[1])
        checksum = 0
        for i in s[1:]:
            checksum = checksum ^ ord(i)
        message = str.format("{:s}*{:02x}\r\n", s, checksum)
        sock.sendto(message, (UDP_IP, UDP_PORT))
        time.sleep(1/50.0)
except KeyboardInterrupt as e:
    stop_event.set()
    reader.join()

print "in main: exiting.."
