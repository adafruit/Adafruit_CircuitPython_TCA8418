# SPDX-FileCopyrightText: Copyright (c) 2022 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

import time

import board

from adafruit_tca8418 import TCA8418

i2c = board.I2C()  # uses board.SCL and board.SDA
# i2c = board.STEMMA_I2C()  # For using the built-in STEMMA QT connector on a microcontroller
tca = TCA8418(i2c)

# setup R0 as an output GPIO
OUTPIN = TCA8418.R0
tca.gpio_mode[OUTPIN] = True
tca.gpio_direction[OUTPIN] = True

# blink it!
while True:
    tca.output_value[OUTPIN] = True
    time.sleep(0.1)
    tca.output_value[OUTPIN] = False
    time.sleep(0.1)
