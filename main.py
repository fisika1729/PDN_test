#!/usr/bin/env python3

import os
from datetime import datetime

import pyvisa

from voltage_configure import connect as connect_psu
from voltage_configure import configure as configure_psu, CHANNEL

from load_configs import connect as connect_load
from load_configs import create
from load_configs import configure as configure_load
from load_configs import run

from scope_config import connect as connect_scope
from scope_config import configure as configure_scope
from scope_config import arm

from dmm_configs import connect as connect_dmm
from dmm_configs import configure as configure_dmm

from logger import save_waveform
from logger import export_csv
from report import generate_report


def main():

    rm = pyvisa.ResourceManager()

    psu = connect_psu(rm)
    configure_psu(psu)

    load = None
    scope = None
    dmm = None

    os.makedirs("captures", exist_ok=True)

    print("\nPDN Load Transient Test")
    print("-----------------------")
    print("Commands:")
    print(" run")
    print(" local")
    print(" C=<current>")
    print(" exit\n")

    try:

        while True:

            cmd = input("> ").strip()

            if cmd.lower() == "run":

                if load is None:
                    load = connect_load(rm)

                if scope is None:
                    scope = connect_scope(rm)
                    configure_scope(scope)

                if dmm is None:
                    dmm = connect_dmm(rm)
                    configure_dmm(dmm)

                config = create()

                configure_load(load, config)

                arm(scope)

                input("\nPress ENTER to start transient...")

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                base = f"captures/{timestamp}"
                npz_file = f"{base}.npz"
                csv_file = f"{base}.csv"
                pdf_file = f"{base}.pdf"

                run(load, config)

                save_waveform(
                    scope,
                    channel="CHAN1",
                    filename=npz_file
                )

                stats = export_csv(
                    npz_file,
                    csv_file
                )

                print("\nWaveform Statistics")
                print("-" * 40)
                print(f"Samples       : {stats['samples']}")
                print(f"Duration      : {stats['duration']*1000:.3f} ms")
                print(f"Minimum       : {stats['minimum']:.6f} V")
                print(f"Maximum       : {stats['maximum']:.6f} V")
                print(f"Peak-to-Peak  : {stats['peak_to_peak']:.6f} V")
                print(f"Mean          : {stats['mean']:.6f} V")
                print(f"RMS           : {stats['rms']:.6f} V")
                print(f"Std Dev       : {stats['std_dev']:.6f} V")

                generate_report(
                    npz_file,
                    stats,
                    config,
                    pdf_file,
                    nominal_voltage=3.3,
                    tolerance=5.0,
                )

                print(f"\nWaveform : {npz_file}")
                print(f"CSV      : {csv_file}")
                print(f"PDF      : {pdf_file}")
                print(f"Samples  : {stats['samples']}")

                print("\nTest completed.\n")
                print("Ready for next command.")

            elif cmd.upper().startswith("C="):

                try:
                    current = float(cmd.split("=", 1)[1])
                except (ValueError, IndexError):
                    print("Invalid current command.")
                    continue

                if not (0 <= current <= 5):
                    print("Current must be between 0 and 5 A")
                    continue

                psu.write("SYSTEM:REMOTE")
                psu.write(f"INST:NSEL {CHANNEL}")
                psu.write(f"CURR {current}")

                print(f"Current limit set to {current:.2f} A")

            elif cmd.lower() == "local":

                psu.write("SYSTEM:LOCAL")
                print("PSU returned to local mode.")

            elif cmd.lower() == "exit":

                break

            else:

                print("Unknown command.")

    except KeyboardInterrupt:
        print("\nInterrupted by user.")

    finally:

        try:
            if scope:
                scope.close()
        except Exception:
            pass

        try:
            if load:
                load.close()
        except Exception:
            pass

        try:
            if dmm:
                dmm.close()
        except Exception:
            pass

        try:
            if psu:
                psu.close()
        except Exception:
            pass

        try:
            rm.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
