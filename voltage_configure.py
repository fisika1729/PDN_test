import pyvisa
import time

VENDOR_ID = 0x05E6
PRODUCT_ID = 0x2230

CHANNEL = 3
VOLTAGE = 5.0
CURRENT_LIMIT = 1.0


def connect(rm):

    resources = rm.list_resources()

    for resource in resources:

        if f"{VENDOR_ID:04X}" in resource.upper() and \
           f"{PRODUCT_ID:04X}" in resource.upper():

            psu = rm.open_resource(resource)

            psu.timeout = 5000
            psu.write_termination = "\n"
            psu.read_termination = "\n"

            print(psu.query("*IDN?").strip())

            return psu

    raise RuntimeError("Keithley 2230 not found")


def configure(psu):

    psu.write("SYSTEM:REMOTE")
    time.sleep(0.5)

    psu.write(f"INST:NSEL {CHANNEL}")
    psu.write(f"VOLT {VOLTAGE}")
    psu.write(f"CURR {CURRENT_LIMIT}")
    psu.write("OUTP ON")

    print("PSU configured.")