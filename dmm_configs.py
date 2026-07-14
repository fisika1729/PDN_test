#!/usr/bin/env python3

MODEL = "DMM6500"


def connect(rm):

    resources = rm.list_resources()

    for resource in resources:

        try:

            dmm = rm.open_resource(resource)

            dmm.timeout = 5000
            dmm.write_termination = "\n"
            dmm.read_termination = "\n"

            identity = dmm.query("*IDN?")

            if MODEL in identity.upper():

                print("Connected to:", identity.strip())

                return dmm

            dmm.close()

        except Exception:
            continue

    raise RuntimeError("Keithley DMM6500 not found")


def configure(dmm):

    print("\nConfiguring DMM...")

    dmm.write("*RST")
    dmm.query("*OPC?")

    dmm.write("SENS:FUNC 'VOLT:DC'")
    dmm.write("SENS:VOLT:DC:RANG:AUTO ON")

    dmm.write("SENS:VOLT:DC:NPLC 1")

    dmm.write("TRIG:LOAD 'SimpleLoop',1")

    dmm.query("*OPC?")

    print("DMM configured.")