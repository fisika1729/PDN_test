import csv
from datetime import datetime
import numpy as np


def export_csv(npz_file, csv_file):

    data = np.load(npz_file)

    time_axis = data["time"]
    voltage = data["voltage"]

    channel = str(data["channel"])

    x_increment = float(data["x_increment"])
    x_origin = float(data["x_origin"])
    x_reference = float(data["x_reference"])

    y_increment = float(data["y_increment"])
    y_origin = float(data["y_origin"])
    y_reference = float(data["y_reference"])

    stats = {
        "samples": len(voltage),
        "duration": time_axis[-1] - time_axis[0],
        "minimum": np.min(voltage),
        "maximum": np.max(voltage),
        "peak_to_peak": np.ptp(voltage),
        "mean": np.mean(voltage),
        "rms": np.sqrt(np.mean(voltage ** 2)),
        "std_dev": np.std(voltage),
    }

    with open(csv_file, "w", newline="") as f:

        writer = csv.writer(f)

        writer.writerow(["Timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        writer.writerow(["Channel", channel])
        writer.writerow(["Samples", len(time_axis)])

        writer.writerow(["X Increment (s)", x_increment])
        writer.writerow(["X Origin", x_origin])
        writer.writerow(["X Reference", x_reference])

        writer.writerow(["Y Increment (V)", y_increment])
        writer.writerow(["Y Origin", y_origin])
        writer.writerow(["Y Reference", y_reference])

        writer.writerow([])

        writer.writerow(["Sample", "Time (s)", "Voltage (V)"])

        for i, (t, v) in enumerate(zip(time_axis, voltage)):
            writer.writerow([
                i,
                f"{t:.12e}",
                f"{v:.6f}"
            ])

        writer.writerow([])
        writer.writerow(["Waveform Statistics"])

        writer.writerow(["Duration (ms)", stats["duration"] * 1000])
        writer.writerow(["Minimum (V)", stats["minimum"]])
        writer.writerow(["Maximum (V)", stats["maximum"]])
        writer.writerow(["Peak-to-Peak (V)", stats["peak_to_peak"]])
        writer.writerow(["Mean (V)", stats["mean"]])
        writer.writerow(["RMS (V)", stats["rms"]])
        writer.writerow(["Standard Deviation (V)", stats["std_dev"]])

    print(f"CSV exported to {csv_file}")

    return stats


def save_waveform(scope, channel, filename):

    print("\nDownloading waveform...")

    scope.write(f":WAVeform:SOURce {channel}")
    scope.query("*OPC?")
    scope.write(":WAVeform:FORMat WORD")
    scope.query("*OPC?")
    scope.write(":WAVeform:BYTeorder LSBFirst")
    scope.query("*OPC?")

    preamble = scope.query(":WAVeform:PREamble?").strip().split(",")

    (
        _format, _type, points,
        x_increment, x_origin, x_reference,
        y_increment, y_origin, y_reference,
        *_rest
    ) = [float(x) for x in preamble]

    points = int(points)

    scope.query("*OPC?")

    raw = scope.query_binary_values(
        ":WAVeform:DATA?",
        datatype="h",
        is_big_endian=False,
    )

    voltage = [(v - y_reference) * y_increment + y_origin for v in raw]
    time_axis = [(i - x_reference) * x_increment + x_origin for i in range(points)]

    np.savez(
        filename,
        time=np.array(time_axis),
        voltage=np.array(voltage),
        channel=channel,
        x_increment=x_increment,
        x_origin=x_origin,
        x_reference=x_reference,
        y_increment=y_increment,
        y_origin=y_origin,
        y_reference=y_reference,
    )

    print(f"Waveform saved to {filename}")

    return {"raw": raw, "voltage": voltage, "time": time_axis}


def waveform_statistics(npz_file):

    data = np.load(npz_file)

    voltage = data["voltage"]
    time_axis = data["time"]

    stats = {
        "samples": len(voltage),
        "duration": time_axis[-1] - time_axis[0],
        "min": np.min(voltage),
        "max": np.max(voltage),
        "peak_to_peak": np.ptp(voltage),
        "mean": np.mean(voltage),
        "rms": np.sqrt(np.mean(voltage ** 2)),
        "std_dev": np.std(voltage),
    }

    print("\nWaveform Statistics")
    print("-" * 40)
    print(f"Samples       : {stats['samples']}")
    print(f"Duration      : {stats['duration']:.6e} s")
    print(f"Minimum       : {stats['min']:.6f} V")
    print(f"Maximum       : {stats['max']:.6f} V")
    print(f"Peak-to-Peak  : {stats['peak_to_peak']:.6f} V")
    print(f"Mean          : {stats['mean']:.6f} V")
    print(f"RMS           : {stats['rms']:.6f} V")
    print(f"Std Deviation : {stats['std_dev']:.6f} V")

    return stats