#!/usr/bin/env python3

import usbtmc

# Open USBTMC connection
# Keithley vendor ID = 0x05E6
# Product ID = 0x2230
psu = usbtmc.Instrument(0x05E6, 0x2230)

# Verify instrument connection
print(psu.ask("*IDN?"))

# Select Channel 3
psu.write("INST:NSEL 3")

# Set output voltage to 5 V
psu.write("VOLT 5.0")

# Set current limit to 5 A
psu.write("CURR 5.0")

# Enable power supply output
psu.write("OUTP ON")

print("Power supply configured to 5 V")

psu.close()
