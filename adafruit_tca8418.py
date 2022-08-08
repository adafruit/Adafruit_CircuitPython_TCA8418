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
_TCA8418_REG_KPGPIO1 = const(0x1D)
_TCA8418_REG_GPIODIR1 = const(0x23)
_TCA8418_REG_DEBOUNCE1 = const(0x29)
_TCA8418_REG_GPIOPULL1 = const(0x2C)

class TCA_reg_prop:
    def __init__(self, tca, base_addr, invert_value=False):
        self._tca = tca
        self._baseaddr = base_addr
        self._invert = invert_value

    def __getitem__(self, pin_number):
        value = self._tca._get_gpio_register(self._baseaddr, pin_number)
        if self._invert:
            value = not value
        return value

    def __setitem__(self, pin_number, value):
        if self._invert:
            value = not value
        self._tca._set_gpio_register(self._baseaddr, pin_number, value)


class TCA8418:
    """Driver for the TCA8418 I2C Keyboard expander / multiplexor.
    :param ~busio.I2C i2c_bus: The I2C bus the TCA8418 is connected to.
    :param address: The I2C device address. Defaults to :const:`0x34`
    """

    def __init__(self, i2c_bus, address=TCA8418_I2CADDR_DEFAULT):
        # pylint: disable=no-member
        self.i2c_device = i2c_device.I2CDevice(i2c_bus, address)
        self._buf = bytearray(2)
        
        # plain GPIO expansion as indexable properties
        self.gpio_mode = TCA_reg_prop(self, _TCA8418_REG_KPGPIO1, invert_value=True)
        self.gpio_direction = TCA_reg_prop(self,_TCA8418_REG_GPIODIR1)
        self.keypad_mode = TCA_reg_prop(self, _TCA8418_REG_KPGPIO1)
        self.output_value = TCA_reg_prop(self, _TCA8418_REG_GPIODIR1)
        self.input_value = TCA_reg_prop(self, _TCA8418_REG_GPIODATSTAT1)
        self.pullup = TCA_reg_prop(self, _TCA8418_REG_GPIOPULL1, invert_value=True)


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
