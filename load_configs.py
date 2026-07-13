import time

MODEL = "2380"


def connect(rm):
    resources = rm.list_resources()

    for resource in resources:
        try:
            load = rm.open_resource(resource)
            load.timeout = 5000
            load.write_termination = "\n"
            load.read_termination = "\n"

            identity = load.query("*IDN?")

            if MODEL in identity.upper():
                print("Connected to:", identity.strip())
                return load

            load.close()

        except Exception:
            continue

    raise RuntimeError("Keithley 2380 not found")


def create():
    print("\nLoad transient configuration")

    max_current = float(input("Maximum current rating (A): "))
    lower_percentage = float(input("Lower load threshold (%): "))
    upper_percentage = float(input("Upper load threshold (%): "))
    duty_cycle = float(input("Duty cycle (%): "))
    frequency = float(input("Transient frequency (Hz): "))
    duration = float(input("Test duration (s): "))

    if max_current <= 0:
        raise ValueError("Maximum current must be greater than 0")

    if not 0 <= lower_percentage <= 100:
        raise ValueError("Lower threshold must be between 0 and 100")

    if not 0 <= upper_percentage <= 100:
        raise ValueError("Upper threshold must be between 0 and 100")

    if upper_percentage <= lower_percentage:
        raise ValueError("Upper threshold must be greater than lower threshold")

    if not 0 < duty_cycle < 100:
        raise ValueError("Duty cycle must be between 0 and 100")

    if not 0.01 <= frequency <= 25000:
        raise ValueError("Frequency must be between 0.01 Hz and 25 kHz")

    if duration <= 0:
        raise ValueError("Duration must be greater than 0")

    low_current = max_current * lower_percentage / 100
    high_current = max_current * upper_percentage / 100

    period = 1 / frequency
    high_time = period * duty_cycle / 100
    low_time = period - high_time

    config = {
        "max_current": max_current,
        "lower_percentage": lower_percentage,
        "upper_percentage": upper_percentage,
        "low_current": low_current,
        "high_current": high_current,
        "duty_cycle": duty_cycle,
        "frequency": frequency,
        "high_time": high_time,
        "low_time": low_time,
        "duration": duration
    }

    print("\nLoad configuration")
    print(f"Low current  : {low_current:.3f} A")
    print(f"High current : {high_current:.3f} A")
    print(f"Frequency    : {frequency} Hz")
    print(f"Duty cycle   : {duty_cycle} %")
    print(f"Duration     : {duration} s")

    return config

def configure(load, config):

    low_current = config["low_current"]
    high_current = config["high_current"]
    high_time = config["high_time"]
    low_time = config["low_time"]

    print("\nConfiguring Keithley 2380...")

    load.write("*RST")
    time.sleep(0.5)

    load.write("SYST:REM")
    time.sleep(0.2)

    load.write("FUNC CURR")
    time.sleep(0.2)

    load.write("INP OFF")

    load.write(f"CURR:RANG {high_current}")

    load.write(f"CURR:TRAN:ALEV {low_current}")
    load.write(f"CURR:TRAN:BLEV {high_current}")

    load.write(f"CURR:TRAN:AWID {low_time}")
    load.write(f"CURR:TRAN:BWID {high_time}")

    load.write("CURR:TRAN:MODE CONT")

    load.write("*WAI")

    try:
        err = load.query("SYST:ERR?")
        print("Load Status :", err.strip())
    except Exception:
        print("Unable to read load status.")

    print("Electronic load configured and waiting for trigger.")


def run(load, config):
    load.write("TRAN ON")
    load.write("INP ON")
    load.write("TRIG:SOUR HOLD")
    load.write("FORC:TRIG")

    print("Load transient running")

    time.sleep(config["duration"])

    load.write("TRAN OFF")
    load.write("INP OFF")

    print("Load transient completed")
