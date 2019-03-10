#!/usr/bin/python
import sys
import Adafruit_DHT

PIN = 4

def ada():
    while True:
        print("Trying to read temp from pin {}".format(PIN))
        humidity, temperature = Adafruit_DHT.read_retry(11, PIN)
        print('Temp: {} C  Humidity: {} %'.format(temperature, humidity))

def gp2():
    import RPi.GPIO as GPIO
    import time

    def bin2dec(string_num):
        return str(int(string_num, 2))

    data = []

    GPIO.setmode(GPIO.BCM)

    GPIO.setup(4, GPIO.OUT)
    GPIO.output(4, GPIO.HIGH)
    time.sleep(0.025)
    GPIO.output(4, GPIO.LOW)
    time.sleep(0.02)

    GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    for i in range(0, 500):
        data.append(GPIO.input(4))

    import pdb; pdb.set_trace()

    bit_count = 0
    tmp = 0
    count = 0
    HumidityBit = ""
    TemperatureBit = ""
    crc = ""

    try:
        while data[count] == 1:
            tmp = 1
            count = count + 1

        for i in range(0, 32):
            bit_count = 0

            while data[count] == 0:
                tmp = 1
                count = count + 1

            while data[count] == 1:
                bit_count = bit_count + 1
                count = count + 1

            if bit_count > 3:
                if i >= 0 and i < 8:
                    HumidityBit = HumidityBit + "1"
                if i >= 16 and i < 24:
                    TemperatureBit = TemperatureBit + "1"
            else:
                if i >= 0 and i < 8:
                    HumidityBit = HumidityBit + "0"
                if i >= 16 and i < 24:
                    TemperatureBit = TemperatureBit + "0"

    except:
        print("ERR_RANGE")
        exit(0)

    try:
        for i in range(0, 8):
            bit_count = 0

            while data[count] == 0:
                tmp = 1
                count = count + 1

            while data[count] == 1:
                bit_count = bit_count + 1
                count = count + 1

            if bit_count > 3:
                crc = crc + "1"
            else:
                crc = crc + "0"
    except:
        print("ERR_RANGE")
        exit(0)

    Humidity = bin2dec(HumidityBit)
    Temperature = bin2dec(TemperatureBit)

    if int(Humidity) + int(Temperature) - int(bin2dec(crc)) == 0:
        print("Humidity:" + Humidity + "%")
        print("Temperature:" + Temperature + "C")
    else:
        print("ERR_CRC")

def gp():
    import smbus
    import os
    import time
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(17, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(18, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(27, GPIO.OUT, initial=GPIO.HIGH)
    bus = smbus.SMBus(1)
    config = [0x00, 0x00]
    bus.write_i2c_block_data(0x18, 0x01, config)

    def enable(pin):
        GPIO.output(int(pin), GPIO.LOW)

    def disable(pin):
        GPIO.output(int(pin), GPIO.HIGH)

    def temp(sensor):
        if sensor == "internal":
            temp = os.popen("vcgencmd measure_temp").readline()
            ctemp = float(temp.replace("temp=", "").replace("'C", ""))
            return str(ctemp * 1.8 + 32)
        if sensor == "external":
            bus.write_byte_data(0x18, 0x08, 0x03)
            time.sleep(0.5)
            data = bus.read_i2c_block_data(0x18, 0x05, 2)
            ctemp = ((data[0] & 0x1F) * 256) + data[1]
            if ctemp > 4095:
                ctemp -= 8192
            ctemp *= 0.0625
            ftemp = ctemp * 1.8 + 32
            return str(ftemp)

    enable(PIN)
    while True:
        print("Trying to read temp from pin {}".format(PIN))
        extemp = temp("external")
        print('Temp: {} '.format(extemp))

gp2()


