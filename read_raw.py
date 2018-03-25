import time
import array
import os
from timeit import default_timer as timer
import ms5611spi
import threading
import string

stop_event = threading.Event()
reader = ms5611spi.MS5611SPI(stop_event)
try:
    reader.start()
    while True:
        timestamp, pressure = reader.readRaw()
        s = str.format("{:.3f},{:.2f}\n", timestamp, pressure)
        print s,
        time.sleep(1/50.0)
except KeyboardInterrupt as e:
    stop_event.set()
    reader.join()
