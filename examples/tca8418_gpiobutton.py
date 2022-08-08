# SPDX-FileCopyrightText: Copyright (c) 2022 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

import time
import board
import adafruit_tca8418

i2c = board.I2C()  # uses board.SCL and board.SDA

from adafruit_debug_i2c import DebugI2C
debug_i2c = DebugI2C(i2c)

tca = adafruit_tca8418.TCA8418(debug_i2c)

OUTPIN = 0
INPIN = 1

tca.gpio_mode[OUTPIN] = True
tca.gpio_mode[INPIN] = True

tca.gpio_direction[OUTPIN] = True
tca.gpio_direction[INPIN] = False
tca.pullup[INPIN] = True

while True:
    tca.output_value[OUTPIN] = tca.input_value[INPIN]
    time.sleep(0.01)
