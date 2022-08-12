# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2022 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_tca8418`
================================================================================

CircuitPython / Python library for TCA8418 Keyboard Multiplexor


* Author(s): ladyada

Implementation Notes
--------------------

**Hardware:**

.. todo:: Add links to any specific hardware product page(s), or category page(s).
  Use unordered list & hyperlink rST inline format: "* `Link Text <url>`_"

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads

.. todo:: Uncomment or remove the Bus Device and/or the Register library dependencies
  based on the library's use of either.

# * Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
# * Adafruit's Register library: https://github.com/adafruit/Adafruit_CircuitPython_Register
"""

# imports

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_TCA8418.git"

from micropython import const
from adafruit_bus_device import i2c_device

TCA8418_I2CADDR_DEFAULT: int = const(0x34)  # Default I2C address

_TCA8418_REG_GPIODATSTAT1 = const(0x14)
_TCA8418_REG_GPIODATOUT1 = const(0x17)
_TCA8418_REG_INTEN1 = const(0x1A)
_TCA8418_REG_KPGPIO1 = const(0x1D)
_TCA8418_REG_GPIOINTSTAT1 = const(0x11)

_TCA8418_REG_EVTMODE1 = const(0x20)

_TCA8418_REG_GPIODIR1 = const(0x23)
_TCA8418_REG_INTLVL1 = const(0x29)
_TCA8418_REG_DEBOUNCEDIS1 = const(0x29)
_TCA8418_REG_GPIOPULL1 = const(0x2C)

class TCA8418_register:
    def __init__(self, tca, base_addr, invert_value=False, read_only=False, initial_value=None):
        self._tca = tca
        self._baseaddr = base_addr
        self._invert = invert_value
        self._ro = read_only
        
        # theres 3 registers in a row for each setting
        if not read_only and initial_value is not None:
            self._tca._write_reg(base_addr, initial_value)
            self._tca._write_reg(base_addr+1, initial_value)
            self._tca._write_reg(base_addr+2, initial_value)

    def __index__(self):
        """Read all 18 bits of register data and return as one integer"""
        val = self._tca._read_reg(self._baseaddr+2)
        val <<= 8
        val |= self._tca._read_reg(self._baseaddr+1)
        val <<= 8
        val |= self._tca._read_reg(self._baseaddr)
        val &= 0x3FFFF
        return val

    def __getitem__(self, pin_number):
        """Read the single bit at 'pin_number' offset"""
        value = self._tca._get_gpio_register(self._baseaddr, pin_number)
        if self._invert:
            value = not value
        return value

    def __setitem__(self, pin_number, value):
        """Set a single bit at 'pin_number' offset to 'value'"""
        if self._ro:
            raise NotimplementedErrror("Read only register")
        if self._invert:
            value = not value
        self._tca._set_gpio_register(self._baseaddr, pin_number, value)



class TCA8418:
    """Driver for the TCA8418 I2C Keyboard expander / multiplexor.
    :param ~busio.I2C i2c_bus: The I2C bus the TCA8418 is connected to.
    :param address: The I2C device address. Defaults to :const:`0x34`
    """

    R0 = 0
    R1 = 1
    R2 = 2
    R3 = 3
    R4 = 4
    R5 = 5
    R6 = 6
    R7 = 7
    C0 = 8
    C1 = 9
    C2 = 10
    C3 = 11
    C4 = 12
    C5 = 13
    C6 = 14
    C7 = 15
    C8 = 16
    C9 = 17
    
    def __init__(self, i2c_bus, address=TCA8418_I2CADDR_DEFAULT):
        # pylint: disable=no-member
        self.i2c_device = i2c_device.I2CDevice(i2c_bus, address)
        self._buf = bytearray(2)

        # plain GPIO expansion as indexable properties

        # set all pins to inputs
        self.gpio_direction = TCA8418_register(self,_TCA8418_REG_GPIODIR1, initial_value=0)
        # set all pins to GPIO
        self.gpio_mode = TCA8418_register(self, _TCA8418_REG_KPGPIO1, invert_value=True, initial_value=0)
        self.keypad_mode = TCA8418_register(self, _TCA8418_REG_KPGPIO1)
        # set all pins low output
        self.output_value = TCA8418_register(self, _TCA8418_REG_GPIODATOUT1, initial_value=0)
        self.input_value = TCA8418_register(self, _TCA8418_REG_GPIODATSTAT1, read_only=True)
        # enable all pullups
        self.pullup = TCA8418_register(self, _TCA8418_REG_GPIOPULL1, invert_value=True, initial_value=0)
        # enable all debounce
        self.debounce = TCA8418_register(self, _TCA8418_REG_DEBOUNCEDIS1, invert_value=True, initial_value=0)
        # default int on falling
        self.int_on_rising = TCA8418_register(self, _TCA8418_REG_INTLVL1, initial_value=0)
        # disable all interrupt
        self.enable_int = TCA8418_register(self, _TCA8418_REG_INTEN1, initial_value=0)
        self.gpio_int_status = TCA8418_register(self, _TCA8418_REG_GPIOINTSTAT1, read_only=True)

    def _set_gpio_register(self, reg_base_addr, pin_number, value):
        if not 0 <= pin_number <= 17:
            raise ValueError("Pin number must be between 0 & 17")
        reg_base_addr +=  pin_number // 8
        self._set_reg_bit(reg_base_addr, pin_number % 8, value)


    def _get_gpio_register(self, reg_base_addr, pin_number):
        if not 0 <= pin_number <= 17:
            raise ValueError("Pin number must be between 0 & 17")
        reg_base_addr +=  pin_number // 8
        return self._get_reg_bit(reg_base_addr, pin_number % 8)


    # register helpers

    def _set_reg_bit(self, addr, bitoffset, value):
        temp = self._read_reg(addr)
        if value:
            temp |= (1 << bitoffset)
        else:
            temp &= ~(1 << bitoffset)
        self._write_reg(addr, temp)

    def _get_reg_bit(self, addr, bitoffset):
        temp = self._read_reg(addr)
        return bool(temp & (1 << bitoffset))
    

    def _write_reg(self, addr, val):
        with self.i2c_device as i2c:
            self._buf[0] = addr
            self._buf[1] = val            
            i2c.write(self._buf, end=2)

    def _read_reg(self, addr):
        with self.i2c_device as i2c:
            self._buf[0] = addr
            i2c.write_then_readinto(self._buf, self._buf, out_end=1, in_end=1)
        return self._buf[0]
