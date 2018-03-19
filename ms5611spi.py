import spidev
import time
import array
from timeit import default_timer as timer
import threading

class MS5611SPI(threading.Thread):

    values = array.array('d')
    times = array.array('d')
    writeIndex = 0
    readIndex = 0

    def __init__(self, exit):
        super(MS5611SPI, self).__init__()
        self.exit = exit
        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)
        self.spi.max_speed_hz = 976000
        for x in range(0, 500):
            self.values.append(0.0)
            self.times.append(0.0)
        self.dataLock = threading.Lock()

    def run(self):
        self.reset()
        time.sleep(1/10.0)
        self.readprom()
        self.sensorRead()

    def readprom(self):
       	self.prom = array.array('i')
        for adr in range(0,7):
            r = self.spi.xfer2([0xa0 + (adr << 1), 0, 0])
            self.prom.append((r[1] << 8) + r[2])

    def convertpressure4096(self):
        self.spi.xfer2([0x48])

    def converttemperature4096(self):
        self.spi.xfer2([0x58])

    def readadc(self):
        r = self.spi.xfer2([0, 0, 0, 0])
        return (r[1] << 16) + (r[2] << 8) + r[3]

    def reset(self):
        self.spi.xfer2([0x1e])

    def sensorRead(self):
        C = self.prom
        while not self.exit.is_set():
            self.converttemperature4096()
            readTime = time.time()
            time.sleep(1/100.0)
            D2 = self.readadc()
            self.convertpressure4096()
            time.sleep(1/100.0)
            D1 = self.readadc()
            dT = D2 - C[5] * 256
            TEMP = 2000 + dT * C[6] / 8388608.0
            OFF = C[2] * 65536 + (C[4] * dT) / 128.0
            SENS = C[1] * 32768 + (C[3] * dT) / 256.0
            P = (D1 * SENS / 2097152.0 - OFF) / 32768.0
            self.dataLock.acquire()
            self.values[self.writeIndex] = round(P/100.0, 2)
            self.times[self.writeIndex] = readTime
            self.writeIndex += 1
            if self.writeIndex >= 500:
                self.writeIndex = 0
            self.dataLock.release()

    def readValue(self):
        self.dataLock.acquire()
        if self.readIndex != self.writeIndex:
            values = array.array('d', [self.times[self.readIndex], self.values[self.readIndex]])
            self.readIndex += 1
            if self.readIndex >= 500:
                self.readIndex = 0
        else:
            values = array.array('d')
        self.dataLock.release()
        return values

    def readVario(self):
        self.dataLock.acquire()
        # current average
        index = self.writeIndex
        currentTime = 0.0
        currentAverage = 0.0
        valueCount = 0
        while True:
            index -= 1
            if index < 0:
                index = 499
            if currentTime - self.times[index] > 1.0 or self.times[index] == 0.0:
                break;
            if currentTime == 0.0:
                currentTime = self.times[index]
            currentAverage += self.values[index]
            valueCount += 1
        if valueCount > 0:
            currentAverage = currentAverage / valueCount
        else:
            currentAverage = 0
        lastAverage = 0.0
        valueCount = 0
        while True:
            if currentTime - self.times[index] > 2.0 or self.times[index] == 0.0:
                break; 
            lastAverage += self.values[index]
            valueCount += 1
            index -= 1
            if index < 0:
                index = 499

        if valueCount > 0:
            lastAverage = lastAverage / valueCount
        else:
            lastAverage = 0
        self.dataLock.release()
        return array.array('d', [(currentAverage - lastAverage) * -8, self.values[self.writeIndex-1]])
