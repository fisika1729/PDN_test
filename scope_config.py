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


def configure(scope, trigger_level=3.2):

    print("\nConfiguring Oscilloscope...")

    scope.write("*RST")
    scope.query("*OPC?")

    scope.write(":STOP")
    scope.query("*OPC?")

    scope.write(":CHANnel1:DISPlay ON")
    scope.write(":CHANnel1:COUPling DC")
    scope.write(":CHANnel1:PROBe 10")

    scope.write(":CHANnel1:SCALe 500E-3")
    scope.write(":CHANnel1:OFFSet 0")

    scope.write(":TIMebase:SCALe 1E-3")

    scope.write(":ACQuire:TYPE NORM")
    scope.write(":ACQuire:POINts 100000")

    scope.write(":TRIGger:EDGE:SOURce CHANnel1")
    scope.write(":TRIGger:EDGE:SLOPe POSitive")

    if trigger_level is not None:
        scope.write(f":TRIGger:LEVel {trigger_level}")

    scope.query("*OPC?")

    print("Oscilloscope configured.")


def arm(scope):

    print("\nArming Oscilloscope...")

    scope.write(":SINGLE")
    scope.query("*OPC?")

    print("Oscilloscope armed and waiting for trigger.")