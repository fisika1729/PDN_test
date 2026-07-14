from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    Image,
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


def generate_report(
    npz_file,
    stats,
    load_config,
    output_pdf,
    nominal_voltage=None,
    tolerance=None,
):

    data = np.load(npz_file)

    channel = str(data["channel"])

    x_increment = float(data["x_increment"])
    y_increment = float(data["y_increment"])

    time_axis = data["time"]
    voltage = data["voltage"]

    Path(output_pdf).parent.mkdir(parents=True, exist_ok=True)

    plot_file = Path(output_pdf).with_suffix(".png")

    plt.figure(figsize=(8, 3))

    plt.plot(
        time_axis,
        voltage,
        linewidth=1,
        label="Measured Voltage",
    )

    # Draw nominal voltage and tolerance limits if supplied
    if nominal_voltage is not None:

        plt.axhline(
            nominal_voltage,
            color="green",
            linewidth=1,
            label="Nominal",
        )

        if tolerance is not None:

            upper = nominal_voltage * (1 + tolerance / 100)
            lower = nominal_voltage * (1 - tolerance / 100)

            plt.axhline(
                upper,
                color="red",
                linestyle="--",
                linewidth=1,
                label="Upper Limit",
            )

            plt.axhline(
                lower,
                color="red",
                linestyle="--",
                linewidth=1,
                label="Lower Limit",
            )

    plt.title("Captured Waveform")

    plt.xlabel("Time (s)")
    plt.ylabel("Voltage (V)")

    plt.minorticks_on()

    plt.grid(True, which="major")
    plt.grid(True, which="minor", linestyle=":")

    plt.legend(loc="best", fontsize=8)

    plt.tight_layout()

    plt.savefig(
        plot_file,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close()

    doc = SimpleDocTemplate(output_pdf)

    doc.title = "PDN Load Transient Test Report"
    doc.author = "PDN Load Transient Test Automation"
    doc.subject = "Load Transient Measurement Report"

    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph("<b>PDN Load Transient Test Report</b>", styles["Title"])
    )

    elements.append(
        Paragraph(
            f"Generated : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            styles["Normal"],
        )
    )

    elements.append(Spacer(1, 15))

    elements.append(
        Paragraph("<b>Test Information</b>", styles["Heading2"])
    )

    info = [
        ["Waveform File", npz_file],
        ["Channel", channel],
        ["Samples", stats["samples"]],
        ["Duration (ms)", f"{stats['duration'] * 1000:.3f}"],
        ["Sampling Interval (s)", f"{x_increment:.3e}"],
        ["Voltage Resolution (V)", f"{y_increment:.6f}"],
    ]

    if nominal_voltage is not None:
        info.append(
            ["Nominal Voltage (V)", f"{nominal_voltage:.3f}"]
        )

    if tolerance is not None:
        info.append(
            ["Tolerance (%)", f"±{tolerance:.1f}"]
        )

    info_table = Table(info, colWidths=[180, 250])

    info_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    elements.append(info_table)

    elements.append(Spacer(1, 20))

    elements.append(
        Paragraph("<b>Test Instruments</b>", styles["Heading2"])
    )

    instrument_data = [
        ["Power Supply", "Keithley 2230-30-1"],
        ["Electronic Load", "Keithley 2380 Series"],
        ["Oscilloscope", "Keysight DSOX6004A"],
        ["Digital Multimeter", "Keithley DMM6500"],
    ]

    instrument_table = Table(
        instrument_data,
        colWidths=[180, 250],
    )

    instrument_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    elements.append(instrument_table)

    elements.append(Spacer(1, 20))

    elements.append(
        Paragraph("<b>Load Transient Configuration</b>", styles["Heading2"])
    )

    transient = [
        ["Low Current (A)", f"{load_config['low_current']:.3f}"],
        ["High Current (A)", f"{load_config['high_current']:.3f}"],
        ["Duty Cycle (%)", f"{load_config['duty_cycle']}"],
        ["Frequency (Hz)", f"{load_config['frequency']}"],
        ["Duration (s)", f"{load_config['duration']}"],
    ]

    transient_table = Table(
        transient,
        colWidths=[180, 250],
    )

    transient_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    elements.append(transient_table)

    elements.append(Spacer(1, 20))

    elements.append(
        Paragraph("<b>Measurement Results</b>", styles["Heading2"])
    )

    result = stats.get("result", "N/A")

    results = [
        ["Minimum Voltage (V)", f"{stats['minimum']:.6f}"],
        ["Maximum Voltage (V)", f"{stats['maximum']:.6f}"],
        ["Peak-to-Peak (V)", f"{stats['peak_to_peak']:.6f}"],
        ["Mean Voltage (V)", f"{stats['mean']:.6f}"],
        ["RMS Voltage (V)", f"{stats['rms']:.6f}"],
        ["Standard Deviation (V)", f"{stats['std_dev']:.6f}"],
    ]

    if "dmm_voltage" in stats:
        results.append(
            [
                "Measured DC Voltage (V)",
                f"{stats['dmm_voltage']:.6f}",
            ]
        )

    results.append(["Result", result])

    results_table = Table(results, colWidths=[180, 250])

    style = TableStyle(
        [
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]
    )

    result_row = len(results) - 1

    if result == "PASS":
        style.add(
            "TEXTCOLOR",
            (1, result_row),
            (1, result_row),
            colors.green,
        )
        style.add(
            "FONTNAME",
            (1, result_row),
            (1, result_row),
            "Helvetica-Bold",
        )

    elif result == "FAIL":
        style.add(
            "TEXTCOLOR",
            (1, result_row),
            (1, result_row),
            colors.red,
        )
        style.add(
            "FONTNAME",
            (1, result_row),
            (1, result_row),
            "Helvetica-Bold",
        )

    results_table.setStyle(style)

    elements.append(results_table)

    elements.append(Spacer(1, 20))

    elements.append(
        Paragraph("<b>Captured Waveform</b>", styles["Heading2"])
    )

    available_width = doc.width

    waveform = Image(
        str(plot_file),
        width=available_width,
        height=available_width * 0.40,
    )

    waveform.hAlign = "CENTER"

    elements.append(waveform)

    elements.append(Spacer(1, 20))

    elements.append(
        Paragraph("<b>Remarks</b>", styles["Heading2"])
    )

    if result == "PASS":
        remarks = (
            "Measured waveform satisfies the configured acceptance criteria."
        )

    elif result == "FAIL":
        remarks = (
            "Measured waveform exceeds one or more configured acceptance limits."
        )

    else:
        remarks = (
            "Acceptance result was not available."
        )

    elements.append(
        Paragraph(
            remarks,
            styles["Normal"],
        )
    )

    elements.append(Spacer(1, 20))

    elements.append(
        Paragraph("<b>Overall Result</b>", styles["Heading2"])
    )

    summary = Table(
        [["FINAL RESULT", result]],
        colWidths=[220, 210],
    )

    summary_style = TableStyle(
        [
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("BACKGROUND", (0, 0), (0, 0), colors.lightgrey),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 14),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ]
    )

    if result == "PASS":
        summary_style.add(
            "TEXTCOLOR",
            (1, 0),
            (1, 0),
            colors.green,
        )
        summary_style.add(
            "BACKGROUND",
            (1, 0),
            (1, 0),
            colors.lightgreen,
        )

    elif result == "FAIL":
        summary_style.add(
            "TEXTCOLOR",
            (1, 0),
            (1, 0),
            colors.red,
        )
        summary_style.add(
            "BACKGROUND",
            (1, 0),
            (1, 0),
            colors.pink,
        )

    summary.setStyle(summary_style)

    elements.append(summary)

    elements.append(Spacer(1, 20))

    elements.append(
        Table(
            [[""]],
            colWidths=[430],
            style=TableStyle([
                ("LINEABOVE", (0, 0), (-1, 0), 0.5, colors.grey),
            ]),
        )
    )

    elements.append(Spacer(1, 10))

    elements.append(
        Paragraph(
            "<font size=8>End of Report</font>",
            styles["Italic"],
        )
    )

    try:
        doc.build(elements)
    finally:
        try:
            plot_file.unlink()
        except FileNotFoundError:
            pass

    print(f"Report saved to {output_pdf}")
