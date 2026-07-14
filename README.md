# PDN Load Transient Test Automation

Automated load transient response testing for Power Distribution Networks (PDN) using GPIB/USB-controlled bench instruments. This framework orchestrates a Keithley 2230 power supply, a Keithley 2380 electronic load, a Keysight DSOX6004A oscilloscope, and a Keithley DMM6500 multimeter to execute repeatable transient tests and produce professional PDF reports.

## Table of Contents

- [Architecture](#architecture)
- [Supported Instruments](#supported-instruments)
- [Installation](#installation)
- [Usage](#usage)
- [Commands](#commands)
- [Test Workflow](#test-workflow)
- [Output Structure](#output-structure)
- [Report Contents](#report-contents)
- [Module Reference](#module-reference)
- [Configuration](#configuration)
- [Extending](#extending)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Architecture

The framework is organized into single-responsibility modules that each encapsulate one instrument or function:

```
PDN_test/
  main.py                 Entry point and interactive REPL
  voltage_configure.py    Keithley 2230 PSU connection and configuration
  load_configs.py         Keithley 2380 load connection, transient config, and execution
  scope_config.py         Keysight DSOX6004A scope connection, configuration, and arming
  dmm_configs.py          Keithley DMM6500 DMM connection and configuration
  logger.py               Waveform save, CSV export, and statistics computation
  report.py               PDF report generation with matplotlib waveform plot
  captures/               Output directory for test artifacts (auto-created)
```

### Data Flow

```
User input (REPL)
     |
     v
  main.py  ──►  load_configs.create()          Interactive transient parameters
     |            |
     |            v
     |         load_configs.configure()         Program electronic load
     |
     |──►  scope_config.configure()             Configure oscilloscope (once)
     |──►  scope_config.arm()                   Arm single-shot acquisition
     |
     |──►  dmm_configs.configure()              Configure DMM (once)
     |
     |──►  load_configs.run()                   Start load transient
     |            |
     |            v
     |         logger.save_waveform()            Download waveform → .npz
     |            |
     |            v
     |         logger.export_csv()               Compute stats → .csv
     |            |
     |            v
     |         report.generate_report()          Plot + tables → .pdf
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

Each module auto-discovers its instrument by scanning the VISA resource list and matching against a model identifier or VID/PID pair. Instruments can be connected in any order and are only initialized on first use.

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

### Dependencies

```
pyvisa
numpy
matplotlib
reportlab
```

Install with:

```bash
pip install pyvisa numpy matplotlib reportlab
```

## Usage

```bash
python main.py
```

The framework starts with a connection banner and an interactive prompt:

```
PDN Load Transient Test
-----------------------
Commands:
 run
 local
 C=<current>
 exit
```

All instruments are auto-discovered on first use. The REPL accepts commands case-insensitively.

## REPL Commands

The framework exposes four commands in the interactive `> ` prompt:

### `run`

Execute a complete load transient test.

Internally this calls `load_configs.create()`, which interactively prompts for:

| Prompt | Variable | Example |
|--------|----------|---------|
| Maximum current rating (A) | `max_current` | 3.0 |
| Lower load threshold (%) | `low_current` as % of max | 10 |
| Upper load threshold (%) | `high_current` as % of max | 90 |
| Duty cycle (%) | `duty_cycle` | 50 |
| Transient frequency (Hz) | `frequency` | 1000 |
| Test duration (s) | `duration` | 5 |

After collecting parameters, `run` sequences through:

1. Connect instruments (first run only) — scope, DMM, load
2. Configure scope and DMM (first run only)
3. Configure load with transient parameters
4. Arm oscilloscope single-shot
5. Wait for ENTER to start transient
6. Start load transient with elapsed-time progress bar
7. Download waveform from scope → `.npz`
8. Compute statistics and export → `.csv`
9. Generate PDF report → `.pdf`
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

Set the power supply current limit to `<value>` amps. Value must be between 0 and 5.

```
> C=1.5
Current limit set to 1.50 A
> C=abc
Invalid current command.
> C=10
Current must be between 0 and 5 A
```

### `local`

Return the power supply to local (front-panel) control mode.

```
> local
PSU returned to local mode.
```

### `exit`

Gracefully disconnect all instruments (scope, load, DMM, PSU, VISA resource manager) and exit the program.

## Test Workflow

A typical test session follows this sequence:

```
1. Start framework              python main.py
2. (Optional) Adjust current    C=2.0
3. Run test                     run
4. Enter transient parameters   Interactive prompts
5. Press ENTER to start         Transient executes
6. Review results               Statistics printed, files saved
7. Repeat steps 3-6 or exit     exit
```

### Transient Parameter Prompts

During `run`, the framework interactively collects:

| Parameter | Description | Example |
|-----------|-------------|---------|
| Maximum current rating | Full-scale current of the DUT | 3.0 A |
| Lower load threshold | Low-side load as % of max | 10 % |
| Upper load threshold | High-side load as % of max | 90 % |
| Duty cycle | High-current duty cycle | 50 % |
| Transient frequency | Load switching frequency | 1000 Hz |
| Test duration | Total transient runtime | 5 s |

All inputs are validated before execution. Derived values (low current, high current, period, high/low times) are computed and displayed.

## Output Structure

Each `run` creates a timestamped set of files:

```
captures/
  20260714_213502/
    waveform.npz     Raw waveform data (time, voltage, channel metadata)
    waveform.csv     Human-readable export with header and statistics
    report.pdf       Auto-generated PDF report
```

The timestamp format is `YYYYMMDD_HHMMSS`, ensuring chronological sorting. A new directory is created per run to keep artifacts organized.

### File Formats

**NPZ** — NumPy compressed archive containing:
- `time` — time axis array (s)
- `voltage` — voltage samples array (V)
- `channel` — oscilloscope channel identifier
- `x_increment`, `x_origin`, `x_reference` — horizontal scaling parameters
- `y_increment`, `y_origin`, `y_reference` — vertical scaling parameters

**CSV** — Comma-separated file containing:
- Header with timestamp, channel, and acquisition parameters
- Full sample table (index, time, voltage)
- Summary statistics (duration, min, max, peak-to-peak, mean, RMS, std dev)

**PDF** — Professional report (see [Report Contents](#report-contents))

## Report Contents

The generated PDF report includes:

1. **Title** — PDN Load Transient Test Report with generation timestamp
2. **Test Information** — Waveform file, channel, samples, duration, sampling interval, voltage resolution, nominal voltage, tolerance
3. **Test Instruments** — Inventory of all connected instruments with model numbers
4. **Load Transient Configuration** — Low/high current, duty cycle, frequency, duration
5. **Measurement Results** — Statistical summary with optional DMM reading and PASS/FAIL result
6. **Captured Waveform** — Oscilloscope-style plot with:
   - Measured voltage trace
   - Nominal voltage reference line (green)
   - Upper/lower tolerance limits (red dashed)
   - Grid with major and minor tick lines
7. **Remarks** — Contextual commentary based on test result
8. **Overall Result** — Highlighted FINAL RESULT cell (green for PASS, red for FAIL)

The waveform plot is rendered at 300 DPI and embedded at full page width. Temporary plot files are automatically cleaned up after PDF generation.

## Module Reference

### `main.py`

Entry point wrapping a `main()` function guarded by `if __name__ == "__main__"`. Implements the interactive REPL with commands for running tests, adjusting current, and exiting. Manages instrument lifecycle and orchestrates the test sequence.

Key behaviors:
- Instruments are lazily connected on first `run`
- Oscilloscope and DMM are configured only once
- Electronic load is reconfigured every run (parameters change each test)
- Each instrument is individually closed in `finally`, wrapped in try/except
- ResourceManager is closed last, also in try/except
- Ctrl+C is caught cleanly with an "Interrupted by user." message

### `voltage_configure.py`

Connects to a Keithley 2230-30-1 using USB VID/PID matching. Configures the selected channel (default CH3) with:
- 5.0 V output
- 1.0 A current limit
- Output enabled via `OUTP ON`

Exposes `CHANNEL` as an importable constant used by `main.py` for live current adjustment.

### `load_configs.py`

Connects to a Keithley 2380 series load using *IDN string matching. Provides three functions:

- `create()` — Interactive parameter collection with validation
- `configure(load, config)` — Programs the transient waveform (levels, widths, mode, trigger)
- `run(load, config)` — Starts the transient, monitors elapsed time, handles interruption

Transient mode uses `CONT` (continuous) with `SOUR HOLD` trigger, started via `FORC:TRIG`. Runs in a polling loop with progress display.

### `scope_config.py`

Connects to a Keysight DSOX6004A using *IDN matching. Provides:

- `configure(scope)` — Resets, stops, sets up CHAN1 (DC coupled, 10x probe, 500 mV/div, 0 V offset, 1 ms/div timebase, 100k points, edge trigger at 3.2 V positive slope)
- `arm(scope)` — Arms single-shot acquisition and waits for trigger readiness

### `dmm_configs.py`

Connects to a Keithley DMM6500 using *IDN matching. Configures for DC voltage measurement with auto-ranging and 1 PLC integration.

### `logger.py`

Two functions:

- `save_waveform(scope, channel, filename)` — Downloads waveform data from the oscilloscope, saves as NPZ archive
- `export_csv(npz_file, csv_file)` — Loads NPZ data, computes statistics (min, max, peak-to-peak, mean, RMS, std dev), writes CSV with header, sample table, and summary. Returns the `stats` dictionary.

### `report.py`

Generates a professional PDF report using ReportLab. Flow:

1. Creates output directory if needed
2. Generates a matplotlib waveform plot with optional nominal/tolerance overlays
3. Builds a PDF document with sequential sections:
   - Title and timestamp
   - Test Information table
   - Test Instruments table
   - Load Transient Configuration table
   - Measurement Results table (dynamic row count)
   - Captured Waveform image (page-width, centered)
   - Remarks (contextual to PASS/FAIL)
   - Overall Result (highlighted FINAL RESULT)
   - Footer separator and End of Report
4. Sets PDF metadata (title, author, subject)
5. Cleans up the temporary PNG file even if PDF generation fails

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

The nominal voltage and tolerance are currently hardcoded in `main.py`:

```python
generate_report(
    npz_file, stats, config, pdf_file,
    nominal_voltage=3.3,    # Nominal rail voltage (V)
    tolerance=5.0,          # Tolerance (%)
)
```

Adjust these values or make them user-configurable through input prompts.

### Instrument Identifiers

Each instrument module contains a `MODEL` or `VENDOR_ID`/`PRODUCT_ID` constant used for auto-discovery. Update these if your instrument has a different *IDN string or USB identifiers.

## Extending

### Adding a New Instrument

1. Create a new module (e.g., `new_instrument.py`)
2. Implement `connect(rm)` that scans VISA resources and returns a connection
3. Implement `configure(instrument)` to set up the instrument
4. Import and call from `main.py`

### Adding a New Test Type

The framework can be extended beyond load transient testing:

- **Ripple measurement** — Configure scope for AC coupling, measure noise amplitude
- **Turn-on/turn-off profiling** — Trigger on power supply ramp, capture startup waveform
- **Load regulation sweep** — Iterate over multiple load currents, capture steady-state voltage

Each new test type can reuse the existing `logger.py` and `report.py` modules.

### Capturing Additional Channels

Change `SCOPE_CHANNEL` in `main.py` or make it configurable:

```python
save_waveform(scope, channel="CHAN2", filename=npz_file)
```

## Troubleshooting

### "Resource not found" errors

```
RuntimeError: Keithley 2230 not found
```

- Verify the instrument is powered on and connected
- Run `python -m pyvisa info` to list available VISA backends and resources
- Check that the VID/PID or *IDN string in the module matches your instrument
- For USB devices, ensure the kernel driver is detached (e.g., `usbip` or `pyvisa-py`)

### VISA timeout errors

```
pyvisa.errors.VisaIOError: VI_ERROR_TMO (Timeout expired)
```

- Increase `timeout` in the connect function
- Verify the instrument is responding to *IDN? queries
- Check USB/GPIB cable connections
- Ensure no other application has the instrument open

### Oscilloscope not triggering

- Verify the trigger level (`:TRIG:LEV`) is within the signal range
- Check that the probe is connected to CHAN1 and the signal is present
- Increase the trigger source voltage or adjust the vertical scale

### PDF generation fails

- Ensure `reportlab` and `matplotlib` are installed
- Verify the output directory is writable
- Check that `npz_file` contains valid waveform data

## References

- [sgoadhouse/oscope-scpi](https://github.com/sgoadhouse/oscope-scpi) — SCPI waveform acquisition from Keysight oscilloscopes
- [samdejong86/Keithley-2220-30-1-Control](https://github.com/samdejong86/Keithley-2220-30-1-Control) — Keithley 2220-30-1 power supply control in Python
- [kelvinxuande/keithley-opensource](https://github.com/kelvinxuande/keithley-opensource) — Open-source Keithley instrument automation
- [kasper64/py-DMM6500](https://github.com/kasper64/py-DMM6500) — Python driver for the Keithley DMM6500


