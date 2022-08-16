# SPDX-FileCopyrightText: Copyright (c) 2022 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

import time
import board
from adafruit_tca8418 import TCA8418

i2c = board.I2C()  # uses board.SCL and board.SDA

from adafruit_debug_i2c import DebugI2C
debug_i2c = DebugI2C(i2c)

tca = TCA8418(i2c)

# set up all R pins and some of the C pins as GPIO pins
INPINS = (TCA8418.R0, TCA8418.R1, TCA8418.R2, TCA8418.R3, 
          TCA8418.R4, TCA8418.R5, TCA8418.R6, TCA8418.R7,
          TCA8418.C0, TCA8418.C1, TCA8418.C2, TCA8418.C3,)

# make them inputs with pullups
for pin in INPINS:
    tca.gpio_mode[pin] = True
    tca.gpio_direction[pin] = False
    tca.pullup[pin] = True

    # make sure the in pin generates FIFO events
    tca.enable_int[pin] = True
    tca.event_mode_fifo[pin] = True

while True:
    if tca.GPI_int:
        # print("IRQ! ", hex(int(tca.gpio_int_status)))
        events = tca.events_count
        for _ in range(events):
            keyevent = tca.next_event
            print("\tKey event: 0x%02X - GPIO #%d "  % (keyevent, (keyevent&0xF) - 1), end="")
            if keyevent & 0xF0 == 0xE0:
                print("key down")
            if keyevent & 0xF0 == 0x60:
                print("key up")
        tca.GPI_int = True # clear the IRQ by writing 1 to it

