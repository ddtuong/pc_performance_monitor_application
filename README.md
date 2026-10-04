# PC Performance Monitor

A modular desktop system monitor built with **Python 3.11+ and Tkinter/ttk**, targeting **Windows 10/11**
(CPU, memory, disk, network, processes and system info also run on Linux). Real values only: when a metric
cannot be read it is shown as `N/A` and the reason is logged. Nothing is ever faked.

## Features
- **Dashboard** – CPU, RAM, GPU, Disk, Network and Temperature cards plus live charts.
- **CPU** (most detailed page) – name, vendor, architecture, **physical cores vs logical processors**
  (shown separately), overall usage, per-logical-processor usage, current/base/max frequency, temperature,
  package temperature, power, load average, four history charts, a dynamically generated grid of
  per-processor tiles (works for 4…64+ logical processors) and a physical-core → logical-processor tree.
- **Memory** – total/used/available/free/cached, usage bar, swap/page file, history.
- **GPU** – provider abstraction: NVIDIA via NVML, AMD/Intel via LibreHardwareMonitor sensors, plus
  registry-based adapter names/VRAM on Windows. "GPU information unavailable" if nothing is found.
- **Disk** – volumes (capacity/used/free), per-disk read/write speed and IOPS (computed from counter deltas),
  storage temperatures when a sensor provider exists.
- **Network** – per-interface speed (delta based), totals, IPv4/IPv6/MAC, packets, errors, drops.
- **Processes** – Task-Manager-style table: search, sort (combobox or column header), refresh, diff-based updates.
- **System** – OS, build, host, manufacturer/model/BIOS, uptime, collector health, every detected sensor.
- **Settings** – interval (100 ms–5 s), chart history, theme (live switch), °C/°F, start with Windows,
  start minimized, logging, visible dashboard metrics, configurable colour thresholds.

## Architecture
```
Tkinter UI (pages, widgets)           <- main thread only
        ^  root.after(50 ms): MonitoringService.poll()
   queue.Queue(maxsize=2)  (UI always gets the newest snapshot)
        ^
 MonitoringService  -- ONE long-running worker thread, interval + wake-up Event
        |
 MonitorManager     -- runs collectors, isolates failures, builds SystemSnapshot
        |
 Collectors (cpu, memory, gpu, disk, network, sensors, system, processes)  -> psutil / NVML / WMI / registry
        |
 Models (dataclasses)  ->  HardwareService (bounded history deques) -> charts
```
Rules enforced by the layout: collectors never import Tkinter; the UI never calls psutil; widgets are created
once and updated in place; history is bounded (`deque(maxlen=…)`, hard cap 600 points).

```
pc_performance_monitor/
├── app.py                  entry point
├── config/                 constants.py (fixed), settings.py (typed, persisted JSON, change notification)
├── core/                   application.py (wiring), monitor_manager.py, monitoring_service.py, exceptions.py
├── collectors/             one module per hardware area + cpu_topology.py; base.py is the contract
├── models/                 dataclasses: CPUInfo, MemoryInfo, GPUInfo, DiskInfo, NetworkInfo, ..., SystemSnapshot
├── services/               hardware_service.py (history), process_service.py (filter/sort)
├── ui/                     main_window.py, pages/, widgets/, styles/theme.py
├── utils/                  formatters, converters, rates (delta speeds), levels, scale, logger, platform_utils
├── tests/                  pytest suite (hardware mocked; no specific CPU/GPU needed)
└── logs/                   app.log (rotating)
```

## Installation
```bash
python -m venv .venv
.venv\Scripts\activate            # Windows   (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt   # psutil is required, the rest are optional
```
Tkinter ships with the python.org Windows installer (tick "tcl/tk and IDLE").

## Running
```bash
python app.py
```

## Configuration
Settings are edited on the **Settings** page and stored in `%APPDATA%\PCPerformanceMonitor\settings.json`.
Fixed values (history cap, process refresh floor, queue size) live in `config/constants.py`.

## Supported metrics and where they come from
| Metric | Source | Notes |
|---|---|---|
| CPU usage / per-processor usage | `psutil.cpu_percent` | first reading is primed so it is meaningful |
| CPU name, vendor, base clock | Windows registry (`CentralProcessor\0`) | no subprocess needed |
| Max / current frequency | `psutil.cpu_freq` | |
| Physical-core mapping | `GetLogicalProcessorInformationEx` (Windows), sysfs (Linux) | validated, else hidden |
| Temperature, fans, power | LibreHardwareMonitor over WMI (Windows), psutil sensors (Linux) | see limitations |
| NVIDIA GPU | NVML (`nvidia-ml-py`) | usage, VRAM, temp, clocks, fan, power |
| Disk / network speed | `psutil` counters, **deltas / elapsed time** | |
| Processes | `psutil.process_iter` | CPU % normalised by logical CPU count (matches Task Manager) |

## Windows limitations
- **No built-in temperature/fan/power API.** Windows exposes no CPU/SSD sensors to user-mode Python.
  Run **LibreHardwareMonitor** (as administrator) and `pip install wmi pywin32`; the app then reads its WMI
  namespace. Without it those fields show `N/A`.
- **Per-logical-processor frequency** is not exposed by `psutil` on Windows. Tiles then omit it (stated on the page).
- **Cached memory** is not reported on Windows.
- **AMD/Intel GPU** live metrics need LibreHardwareMonitor; without it only name/VRAM size are shown.
- **Disk I/O counters** may require `diskperf -y` on old installs.
- **>64 logical processors** (multiple processor groups): topology mapping is deliberately disabled instead of guessed.
- Base clock comes from the registry's nominal `~MHz`; hybrid CPUs (P/E cores) have no single base clock.
- Temperature thresholds are generic defaults, **not** hardware limits. Tune them to your CPU/GPU.

## Troubleshooting
- *All temperatures N/A* – start LibreHardwareMonitor, `pip install wmi pywin32`, restart the app, then check **System → Collector health / Detected sensors**.
- *GPU unavailable* – `pip install nvidia-ml-py` and update the NVIDIA driver; check `logs/app.log`.
- *Window does not start* – confirm `python -c "import tkinter"` works.
- *High CPU use of the monitor* – raise the interval in Settings; the Processes page collects only while open.

## Testing
```bash
pip install pytest
pytest
```

## Development guide
- **New metric:** add a dataclass in `models/`, a collector in `collectors/` (subclass `BaseCollector`), register it in
  `MonitorManager.create_default`, add a field to `SystemSnapshot`, then render it in a page.
- **New page:** subclass `ui.pages.base.BasePage`, implement `build()` (create widgets once) and `update_view(snapshot)`,
  and register it in `ui/main_window.py` and `config.constants.PAGES`.
- **New GPU vendor:** implement `GPUProvider.collect()` and add it to `GPUCollector`.
- Raise `CollectorError` subclasses for "whole category unavailable"; return `None` for individual missing values.

## Future improvements
Tray icon and alerts, CSV export, per-process disk/network, ETW/PDH GPU engine counters (vendor-neutral GPU usage),
SMART attributes, per-core temperatures chart, packaged `.exe` (PyInstaller).
