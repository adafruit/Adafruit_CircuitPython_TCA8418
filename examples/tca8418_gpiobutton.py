# SPDX-FileCopyrightText: Copyright (c) 2022 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

import time
import board
from adafruit_tca8418 import TCA8418

i2c = board.I2C()  # uses board.SCL and board.SDA
tca = TCA8418(i2c)

# setup 2 gpio: LED on R0 and button in R1
OUTPIN = TCA8418.R0
INPIN = TCA8418.R1
tca.gpio_mode[OUTPIN] = True
tca.gpio_mode[INPIN] = True

# one is output, other is input with pullup
tca.gpio_direction[OUTPIN] = True
tca.gpio_direction[INPIN] = False
tca.pullup[INPIN] = True

# have LED mirror button
while True:
    tca.output_value[OUTPIN] = tca.input_value[INPIN]
    time.sleep(0.01)
