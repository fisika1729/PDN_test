#!/usr/bin/env python3

import pyvisa
import time

#device configs
VENDOR_ID = 0x05E6
PRODUCT_ID = 0x2230

# Channel 3 for low voltage high current range.
CHANNEL = 3
VOLTAGE = 5.0
CURRENT_LIMIT = 1.0


rm = pyvisa.ResourceManager()
resources = rm.list_resources()

psu = None

for resource in resources:
    if f"{VENDOR_ID:04X}" in resource.upper() and \
       f"{PRODUCT_ID:04X}" in resource.upper():

        psu = rm.open_resource(resource)
        break


if psu is None:
    raise RuntimeError("Keithley 2230-30-1 not found")


#communication configs
psu.timeout = 5000
psu.write_termination = "\n"
psu.read_termination = "\n"


try:
    
    identity = psu.query("*IDN?")
    print("Connected to:", identity.strip())
    psu.write("SYSTEM:REMOTE")
    time.sleep(0.5)
    psu.write(f"INST:NSEL {CHANNEL}")
    time.sleep(0.1)
    psu.write(f"VOLT {VOLTAGE}")
    time.sleep(0.1)
    psu.write(f"CURR {CURRENT_LIMIT}")
    time.sleep(0.1)
    psu.write("OUTP ON")
    time.sleep(1)

    print(f"Channel {CHANNEL} configured to {VOLTAGE} V")
    print(f"Current limit set to {CURRENT_LIMIT} A")

finally:
    # Return instrument to local control
    psu.write("SYSTEM:LOCAL")

    psu.close()
    rm.close()
