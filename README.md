## Project: Capacitance Touch Sensor
This project consists in the use of a programmed RP2040 to use its pins as capacitance sensors, turning them into touch-interactible gadgets. These gadgets are responsible for emitting a frequency vibration to the amplifier and make things jump according to your touch. 

Thus, in this repository you can find the Seeed Studio RP2040 code (hopefully commented) with the main libraries and bugs.  

## Funcionalities
- Adjustable touch sensibility
- Personalizable frequency tone to make the speakers' membrane vibrate
- Code implemented using *CircuitPython* for RP2040 microcontroller. 

## Needed hardware
- Adafruit Max9744 (20W) or similar amplifier
- XIAO Seeed RP2040 or similar microcontroller
- USB-C cable
- Propper power supply (12V)
- Potenciometer
- Some wiring for the ground, 3V and SCL/SDA pins

## Current bugs
- The columns do play the sound, but either the sample rate is using the wrong bit codification or the amplifier isn't capable of playing a propper 16Hz frequency sound because it doesn't sound like it at all. 
- The potentiometer input has some stability issues, which causes some sensibility oscillation. 

## Developed by
- Delmont Maria, Maurício Martins

