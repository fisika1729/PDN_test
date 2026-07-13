import pyvisa

from voltage_configure import connect as connect_psu
from voltage_configure import configure as configure_psu

from load_configs import connect as connect_load
from load_configs import create
from load_configs import configure as configure_load
from load_configs import run

from scope_config import connect as connect_scope
from scope_config import configure as configure_scope
from scope_config import arm

rm = pyvisa.ResourceManager()

psu = connect_psu(rm)
configure_psu(psu)

load = None
scope = None

while True:

    cmd = input("> ").strip()

    if cmd == "run":

        if load is None:
            load = connect_load(rm)

        if scope is None:
            scope = connect_scope(rm)

        config = create()

        configure_load(load, config)

        configure_scope(scope)

        arm(scope)

        input("Press ENTER to start transient...")

        run(load, config)

    elif cmd.upper().startswith("C="):

        current = float(cmd.split("=")[1])

        psu.write("SYSTEM:REMOTE")
        psu.write("INST:NSEL 3")
        psu.write(f"CURR {current}")

    elif cmd == "local":

        psu.write("SYSTEM:LOCAL")

    elif cmd == "exit":

        break

if scope:
    scope.close()

if load:
    load.close()

psu.close()

rm.close()