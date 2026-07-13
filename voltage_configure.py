#!/usr/bin/env python3

import pyvisa
import time

VENDOR_ID = 0x05E6
PRODUCT_ID = 0x2230

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
    rm.close()
    raise RuntimeError("Keithley 2230-30-1 not found")

psu.timeout = 5000
psu.write_termination = "\n"
psu.read_termination = "\n"

try:
    identity = psu.query("*IDN?")
    print("Connected to:", identity.strip())

    psu.write("SYSTEM:REMOTE")
    time.sleep(0.5)

    psu.write(f"INST:NSEL {CHANNEL}")
    psu.write(f"VOLT {VOLTAGE}")
    psu.write(f"CURR {CURRENT_LIMIT}")
    psu.write("OUTP ON")

    print(f"Channel {CHANNEL} configured to {VOLTAGE} V")
    print(f"Current limit set to {CURRENT_LIMIT} A")

    while True:
        command = input("> ").strip()

        if command.lower() == "local":
            psu.write("SYSTEM:LOCAL")
            print("Local mode")
            break

        if command.upper().startswith("C="):
            try:
                current = float(command.split("=", 1)[1])

                if current < 0 or current > 5.0:
                    print("Current must be between 0 and 5 A")
                    continue

                psu.write("SYSTEM:REMOTE")
                psu.write(f"INST:NSEL {CHANNEL}")
                psu.write(f"CURR {current}")

                print(f"Current limit set to {current} A")

            except ValueError:
                print("Invalid current value")

finally:
    psu.close()
    rm.close()
