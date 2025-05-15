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

* `TCA8418 keyboard multiplexor <http://www.adafruit.com/products/4918>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloadss

# * Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
# * Adafruit's Register library: https://github.com/adafruit/Adafruit_CircuitPython_Register
"""

import digitalio
from adafruit_bus_device import i2c_device
from adafruit_register.i2c_bit import RWBit
from adafruit_register.i2c_bits import ROBits
from micropython import const

try:
    from typing import Optional

    from busio import I2C
    from typing_extensions import Literal
except ImportError:
    pass

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_TCA8418.git"

TCA8418_I2CADDR_DEFAULT: int = const(0x34)  # Default I2C address

_TCA8418_REG_CONFIG = const(0x01)
_TCA8418_REG_INTSTAT = const(0x02)
_TCA8418_REG_KEYLCKEC = const(0x03)
_TCA8418_REG_KEYEVENT = const(0x04)

_TCA8418_REG_GPIODATSTAT1 = const(0x14)
_TCA8418_REG_GPIODATOUT1 = const(0x17)
_TCA8418_REG_INTEN1 = const(0x1A)
_TCA8418_REG_KPGPIO1 = const(0x1D)
_TCA8418_REG_GPIOINTSTAT1 = const(0x11)

_TCA8418_REG_EVTMODE1 = const(0x20)
_TCA8418_REG_GPIODIR1 = const(0x23)
_TCA8418_REG_INTLVL1 = const(0x26)
_TCA8418_REG_DEBOUNCEDIS1 = const(0x29)
_TCA8418_REG_GPIOPULL1 = const(0x2C)


class TCA8418_register:
    """A class for interacting with the TCA8418 registers

    :param TCA8418 tca: The associated TCA8418 object
    :param int base_addr: The base address for this register
    :param bool invert_value: Whether the value given should be interpreted as inverted
        (True -> False), default is False (inputs are as-is, not inverted)
    :param bool read_only: Whether the register is read-only or read/write, default
        is False (register is read/write)
    :param int|None initial_value: An initial value to provide to the register, default
        is ``None`` (no default is provided)
    """

    def __init__(
        self,
        tca: "TCA8418",
        base_addr: int,
        invert_value: bool = False,
        read_only: bool = False,
        initial_value: Optional[int] = None,
    ) -> None:
        self._tca = tca
        self._baseaddr = base_addr
        self._invert = invert_value
        self._ro = read_only

        # theres 3 registers in a row for each setting
        if not read_only and initial_value is not None:
            self._tca._write_reg(base_addr, initial_value)
            self._tca._write_reg(base_addr + 1, initial_value)
            self._tca._write_reg(base_addr + 2, initial_value)

    def __index__(self) -> int:
        """Read all 18 bits of register data and return as one integer"""
        val = self._tca._read_reg(self._baseaddr + 2)
        val <<= 8
        val |= self._tca._read_reg(self._baseaddr + 1)
        val <<= 8
        val |= self._tca._read_reg(self._baseaddr)
        val &= 0x3FFFF
        return val

    def __getitem__(self, pin_number: int) -> bool:
        """Read the single bit at 'pin_number' offset"""
        value = self._tca._get_gpio_register(self._baseaddr, pin_number)
        if self._invert:
            value = not value
        return value

    def __setitem__(self, pin_number: int, value: bool) -> None:
        """Set a single bit at 'pin_number' offset to 'value'"""
        if self._ro:
            raise NotImplementedError("Read only register")
        if self._invert:
            value = not value
        self._tca._set_gpio_register(self._baseaddr, pin_number, value)


class TCA8418:
    """Driver for the TCA8418 I2C Keyboard expander / multiplexor.

    :param ~busio.I2C i2c_bus: The I2C bus the TCA8418 is connected to.
    :param address: The I2C device address. Defaults to :const:`0x34`
    """

    events_count = ROBits(4, _TCA8418_REG_KEYLCKEC, 0)
    cad_int = RWBit(_TCA8418_REG_INTSTAT, 4)
    overflow_int = RWBit(_TCA8418_REG_INTSTAT, 3)
    keylock_int = RWBit(_TCA8418_REG_INTSTAT, 2)
    gpi_int = RWBit(_TCA8418_REG_INTSTAT, 1)
    key_int = RWBit(_TCA8418_REG_INTSTAT, 0)

    gpi_event_while_locked = RWBit(_TCA8418_REG_CONFIG, 6)
    overflow_mode = RWBit(_TCA8418_REG_CONFIG, 5)
    int_retrigger = RWBit(_TCA8418_REG_CONFIG, 4)
    overflow_intenable = RWBit(_TCA8418_REG_CONFIG, 3)
    keylock_intenable = RWBit(_TCA8418_REG_CONFIG, 2)
    GPI_intenable = RWBit(_TCA8418_REG_CONFIG, 1)
    key_intenable = RWBit(_TCA8418_REG_CONFIG, 0)

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

    # pylint: enable=invalid-name

    def __init__(self, i2c_bus: I2C, address: int = TCA8418_I2CADDR_DEFAULT) -> None:
        self.i2c_device = i2c_device.I2CDevice(i2c_bus, address)
        self._buf = bytearray(2)

        # disable all interrupt
        self.enable_int = TCA8418_register(self, _TCA8418_REG_INTEN1, initial_value=0)
        self.gpio_int_status = TCA8418_register(self, _TCA8418_REG_GPIOINTSTAT1, read_only=True)
        _ = self.gpio_int_status  # read to clear

        # plain GPIO expansion as indexable properties

        # set all pins to inputs
        self.gpio_direction = TCA8418_register(self, _TCA8418_REG_GPIODIR1, initial_value=0)
        # set all pins to GPIO
        self.gpio_mode = TCA8418_register(
            self, _TCA8418_REG_KPGPIO1, invert_value=True, initial_value=0
        )
        self.keypad_mode = TCA8418_register(self, _TCA8418_REG_KPGPIO1)
        # set all pins low output
        self.output_value = TCA8418_register(self, _TCA8418_REG_GPIODATOUT1, initial_value=0)
        self.input_value = TCA8418_register(self, _TCA8418_REG_GPIODATSTAT1, read_only=True)
        # enable all pullups
        self.pullup = TCA8418_register(
            self, _TCA8418_REG_GPIOPULL1, invert_value=True, initial_value=0
        )
        # enable all debounce
        self.debounce = TCA8418_register(
            self, _TCA8418_REG_DEBOUNCEDIS1, invert_value=True, initial_value=0
        )
        # default int on falling
        self.int_on_rising = TCA8418_register(self, _TCA8418_REG_INTLVL1, initial_value=0)

        # default no gpio in event queue
        self.event_mode_fifo = TCA8418_register(self, _TCA8418_REG_EVTMODE1, initial_value=0)

        # read in event queue
        # print(self.events_count, "events")
        while self.events_count:
            _ = self.next_event  # read and toss

        # reset interrutps
        self._write_reg(_TCA8418_REG_INTSTAT, 0x1F)
        self.gpi_int = False

    @property
    def next_event(self) -> int:
        """The next key event"""

        if self.events_count == 0:
            raise RuntimeError("No events in FIFO")
        return self._read_reg(_TCA8418_REG_KEYEVENT)

    def _set_gpio_register(self, reg_base_addr: int, pin_number: int, value: bool) -> None:
        if not 0 <= pin_number <= 17:
            raise ValueError("Pin number must be between 0 & 17")
        reg_base_addr += pin_number // 8
        self._set_reg_bit(reg_base_addr, pin_number % 8, value)

    def _get_gpio_register(self, reg_base_addr: int, pin_number: int) -> bool:
        if not 0 <= pin_number <= 17:
            raise ValueError("Pin number must be between 0 & 17")
        reg_base_addr += pin_number // 8
        return self._get_reg_bit(reg_base_addr, pin_number % 8)

    def get_pin(self, pin: int) -> "DigitalInOut":
        """Convenience function to create an instance of the DigitalInOut class
        pointing at the specified pin of this TCA8418 device.

        :param int pin: Pin to use for digital IO, 0 to 17 inclusive; you can
            use the pins like TCA8418.R3 or TCA8418.C4 for convenience
        """
        assert 0 <= pin <= 17
        return DigitalInOut(pin, self)

    # register helpers

    def _set_reg_bit(self, addr: int, bitoffset: int, value: bool) -> None:
        temp = self._read_reg(addr)
        if value:
            temp |= 1 << bitoffset
        else:
            temp &= ~(1 << bitoffset)
        self._write_reg(addr, temp)

    def _get_reg_bit(self, addr: int, bitoffset: int) -> bool:
        temp = self._read_reg(addr)
        return bool(temp & (1 << bitoffset))

    def _write_reg(self, addr: int, val: int) -> None:
        with self.i2c_device as i2c:
            self._buf[0] = addr
            self._buf[1] = val
            i2c.write(self._buf, end=2)

    def _read_reg(self, addr: int) -> int:
        with self.i2c_device as i2c:
            self._buf[0] = addr
            i2c.write_then_readinto(self._buf, self._buf, out_end=1, in_end=1)
        return self._buf[0]


class DigitalInOut:
    """Digital input/output of the TCA8418.  The interface is exactly the
    same as the digitalio.DigitalInOut class, however:

      - TCA8418 does not support pull-down resistors

    Exceptions will be thrown when attempting to set unsupported pull
    configurations.

    * Author(s): Tony DiCola

    :param int pin_number: The pin number to use
    :param TCA8418 tca: The TCA8418 object associated with the DIO
    """

    def __init__(self, pin_number: int, tca: "TCA8418") -> None:
        """Specify the pin number of the TCA8418 0..17, and instance."""
        self._pin = pin_number
        self._tca = tca
        self._tca.gpio_mode[pin_number] = True

    # kwargs in switch functions below are _necessary_ for compatibility
    # with DigitalInout class (which allows specifying pull, etc. which
    # is unused by this class).  Do not remove them, instead turn off pylint
    # in this case.
    def switch_to_output(self, value: bool = False, **kwargs) -> None:
        """Switch the pin state to a digital output with the provided starting
        value (True/False for high or low, default is False/low).
        """
        self.direction = digitalio.Direction.OUTPUT
        self.value = value

    def switch_to_input(self, pull: Optional[digitalio.Pull] = None, **kwargs) -> None:
        """Switch the pin state to a digital input which is the same as
        setting the light pullup on.  Note that true tri-state or
        pull-down resistors are NOT supported!
        """
        self.direction = digitalio.Direction.INPUT
        self.pull = pull

    @property
    def value(self) -> bool:
        """The value of the pin, either True for high/pulled-up or False for
        low.
        """
        return self._tca.input_value[self._pin]

    @value.setter
    def value(self, val: bool) -> None:
        self._tca.output_value[self._pin] = val

    @property
    def direction(self) -> digitalio.Direction:
        """The direction of the pin, works identically to
        the one in `digitalio`
        """
        return self._dir

    @direction.setter
    def direction(self, val: digitalio.Direction) -> None:
        if val == digitalio.Direction.INPUT:
            self._tca.gpio_direction[self._pin] = False
        elif val == digitalio.Direction.OUTPUT:
            self._tca.gpio_direction[self._pin] = True
        else:
            raise ValueError("Expected INPUT or OUTPUT direction!")

        self._dir = val

    @property
    def pull(self) -> Optional[Literal[digitalio.Pull.UP]]:
        """The pull setting for the digital IO, either `digitalio.Pull.UP`
        for pull up, or ``None`` for no pull up
        """

        if self._tca.pullup[self._pin]:
            return digitalio.Pull.UP
        return None

    @pull.setter
    def pull(self, val: Optional[Literal[digitalio.Pull.UP]]) -> None:
        if val is digitalio.Pull.UP:
            # for inputs, turn on the pullup (write high)
            self._tca.pullup[self._pin] = True
        elif val is None:
            self._tca.pullup[self._pin] = False
        else:
            raise NotImplementedError("Pull-down resistors not supported.")
