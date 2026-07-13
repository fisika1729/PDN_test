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
