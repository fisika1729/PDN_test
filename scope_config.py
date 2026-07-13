#!/usr/bin/env python3

MODEL = "DSOX6004A"


def connect(rm):

    resources = rm.list_resources()

    for resource in resources:

        try:

            scope = rm.open_resource(resource)

            scope.timeout = 10000
            scope.write_termination = "\n"
            scope.read_termination = "\n"

            identity = scope.query("*IDN?")

            if MODEL in identity.upper():

                print("Connected to:", identity.strip())

                return scope

            scope.close()

        except Exception:
            continue

    raise RuntimeError("Keysight DSOX6004A not found")


def configure(scope):

    print("\nConfiguring Oscilloscope...")

    scope.write("*RST")
    scope.query("*OPC?")

    scope.write(":STOP")
    scope.query("*OPC?")

    scope.write(":CHAN1:DISP ON")
    scope.write(":CHAN1:COUP DC")
    scope.write(":CHAN1:PROB 10")

    scope.write(":CHAN1:SCAL 500E-3")
    scope.write(":CHAN1:OFFS 0")

    scope.write(":TIM:SCAL 1E-3")

    scope.write(":ACQ:TYPE NORM")
    scope.write(":ACQ:POIN 100000")

    scope.write(":TRIG:EDGE:SOUR CHAN1")
    scope.write(":TRIG:EDGE:SLOP POS")
    scope.write(":TRIG:LEV 3.2")

    scope.query("*OPC?")

    print("Oscilloscope configured.")


def arm(scope):

    print("\nArming Oscilloscope...")

    scope.write(":SINGLE")
    scope.query("*OPC?")

    print("Oscilloscope armed and waiting for trigger.")