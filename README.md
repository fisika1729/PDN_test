# PDN Load Transient Test Automation

Load transient response testing for Power Distribution Networks (PDN) using GPIB/USB-controlled bench instruments. Orchestrates a Keithley 2230 power supply, Keithley 2380 electronic load, Keysight DSOX6004A oscilloscope, and Keithley DMM6500 multimeter to execute repeatable transient tests and produce PDF reports.

## Table of Contents

- [Architecture](#architecture)
- [Supported Instruments](#supported-instruments)
- [Installation](#installation)
- [Usage](#usage)
- [Commands](#commands)
- [Output Structure](#output-structure)
- [Report Contents](#report-contents)
- [Module Reference](#module-reference)
- [Configuration](#configuration)
- [Extending](#extending)
- [Troubleshooting](#troubleshooting)
- [References](#references)

## Architecture

Single-responsibility modules, one per instrument:

```
PDN_test/
  main.py                 Entry point and interactive REPL
  voltage_configure.py    Keithley 2230 PSU connection and configuration
  load_configs.py         Keithley 2380 load connection, transient config, and execution
  scope_config.py         Keysight DSOX6004A scope connection, configuration, and arming
  dmm_configs.py          Keithley DMM6500 DMM connection and configuration
  logger.py               Waveform save, CSV export, and statistics
  report.py               PDF report generation with matplotlib waveform plot
  captures/               Output directory for test artifacts (auto-created)
```

### Data Flow

```
User input (REPL)
     |
     v
  main.py  ->  load_configs.create()          Interactive transient parameters
     |            |
     |            v
     |         load_configs.configure()         Program electronic load
     |
     |->  scope_config.configure()             Configure oscilloscope (once)
     |->  scope_config.arm()                   Arm single-shot acquisition
     |
     |->  dmm_configs.configure()              Configure DMM (once)
     |
     |->  load_configs.run()                   Start load transient
     |            |
     |            v
     |         logger.save_waveform()            Download waveform -> .npz
     |            |
     |            v
     |         logger.export_csv()               Compute stats -> .csv
     |            |
     |            v
     |         report.generate_report()          Plot + tables -> .pdf
     |
     v
  captures/{timestamp}/
      waveform.npz     Raw oscilloscope data (NumPy archive)
      waveform.csv     Metadata + time-voltage samples + statistics
      report.pdf       Professional PDF report
```

## Supported Instruments

| Instrument | Model | Module | Connection |
|------------|-------|--------|------------|
| Power Supply | Keithley 2230-30-1 | `voltage_configure.py` | USB (VID 0x05E6 / PID 0x2230) |
| Electronic Load | Keithley 2380 Series | `load_configs.py` | GPIB/USB (*IDN match "2380") |
| Oscilloscope | Keysight DSOX6004A | `scope_config.py` | GPIB/USB (*IDN match "DSOX6004A") |
| Digital Multimeter | Keithley DMM6500 | `dmm_configs.py` | GPIB/USB (*IDN match "DMM6500") |

Each module auto-discovers its instrument by scanning the VISA resource list and matching a model identifier or VID/PID pair. Instruments connect on first use, in any order.

## Installation

### Prerequisites

- Python 3.8+
- [NI-VISA](https://www.ni.com/en/support/downloads/drivers/download.ni-visa.html) or [pyvisa-py](https://pyvisa.readthedocs.io/en/latest/backends/pyvisa-py.html) backend
- USB/GPIB drivers for your instrument adapter

### Setup

```bash
git clone <repo-url> PDN_test
cd PDN_test
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

Starts a connection banner and interactive prompt:

```
PDN Load Transient Test
-----------------------
Commands:
 run
 local
 C=<current>
 exit
```

Commands are case-insensitive.

## Commands

### `run`

Execute a load transient test. Prompts for parameters, configures instruments, runs the transient, saves waveform data, and generates a report.

Parameters collected by `load_configs.create()`:

| Prompt | Variable | Example |
|--------|----------|---------|
| Maximum current rating (A) | `max_current` | 3.0 |
| Lower load threshold (%) | `low_current` as % of max | 10 |
| Upper load threshold (%) | `high_current` as % of max | 90 |
| Duty cycle (%) | `duty_cycle` | 50 |
| Transient frequency (Hz) | `frequency` | 1000 |
| Test duration (s) | `duration` | 5 |

Sequence:

1. Connect instruments (first run only): scope, DMM, load
2. Configure scope and DMM (first run only)
3. Configure load with transient parameters
4. Arm oscilloscope single-shot
5. Wait for ENTER to start transient
6. Start load transient with elapsed-time progress bar
7. Download waveform from scope -> `.npz`
8. Compute statistics and export -> `.csv`
9. Generate PDF report -> `.pdf`
10. Print file paths and waveform statistics

```
> run

Load transient configuration
Maximum current rating (A): 3.0
Lower load threshold (%): 10
Upper load threshold (%): 90
...
```

### `C=<value>`

Set the power supply current limit to `<value>` amps (0-5).

```
> C=1.5
Current limit set to 1.50 A
> C=abc
Invalid current command.
> C=10
Current must be between 0 and 5 A
```

### `local`

Return the power supply to front-panel control mode.

```
> local
PSU returned to local mode.
```

### `exit`

Disconnect all instruments and exit.

## Output Structure

Each `run` creates timestamped files in a directory:

```
captures/
  20260714_213502/
    waveform.npz     Raw waveform data (time, voltage, channel metadata)
    waveform.csv     Human-readable export with header and statistics
    report.pdf       Auto-generated PDF report
```

Timestamp format: `YYYYMMDD_HHMMSS`.

### File Formats

**NPZ** - NumPy compressed archive with `time`, `voltage`, `channel`, and scaling parameters.

**CSV** - Header with timestamp, channel, acquisition parameters, full sample table, and summary statistics.

**PDF** - Professional report (see below).

## Report Contents

1. **Title** - PDN Load Transient Test Report with generation timestamp
2. **Test Information** - Waveform file, channel, samples, duration, sampling interval, voltage resolution, nominal voltage, tolerance
3. **Test Instruments** - Inventory of connected instruments with model numbers
4. **Load Transient Configuration** - Low/high current, duty cycle, frequency, duration
5. **Measurement Results** - Statistical summary with optional DMM reading and PASS/FAIL result
6. **Captured Waveform** - Oscilloscope-style plot with measured trace, nominal voltage line (green), tolerance limits (red dashed), major/minor grid
7. **Remarks** - Contextual commentary based on test result
8. **Overall Result** - Highlighted FINAL RESULT cell (green for PASS, red for FAIL)

Waveform plot rendered at 300 DPI, full page width. Temporary plot files cleaned up after PDF generation.

## Module Reference

### `main.py`

Entry point with `main()` guarded by `if __name__ == "__main__"`. Implements the REPL, manages instrument lifecycle, orchestrates the test sequence.

- Instruments connect lazily on first `run`
- Oscilloscope and DMM configure once
- Electronic load reconfigured every run
- Each instrument individually closed in `finally` with try/except
- Ctrl+C prints "Interrupted by user."

### `voltage_configure.py`

Connects to Keithley 2230-30-1 via USB VID/PID. Configures channel 3 with 5.0 V, 1.0 A limit, output enabled. Exposes `CHANNEL` for live current adjustment.

### `load_configs.py`

Connects to Keithley 2380 via *IDN. Three functions:
- `create()` - Interactive parameter collection with validation
- `configure(load, config)` - Programs transient waveform (levels, widths, mode, trigger)
- `run(load, config)` - Starts transient, monitors elapsed time, handles interruption

Transient mode: `CONT` with `SOUR HOLD` trigger, started via `FORC:TRIG`.

### `scope_config.py`

Connects to Keysight DSOX6004A via *IDN.
- `configure(scope)` - Resets, stops, sets up CHAN1 (DC coupled, 10x probe, 500 mV/div, 1 ms/div, 100k points, edge trigger)
- `arm(scope)` - Arms single-shot acquisition

### `dmm_configs.py`

Connects to Keithley DMM6500 via *IDN. Configures for DC voltage with auto-ranging, 1 PLC.

### `logger.py`

- `save_waveform(scope, channel, filename)` - Downloads waveform, saves as NPZ
- `export_csv(npz_file, csv_file)` - Loads NPZ, computes statistics, writes CSV, returns stats dict

### `report.py`

Generates PDF with ReportLab. Creates output directory, plots waveform with matplotlib (optional nominal/tolerance lines), builds PDF sections: title, test info, instruments, transient config, measurement results, waveform image, remarks, overall result, footer. Sets PDF metadata. Cleans up temporary PNG.

## Configuration

### Power Supply

Edit `voltage_configure.py`:

```python
CHANNEL = 3           # Output channel (1-3)
VOLTAGE = 5.0         # Output voltage (V)
CURRENT_LIMIT = 1.0   # Current limit (A)
VENDOR_ID = 0x05E6    # USB vendor ID
PRODUCT_ID = 0x2230   # USB product ID
```

### Oscilloscope

Edit `scope_config.py` to adjust acquisition parameters:

```python
scope.write(":CHAN1:SCAL 500E-3")    # Vertical scale (V/div)
scope.write(":TIM:SCAL 1E-3")        # Timebase (s/div)
scope.write(":ACQ:POIN 100000")      # Acquisition points
scope.write(":TRIG:LEV 3.2")         # Trigger level (V)
```

### Report Parameters

Hardcoded in `main.py`:

```python
generate_report(
    npz_file, stats, config, pdf_file,
    nominal_voltage=3.3,    # Nominal rail voltage (V)
    tolerance=5.0,          # Tolerance (%)
)
```

### Instrument Identifiers

Each module has a `MODEL` or `VENDOR_ID`/`PRODUCT_ID` constant for auto-discovery. Update these if your instrument uses a different *IDN string or USB identifiers.

## Extending

### Adding a New Instrument

1. Create a new module
2. Implement `connect(rm)` that scans VISA resources
3. Implement `configure(instrument)`
4. Import and call from `main.py`

### Adding a New Test Type

- **Ripple measurement** - Scope AC coupling, measure noise amplitude
- **Turn-on/turn-off profiling** - Trigger on power supply ramp
- **Load regulation sweep** - Iterate over load currents

Reuse `logger.py` and `report.py`.

### Capturing Additional Channels

```python
save_waveform(scope, channel="CHAN2", filename=npz_file)
```

## Troubleshooting

### "Resource not found"

```
RuntimeError: Keithley 2230 not found
```

- Verify instrument is powered and connected
- Run `python -m pyvisa info` to list available resources
- Check that the VID/PID or *IDN string matches your instrument
- For USB devices, detach the kernel driver (e.g., `usbip` or `pyvisa-py`)

### VISA timeout

```
pyvisa.errors.VisaIOError: VI_ERROR_TMO (Timeout expired)
```

- Increase `timeout` in the connect function
- Verify instrument responds to *IDN? queries
- Check USB/GPIB cable connections
- Close other applications using the instrument

### Oscilloscope not triggering

- Verify trigger level is within the signal range
- Check probe is connected to CHAN1 and signal is present
- Adjust vertical scale or trigger level

### PDF generation fails

- Ensure `reportlab` and `matplotlib` are installed
- Verify the output directory is writable
- Check `npz_file` contains valid waveform data

## References

- [sgoadhouse/oscope-scpi](https://github.com/sgoadhouse/oscope-scpi) - SCPI waveform acquisition from Keysight oscilloscopes
- [samdejong86/Keithley-2220-30-1-Control](https://github.com/samdejong86/Keithley-2220-30-1-Control) - Keithley 2220-30-1 power supply control in Python
- [kelvinxuande/keithley-opensource](https://github.com/kelvinxuande/keithley-opensource) - Open-source Keithley instrument automation
- [kasper64/py-DMM6500](https://github.com/kasper64/py-DMM6500) - Python driver for the Keithley DMM6500
