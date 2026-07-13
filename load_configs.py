import time


def connect_load(rm):
    resources = rm.list_resources()

    for resource in resources:
        try:
            instrument = rm.open_resource(resource)
            instrument.timeout = 5000
            instrument.write_termination = "\n"
            instrument.read_termination = "\n"

            identity = instrument.query("*IDN?")

            if "2380" in identity.upper():
                print("Connected to:", identity.strip())
                return instrument

            instrument.close()

        except Exception:
            continue

    raise RuntimeError("Keithley 2380 not found")


def configure_load(load):
    load.write("*RST")
    time.sleep(0.5)

    load.write("SYST:REM")
    time.sleep(0.5)

    print("Electronic load ready")
