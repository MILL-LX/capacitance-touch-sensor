# SPDX-FileCopyrightText: 2018 Tony DiCola for Adafruit Industries
# SPDX-License-Identifier: MIT

# Simple demo of the MAX9744 20W class D amplifier I2C control.
# This show how to set the volume of the amplifier.
import board
import busio
import adafruit_max9744

# Initialize I2C bus.
i2c = busio.I2C(board.SCL, board.SDA)

# Initialize amplifier.
amp = adafruit_max9744.MAX9744(i2c)
# Optionally you can specify a different addres if you override the AD1, AD2
# pins to change the address.
# amp = adafruit_max9744.MAX9744(i2c, address=0x49)

# Setting the volume is as easy as writing to the volume property (note
# you cannot read the property so keep track of volume in your own code if
# you need it).
amp.volume = 31  # Volume is a value from 0 to 63 where 0 is muted/off and
# 63 is maximum volume.
volume = 31

quit = False
while not quit:
    choice = input("Higher(+), lower(-) or quit(q)?: ")
    choice.strip('\n')
    plus = choice.count("+", 0, len(choice))
    minus = choice.count("-", 0, len(choice))
    if plus > 0 and volume < 63:
        aux = plus
        while aux > 0:
            amp.volume_up()
            volume += 1
            print("Setting volume to " + str(volume))
            aux -= 1
    if minus > 0 and volume > 0:
        aux = minus
        while aux > 0:
            amp.volume_down()
            volume += 1
            print("Setting volume to " + str(volume))
            aux -= 1
    if choice == "q":
        quit = True