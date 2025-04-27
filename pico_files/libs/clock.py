from machine import Pin, I2C, RTC
import utime

class PicoRTC:
    def __init__(self, i2c_id=1, sda_pin=6, scl_pin=7):
        self.i2c = I2C(i2c_id, sda=Pin(sda_pin), scl=Pin(scl_pin))
        self.address = 0x68  # Default I2C address for PCF8523
    
    def bcd_to_int(self, bcd):
        return (bcd // 16) * 10 + (bcd % 16)

    def int_to_bcd(self, n):
        return (n // 10) * 16 + (n % 10)

    def get(self):
        """Reads the current time from the PCF8523 and returns it."""
        data = self.i2c.readfrom_mem(self.address, 0x03, 7)
        second = self.bcd_to_int(data[0] & 0x7F)
        minute = self.bcd_to_int(data[1])
        hour = self.bcd_to_int(data[2])
        day = self.bcd_to_int(data[3])
        month = self.bcd_to_int(data[5] & 0x1F)
        year = self.bcd_to_int(data[6]) + 2000
        return (year, month, day, 0, hour, minute, second, 0)
    
    def set(self, year, month, day, hour, minute, second):
        """Sets the time on the PCF8523."""
        year -= 2000
        self.i2c.writeto_mem(self.address, 0x03, bytearray([
            self.int_to_bcd(second),
            self.int_to_bcd(minute),
            self.int_to_bcd(hour),
            self.int_to_bcd(day),
            0,  # Not using weekdays
            self.int_to_bcd(month),
            self.int_to_bcd(year)
        ]))
    
    def sync(self):
        """Syncs the time from the external RTC to the internal RTC."""
        year, month, day, weekday, hour, minute, second, empty = self.get()
        internal_time = (year, month, day, weekday, hour, minute, second, 0)
        internal_rtc = RTC()
        internal_rtc.datetime(internal_time)
        
    def time(self):
        """Prints the current date and time in MM/DD/YYYY HH:MM:SS format."""
        year, month, day, _, hour, minute, second, _ = self.get()
        formatted_time = f"{month:02}/{day:02}/{year} {hour:02}:{minute:02}:{second:02}"
        return formatted_time