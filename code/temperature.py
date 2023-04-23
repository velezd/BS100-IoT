import onewire
import time
import ds18x20
from machine import Pin


class TempSensor():
    def __init__(self):
        self.ds = ds18x20.DS18X20(onewire.OneWire(Pin(4)))
        self.device = self.ds.scan()[0]
        self.ds.convert_temp()
        time.sleep_ms(750)

    def read(self):
        """ Read the temp senced last time this function was called
        
        There has to be at least 750ms between reads """
        temp = self.ds.read_temp(self.device)
        self.ds.convert_temp()
        return str(temp)[0:4]
