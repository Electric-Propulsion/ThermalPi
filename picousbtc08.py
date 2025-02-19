"""
Pico USB-TC08 Interface using the Python wrapper by bankrasrg.
https://github.com/bankrasrg/usbtc08
"""

import usbtc08
import atexit

class usbtc08_error(Exception):
    """USBTC08 Error definitions class. Taken directly from bankrasrg's datalogger example:
    https://github.com/bankrasrg/usbtc08/blob/master/source/usbtc08_logger.py#L473
    """
    em = {
        usbtc08.USBTC08_ERROR_OK: "No error occurred.",
        usbtc08.USBTC08_ERROR_OS_NOT_SUPPORTED: "The driver does not support the current operating system.",
        usbtc08.USBTC08_ERROR_NO_CHANNELS_SET: "A call to usb_tc08_set_channel() is required.",
        usbtc08.USBTC08_ERROR_INVALID_PARAMETER: "One or more of the function arguments were invalid.",
        usbtc08.USBTC08_ERROR_VARIANT_NOT_SUPPORTED: "The hardware version is not supported. Download the latest driver.",
        usbtc08.USBTC08_ERROR_INCORRECT_MODE: "An incompatible mix of legacy and non-legacy functions was called (or usb_tc08_get_single() was called while in streaming mode.)",
        usbtc08.USBTC08_ERROR_ENUMERATION_INCOMPLETE: "Function usb_tc08_open_unit_async() was called again while a background enumeration was already in progress.",
        usbtc08.USBTC08_ERROR_NOT_RESPONDING: "Cannot get a reply from a USB TC-08.",
        usbtc08.USBTC08_ERROR_FW_FAIL: "Unable to download firmware.",
        usbtc08.USBTC08_ERROR_CONFIG_FAIL: "Missing or corrupted EEPROM.",
        usbtc08.USBTC08_ERROR_NOT_FOUND: "Cannot find enumerated device.",
        usbtc08.USBTC08_ERROR_THREAD_FAIL: "A threading function failed.",
        usbtc08.USBTC08_ERROR_PIPE_INFO_FAIL: "Can not get USB pipe information.",
        usbtc08.USBTC08_ERROR_NOT_CALIBRATED: "No calibration date was found.",
        usbtc08.USBTC08_EROOR_PICOPP_TOO_OLD: "An old picopp.sys driver was found on the system.",
        usbtc08.USBTC08_ERROR_PICO_DRIVER_FUNCTION: "Undefined error.",
        usbtc08.USBTC08_ERROR_COMMUNICATION: "The PC has lost communication with the device."}

    def __init__(self, err = None, note = None):
        self.err = err
        self.note = note
        self.msg = ''
        if err is None:
            self.msg = note
        else:
            if type(err) is int:
                if err in self.em:
                    self.msg = f"{str(err)}: {self.em[err]}"
                    # self.msg = "%d: %s" % (err, self.em[err])
                else:
                    self.msg = f"{str(err)}: Unknown error"
                    # self.msg = "%d: Unknown error" % err
            else:
                self.msg = err
            if note is not None:
                self.msg = f"{self.msg} [{note}]"
                # self.msg = "%s [%s]" % (self.msg, note)

    def __str__(self):
        return self.msg
    

class PicoUSBTC08_Units():
    units_celsius = usbtc08.USBTC08_UNITS_CENTIGRADE
    units_fahrenheit = usbtc08.USBTC08_UNITS_FAHRENHEIT
    units_kelvin = usbtc08.USBTC08_UNITS_KELVIN


class PicoUSBTC08_ChannelData():
    def __init__(self, channel_no: int, type):
        self.channel_no: int = channel_no
        self.type: str = type
        self.last_measurement: float = 0.0

class PicoUSBTC08():

    def __init__(self):
        atexit.register(self.close_instrument) # As done by bankrasrg
        self.handle: int = None
        self.channel_buffer = usbtc08.floatArray(usbtc08.USBTC08_MAX_CHANNELS + 1)
        self.overflow_flags = usbtc08.shortArray(1)
        self.unit = PicoUSBTC08_Units.units_kelvin
        self.min_interval = None
        
        self.channel_data = {
            0: PicoUSBTC08_ChannelData(usbtc08.USBTC0_CHANNEL_CJC, 'C'),
            1: PicoUSBTC08_ChannelData(usbtc08.USBTC0_CHANNEL_1, 'K'),
            2: PicoUSBTC08_ChannelData(usbtc08.USBTC0_CHANNEL_2, 'K'),
            3: PicoUSBTC08_ChannelData(usbtc08.USBTC0_CHANNEL_3, 'K'),
            4: PicoUSBTC08_ChannelData(usbtc08.USBTC0_CHANNEL_4, 'K'),
            5: PicoUSBTC08_ChannelData(usbtc08.USBTC0_CHANNEL_5, 'K'),
            6: PicoUSBTC08_ChannelData(usbtc08.USBTC0_CHANNEL_6, 'K'),
            7: PicoUSBTC08_ChannelData(usbtc08.USBTC0_CHANNEL_7, 'K'),
            8: PicoUSBTC08_ChannelData(usbtc08.USBTC0_CHANNEL_8, 'K'),
        }

    def check_for_error(self, return_value: int, caller: callable):
        """Checks return value of a usbtc08 function and if an error ocurred, returns the error. 

        Args:
            return_value (int): Return value from the function just called.
            caller (callable): Function in this Python class which was called.

        Raises:
            usbtc08_error: _description_
        """
        if return_value == 0:
            raise usbtc08_error(usbtc08.usb_tc08_get_last_error(self.handle), f'Error when calling: {caller.__name__}')

    def open_instrument(self) -> None:
        rv = usbtc08.usb_tc08_open_unit() 
        if rv > 0:
            self.handle = rv
        elif rv == 0:
            print("No more Pico USB TC-08 are available to open.")
            return
        elif rv == -1:
            self.check_for_error(0, self.open_instrument)

        # Obtain minimum measurment interval for device
        rv = usbtc08.usbtc08_get_minimum_interval_ms(self.handle)
        self.check_for_error(rv)
        self.min_interval = rv
    
    def close_instrument(self) -> None:
        rv = usbtc08.usb_tc08_close_unit(self.handle)
        self.check_for_error(rv, self.close_instrument)

    def enable_sampling(self, sampling_interval: float) -> None:
        assert sampling_interval >= self.min_interval
        rv = usbtc08.usb_tc08_run(self.handle, sampling_interval)
        self.check_for_error(rv, self.enable_sampling)
    
    def disable_sampling(self) -> None:
        rv = usbtc08.usb_tc08_stop(self.handle)
        self.check_for_error(rv, self.disable_sampling)

    def configure_channel(self, channel: int, type: str) -> None:
        if channel == usbtc08.USBTC0_CHANNEL_CJC:
            assert type == 'C'
        else:
            assert type in ('B', 'E', 'J', 'K', 'N', 'R', 'S', 'T', '')

        self.channel_data[channel].type = type
        rv = usbtc08.usb_tc08_set_channel(self.handle, channel, ord(type))
        self.check_for_error(rv, self.configure_channel)
    
    def disable_channel(self, channel: int) -> None:
        self.configure_channel(channel, '')
    
    def measure_all_channels(self) -> float:
        rv = usbtc08.usb_tc08_get_single(self.handle, self.channel_buffer, self.overflow_flags, self.unit)
        
        if rv == 0:
            self.check_for_error(rv, self.measure_all_channels)
        else:
            for i in range(len(self.channel_data)):
                self.channel_data[i].last_measurement = self.channel_buffer[i]