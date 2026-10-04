# Prompt — Build a Professional PC Performance Monitor with Python + Tkinter

## 1. Objective

I want to build a **professional desktop PC Performance Monitoring application using Python and Tkinter**.

The application must collect, calculate, and display detailed real-time hardware and system performance information.

The primary target platform is:

- **Windows 10 / Windows 11**
- Python 3.11+

The application should have a **modern, clean, visually appealing desktop UI** while keeping the codebase simple, modular, and easy to maintain.

Do **not** create a monolithic application such as a single `main.py` containing all business logic and UI code.

The project must be broken into clearly separated:

- folders
- modules
- classes
- functions
- data models
- collectors
- services
- UI components
- utilities
- tests

The architecture must make it easy to add new hardware metrics and new UI pages in the future.

---

# 2. Technology Stack

Use:

- **Python 3.11+**
- **Tkinter / ttk** for GUI
- `psutil` for CPU, RAM, disk, network, process, and system information
- `platform` for operating-system information
- `socket` for network/system information where appropriate
- `subprocess` only when necessary
- `logging` for application logs
- `dataclasses` for structured monitoring data
- `threading` or an appropriate background-worker architecture for hardware monitoring
- `queue` where useful for safely transferring data between worker threads and the Tkinter UI
- `collections.deque` for bounded historical data
- `pytest` for testing

For hardware-specific metrics, use appropriate libraries/APIs when available.

Possible examples:

- NVIDIA NVML / `pynvml`
- Windows WMI
- Windows performance counters
- LibreHardwareMonitor integration/API where appropriate
- SMART information for storage devices where appropriate

Do not introduce a dependency unless it provides a meaningful capability.

The initial implementation should prioritize **Windows**.

---

# 3. Main Requirements

The application should monitor:

```text
CPU
├── Overall CPU usage
├── Logical CPU count
├── Physical core count
├── Threads
├── Per-core usage
├── Per-logical-processor usage
├── Current frequency
├── Base frequency
├── Max frequency
├── Per-core frequency when available
├── CPU temperature
├── CPU package temperature
├── CPU power
├── CPU load
└── CPU model information

RAM
├── Total
├── Used
├── Available
├── Free
├── Usage %
├── Swap
└── Memory information

GPU
├── GPU name
├── GPU usage
├── VRAM usage
├── VRAM total
├── Temperature
├── Core clock
├── Memory clock
├── Fan speed
└── Power consumption

Disk
├── Disk usage
├── Read speed
├── Write speed
├── Read operations
├── Write operations
├── Capacity
├── Free space
└── Temperature / SMART information where available

Network
├── Interface
├── Download speed
├── Upload speed
├── Total received
├── Total sent
├── Packets
├── Errors
└── Dropped packets

Processes
├── PID
├── Process name
├── CPU %
├── Memory %
├── Memory usage
├── Threads
├── Status
└── Executable

System
├── OS
├── OS version
├── Windows build
├── Hostname
├── Manufacturer
├── Model
├── BIOS
├── Architecture
├── Python version
├── Boot time
└── Uptime
```

---

# 4. CPU Monitoring — Very Important

CPU monitoring is one of the most important parts of this application.

Do NOT only display:

```text
CPU: 35%
```

The application must provide detailed CPU information.

## 4.1 CPU General Information

Display:

```text
CPU Name
Manufacturer
Architecture
Physical Cores
Logical Processors
Threads
Base Frequency
Current Frequency
Maximum Frequency
CPU Usage
```

For example:

```text
Intel Core i7-10750H
Architecture: x86_64
Physical Cores: 6
Logical Processors: 12
Threads: 12
Base Frequency: 2.60 GHz
Current Frequency: 3.80 GHz
Max Frequency: 5.00 GHz
Overall Usage: 42%
```

Use correct terminology.

Do not incorrectly claim that:

```text
Physical Cores = Threads
```

Explain and display:

```text
Physical Cores
Logical Processors
```

separately.

---

# 5. Per-Core / Per-Logical-Processor Monitoring

The CPU page must provide a detailed view of individual CPU processors.

For example, if the CPU has:

```text
6 physical cores
12 logical processors
```

display:

```text
Logical Processor 0    35%
Logical Processor 1    42%
Logical Processor 2    18%
Logical Processor 3    56%
Logical Processor 4    40%
Logical Processor 5    31%
Logical Processor 6    22%
Logical Processor 7    37%
Logical Processor 8    45%
Logical Processor 9    29%
Logical Processor 10   51%
Logical Processor 11   34%
```

Use:

```python
psutil.cpu_percent(percpu=True)
```

or another appropriate API.

The UI should clearly identify:

```text
CPU 0
CPU 1
CPU 2
...
```

as logical processors.

If the system provides physical-core mapping, optionally show:

```text
Core 0
├── Thread 0
└── Thread 1

Core 1
├── Thread 0
└── Thread 1
```

Do not assume that every CPU exposes the same topology information.

---

# 6. CPU Core Visualization

Create a visually attractive CPU core monitoring section.

For example:

```text
CPU CORES

┌────────────┐ ┌────────────┐ ┌────────────┐
│ CPU 0      │ │ CPU 1      │ │ CPU 2      │
│            │ │            │ │            │
│    32%     │ │    71%     │ │    45%     │
│            │ │            │ │            │
│  3.80 GHz  │ │  4.10 GHz  │ │  3.60 GHz  │
└────────────┘ └────────────┘ └────────────┘

┌────────────┐ ┌────────────┐ ┌────────────┐
│ CPU 3      │ │ CPU 4      │ │ CPU 5      │
│            │ │            │ │            │
│    20%     │ │    58%     │ │    43%     │
│            │ │            │ │            │
│  3.20 GHz  │ │  4.00 GHz  │ │  3.70 GHz  │
└────────────┘ └────────────┘ └────────────┘
```

The number of cards must be generated dynamically based on the number of logical processors.

Do NOT hardcode:

```python
CPU0
CPU1
CPU2
...
```

The UI must adapt automatically to:

```text
4 logical processors
8 logical processors
12 logical processors
16 logical processors
24 logical processors
32 logical processors
...
```

---

# 7. CPU Historical Charts

The CPU page should provide historical information.

Display charts for:

```text
Overall CPU Usage
Per-CPU Usage
CPU Frequency
CPU Temperature
```

Example:

```text
CPU Usage

100% ┤
 80% ┤                 ╭───╮
 60% ┤        ╭────────╯   ╰──╮
 40% ┤────╭───╯                ╰──
 20% ┤    │
  0% └──────────────────────────────
      60s     45s     30s     15s   Now
```

Use bounded history.

For example:

```python
deque(maxlen=300)
```

Do not allow historical data to grow indefinitely.

---

# 8. CPU Data Model

Use a typed model.

For example:

```python
from dataclasses import dataclass
from typing import Optional


@dataclass
class LogicalProcessorInfo:
    index: int
    usage_percent: float
    frequency_mhz: Optional[float]


@dataclass
class CPUInfo:
    name: str
    architecture: str
    physical_cores: int
    logical_processors: int

    usage_percent: float

    current_frequency_mhz: Optional[float]
    base_frequency_mhz: Optional[float]
    max_frequency_mhz: Optional[float]

    temperature_celsius: Optional[float]
    power_watts: Optional[float]

    logical_processors_info: list[LogicalProcessorInfo]
```

Improve the model if necessary.

Do not use random dictionaries everywhere.

---

# 9. CPU Collector

Create a dedicated:

```text
collectors/cpu.py
```

The collector should be responsible only for collecting CPU data.

Example:

```python
class CPUCollector:

    def collect(self) -> CPUInfo:
        ...
```

Potential responsibilities:

```text
get_cpu_name()
get_cpu_architecture()
get_physical_core_count()
get_logical_processor_count()
get_cpu_usage()
get_per_processor_usage()
get_cpu_frequency()
get_cpu_temperature()
get_cpu_power()
```

Do not put UI code inside the collector.

The collector must never import Tkinter.

---

# 10. RAM Monitoring

Display:

```text
Total RAM
Used RAM
Available RAM
Free RAM
Usage %
Cached RAM where available
Swap Total
Swap Used
Swap %
```

Example:

```text
Memory

31.8 GB Total

Used       10.2 GB
Available  21.6 GB
Usage      32%

Swap
Used       1.2 GB
Total      8.0 GB
```

Add a visual usage bar.

---

# 11. GPU Monitoring

GPU monitoring must use an abstraction.

Architecture:

```text
GPUCollector
    │
    ├── NVIDIA
    │
    ├── AMD
    │
    └── Intel
```

Display when available:

```text
GPU Name
GPU Usage
VRAM Usage
VRAM Total
Temperature
GPU Clock
Memory Clock
Fan Speed
Power Consumption
```

If GPU information is unavailable:

```text
GPU information unavailable
```

Do not fake GPU values.

---

# 12. Disk Monitoring

Display:

```text
Disk
├── Device
├── Mount Point
├── Total Capacity
├── Used
├── Free
├── Usage %
├── Read Speed
├── Write Speed
├── Read Operations
├── Write Operations
└── Temperature where available
```

Calculate speed using deltas.

Example:

```python
read_speed = (
    current_read_bytes - previous_read_bytes
) / elapsed_seconds
```

Do not treat cumulative byte counters as instantaneous speed.

---

# 13. Network Monitoring

Display:

```text
Network Interface
IPv4
IPv6
MAC
Download Speed
Upload Speed
Total Downloaded
Total Uploaded
Packets Sent
Packets Received
Errors
Dropped Packets
```

Calculate:

```text
Download MB/s
Upload MB/s
```

using the difference between two measurements.

Support multiple network interfaces.

---

# 14. Process Monitoring

Create a Task Manager-like process page.

Display:

```text
PID
Name
CPU %
Memory %
Memory Usage
Threads
Status
Username
Executable
```

Support:

- Sorting by CPU
- Sorting by memory
- Search
- Refresh
- Process count

The process list should be virtualized or efficiently refreshed if necessary.

Do not recreate the entire table unnecessarily on every update.

---

# 15. System Information

Display:

```text
Operating System
Windows Version
Windows Build
Hostname
Manufacturer
Model
BIOS
Architecture
Python Version
Boot Time
Uptime
```

Example:

```text
SYSTEM

Operating System    Windows 11
Build               26200
Architecture        x64
Manufacturer        ASUS
Model               TUF Gaming
BIOS                XXXXX
Uptime              3h 24m
```

---

# 16. Temperature and Sensors

Create a dedicated sensor abstraction.

Possible metrics:

```text
CPU Temperature
CPU Package Temperature
CPU Core Temperature
GPU Temperature
GPU Hotspot
SSD Temperature
Motherboard Temperature
Fan RPM
CPU Fan RPM
GPU Fan RPM
```

Hardware sensor availability differs between machines.

Therefore:

- Detect sensors dynamically.
- Do not assume sensors exist.
- Return `None` when unavailable.
- Display `N/A` in the UI.
- Log sensor/API failures.

Example:

```text
CPU Temperature: 58 °C
GPU Temperature: 61 °C
SSD Temperature: N/A
CPU Fan: 2,100 RPM
```

---

# 17. Application Architecture

Use this general architecture:

```text
┌─────────────────────────────────────────────────────────┐
│                    Tkinter UI                           │
│                                                         │
│ Dashboard │ CPU │ RAM │ GPU │ Disk │ Network │ System │
└───────────────────────────┬─────────────────────────────┘
                            │
                     UI Update Layer
                            │
                            ▼
                    Monitoring Service
                            │
                            ▼
                    Monitor Manager
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
          ▼                 ▼                 ▼
      CPUCollector      GPUCollector     MemoryCollector
          │                 │                 │
          ▼                 ▼                 ▼
       psutil            NVML/WMI        psutil/WMI
          │                 │                 │
          └─────────────────┼─────────────────┘
                            ▼
                       Data Models
                            │
                            ▼
                      Tkinter Queue
                            │
                            ▼
                        Main Thread
```

The UI must NOT directly call:

```python
psutil.cpu_percent()
psutil.virtual_memory()
psutil.disk_usage()
```

Instead:

```text
OS
 ↓
Collector
 ↓
Model
 ↓
Monitoring Service
 ↓
Queue
 ↓
Tkinter Main Thread
 ↓
Widget
```

---

# 18. Threading and Tkinter

Tkinter is not thread-safe.

Therefore:

**Never update Tkinter widgets directly from a worker thread.**

Use:

```text
Worker Thread
     │
     ▼
Monitoring Service
     │
     ▼
queue.Queue
     │
     ▼
root.after(...)
     │
     ▼
Tkinter UI
```

Example concept:

```python
monitor_queue.put(snapshot)
```

Then:

```python
root.after(
    100,
    process_monitor_queue
)
```

The UI thread reads the latest snapshot and updates widgets.

The application must remain responsive while monitoring.

---

# 19. Monitoring Interval

Allow configurable monitoring intervals:

```text
100 ms
250 ms
500 ms
1 second
2 seconds
5 seconds
```

Default:

```text
1 second
```

Do not create a new thread every interval.

Use a long-running worker or a controlled monitoring scheduler.

---

# 20. UI Design

The application should look modern despite using Tkinter.

Use:

- `ttk`
- Custom ttk styles
- Frames
- Cards
- Progress bars
- Labels
- Treeviews
- Scrollable frames
- Canvas where useful
- Custom charts if required

Avoid the appearance of an old-fashioned default Tkinter application.

The main layout should resemble a modern monitoring dashboard.

Example:

```text
┌───────────────────────────────────────────────────────────────┐
│ PC PERFORMANCE MONITOR                            ⚙ Settings │
├───────────────┬───────────────────────────────────────────────┤
│               │                                               │
│ Dashboard     │   CPU       RAM       GPU       Disk          │
│               │                                               │
│ CPU           │   42%       53%       61%       58%           │
│               │                                               │
│ Memory        │                                               │
│               │   CPU Usage History                           │
│ GPU           │   ────────────────────────────────            │
│               │                                               │
│ Disk          │   CPU Cores                                  │
│               │   ┌────┐ ┌────┐ ┌────┐ ┌────┐              │
│ Network       │   │32% │ │45% │ │61% │ │20% │              │
│               │   └────┘ └────┘ └────┘ └────┘              │
│ Processes     │                                               │
│               │                                               │
│ System        │                                               │
└───────────────┴───────────────────────────────────────────────┘
```

---

# 21. Main Navigation

Create a sidebar navigation:

```text
Dashboard
CPU
Memory
GPU
Disk
Network
Processes
System
Settings
```

The main content area changes based on the selected page.

Do not create a new application window for every page unless necessary.

Use one main window with replaceable page/frame content.

---

# 22. Dashboard

The dashboard should summarize the most important information.

Display cards for:

```text
CPU
RAM
GPU
Disk
Network
Temperature
```

Example:

```text
CPU
42%
3.8 GHz
58 °C

RAM
10.2 / 32 GB
32%

GPU
61%
4.2 / 12 GB
61 °C

Network
↓ 12.5 MB/s
↑ 2.1 MB/s
```

The dashboard should update automatically.

---

# 23. CPU Page

The CPU page should be the most detailed page.

Suggested structure:

```text
┌────────────────────────────────────────────────────────────┐
│ CPU                                                        │
├────────────────────────────────────────────────────────────┤
│ Intel Core i7-10750H                                      │
│                                                            │
│ Usage       42%       Frequency      3.8 GHz              │
│ Cores       6         Logical CPU    12                   │
│ Temp        58 °C     Power          42 W                 │
├────────────────────────────────────────────────────────────┤
│ Overall CPU Usage                                          │
│                                                            │
│                    CPU CHART                               │
│                                                            │
├────────────────────────────────────────────────────────────┤
│ Logical Processors                                         │
│                                                            │
│ CPU 0   32%   3.8 GHz                                     │
│ CPU 1   45%   3.9 GHz                                     │
│ CPU 2   61%   4.0 GHz                                     │
│ CPU 3   20%   3.2 GHz                                     │
│ ...                                                        │
└────────────────────────────────────────────────────────────┘
```

Also provide a graphical grid of processor cards.

---

# 24. CPU Core / Thread Details

If hardware topology can be determined, display:

```text
Physical Core 0
├── Logical Processor 0
└── Logical Processor 1

Physical Core 1
├── Logical Processor 2
└── Logical Processor 3

Physical Core 2
├── Logical Processor 4
└── Logical Processor 5
```

For each logical processor:

```text
Usage
Frequency
```

If topology information cannot be reliably determined, display only logical processors.

Never fabricate core/thread mapping.

---

# 25. Colors and Visual Feedback

Use color-coded performance states, but do not make the UI visually noisy.

Example concept:

```text
0–50%       Normal
50–80%      Moderate
80–95%      High
95–100%     Critical
```

Apply similar visual feedback to:

- CPU
- RAM
- GPU
- Disk
- Temperature

Temperature thresholds should be configurable and hardware-aware where possible.

Do not hardcode unsafe universal temperature thresholds without explaining that CPU/GPU limits vary by hardware.

---

# 26. Project Structure

Use a structure similar to:

```text
pc_performance_monitor/
│
├── app.py
├── README.md
├── requirements.txt
├── pyproject.toml
├── .gitignore
│
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── constants.py
│
├── core/
│   ├── __init__.py
│   ├── application.py
│   ├── monitor_manager.py
│   ├── monitoring_service.py
│   └── exceptions.py
│
├── collectors/
│   ├── __init__.py
│   ├── base.py
│   ├── cpu.py
│   ├── memory.py
│   ├── gpu.py
│   ├── disk.py
│   ├── network.py
│   ├── sensors.py
│   ├── system.py
│   └── processes.py
│
├── models/
│   ├── __init__.py
│   ├── cpu.py
│   ├── memory.py
│   ├── gpu.py
│   ├── disk.py
│   ├── network.py
│   ├── sensor.py
│   ├── system.py
│   ├── process.py
│   └── snapshot.py
│
├── services/
│   ├── __init__.py
│   ├── hardware_service.py
│   └── process_service.py
│
├── ui/
│   ├── __init__.py
│   ├── main_window.py
│   │
│   ├── pages/
│   │   ├── __init__.py
│   │   ├── dashboard_page.py
│   │   ├── cpu_page.py
│   │   ├── memory_page.py
│   │   ├── gpu_page.py
│   │   ├── disk_page.py
│   │   ├── network_page.py
│   │   ├── processes_page.py
│   │   ├── system_page.py
│   │   └── settings_page.py
│   │
│   ├── widgets/
│   │   ├── __init__.py
│   │   ├── metric_card.py
│   │   ├── progress_card.py
│   │   ├── cpu_core_card.py
│   │   ├── chart.py
│   │   ├── status_badge.py
│   │   └── sidebar.py
│   │
│   └── styles/
│       └── theme.py
│
├── utils/
│   ├── __init__.py
│   ├── formatters.py
│   ├── converters.py
│   ├── platform_utils.py
│   ├── logger.py
│   └── time_utils.py
│
├── tests/
│   ├── __init__.py
│   ├── test_cpu.py
│   ├── test_memory.py
│   ├── test_disk.py
│   ├── test_network.py
│   ├── test_formatters.py
│   └── test_monitor_manager.py
│
└── logs/
    └── .gitkeep
```

You may modify this structure if a better architecture is justified.

Do not over-engineer the project.

---

# 27. Responsibility of Each Layer

## Collectors

Responsible for:

```text
Talking to OS / hardware APIs
Collecting raw information
Converting raw information into models
```

Collectors must NOT know about Tkinter.

---

## Models

Responsible for:

```text
Representing structured monitoring data
```

Examples:

```text
CPUInfo
MemoryInfo
GPUInfo
DiskInfo
NetworkInfo
SystemInfo
ProcessInfo
SystemSnapshot
```

---

## Services

Responsible for:

```text
Business logic
Aggregation
Calculations
Monitoring orchestration
```

Examples:

```text
Calculating speed
Combining collectors
Managing snapshots
Calculating historical values
```

---

## UI

Responsible for:

```text
Displaying information
User interaction
Navigation
Charts
Visual feedback
```

The UI should not know how the hardware data is collected.

---

# 28. Utility Functions

Create reusable utility functions for:

```text
format_bytes()
format_speed()
format_frequency()
format_duration()
format_temperature()
format_percentage()
```

Examples:

```text
1024 → 1 KB
1048576 → 1 MB
1073741824 → 1 GB
```

And:

```text
3800 MHz → 3.80 GHz
```

Keep formatting logic outside the UI widgets.

---

# 29. Error Handling

The application must never crash just because one metric is unavailable.

For example:

```text
CPU          ✓
Memory       ✓
GPU          ✓
Disk         ✓
Network      ✓
Temperature  ✗
```

The UI should continue working.

Possible states:

```text
Available
Unavailable
Not supported
Permission denied
Hardware not detected
API unavailable
```

Log the underlying technical error while displaying a user-friendly message.

---

# 30. Hardware Information Must Be Real

Never generate fake values.

For example, do NOT do:

```python
cpu_temperature = 55
```

unless that value actually came from a real hardware/API reading.

If a metric cannot be obtained:

```python
temperature_celsius = None
```

Then display:

```text
N/A
```

or:

```text
Not available
```

---

# 31. Performance Requirements

The monitoring application itself should be lightweight.

Target:

```text
CPU usage: preferably below 2–5%
Memory: preferably below 150 MB
```

Avoid:

- excessive polling
- creating threads repeatedly
- recreating widgets every update
- blocking the Tkinter main thread
- unbounded historical data
- unnecessary subprocess calls
- excessive hardware API calls

Update existing widgets instead of destroying and recreating them every second.

---

# 32. Settings

Provide a settings page.

Allow configuration of:

```text
Monitoring interval
Chart history duration
Theme
Start with Windows
Start minimized
Enable logging
Temperature unit
Visible metrics
```

Do not hardcode these values throughout the codebase.

---

# 33. Logging

Use:

```python
import logging
```

Store logs in:

```text
logs/app.log
```

Support:

```text
DEBUG
INFO
WARNING
ERROR
CRITICAL
```

Avoid excessive `print()` statements.

---

# 34. Testing

Create unit tests for:

```text
CPU collector
Memory collector
Disk collector
Network collector
Formatters
Monitor manager
Speed calculations
```

Hardware-dependent tests should use mocks where appropriate.

Tests should not require a specific GPU or CPU.

---

# 35. README

Create a complete README containing:

```text
Project Overview
Features
Architecture
Project Structure
Installation
Virtual Environment
Dependencies
Running the Application
Configuration
Supported Metrics
Windows Limitations
Hardware Sensor Limitations
Troubleshooting
Testing
Development Guide
Future Improvements
```

---

# 36. Development Strategy

Do NOT generate the entire application in one giant response.

Build incrementally.

## Phase 1 — Architecture

First explain:

- overall architecture
- data flow
- project structure
- responsibilities of every folder
- responsibilities of important classes
- dependencies
- monitoring lifecycle

Do not implement the entire application yet.

---

## Phase 2 — Application Skeleton

Create:

```text
app.py
config/
core/
models/
collectors/
services/
ui/
utils/
tests/
```

Create a minimal Tkinter application that launches successfully.

---

## Phase 3 — CPU + Memory

Implement:

```text
CPUCollector
MemoryCollector
CPUInfo
MemoryInfo
CPU page
Memory page
Dashboard cards
```

CPU should include:

```text
CPU name
Physical cores
Logical processors
Overall usage
Per-logical-processor usage
Frequency
Temperature if available
Power if available
```

---

## Phase 4 — GPU

Implement:

```text
GPU abstraction
NVIDIA support
AMD support where possible
Intel support where possible
GPU UI
VRAM monitoring
GPU temperature
```

---

## Phase 5 — Disk + Network

Implement:

```text
DiskCollector
NetworkCollector
Read/write speed
Download/upload speed
Disk UI
Network UI
```

---

## Phase 6 — Sensors

Implement:

```text
Temperature
Fan RPM
Power
SSD health / temperature where possible
```

---

## Phase 7 — Processes

Implement:

```text
Process monitoring
Sorting
Search
CPU usage
Memory usage
Threads
```

---

## Phase 8 — Charts

Implement historical charts for:

```text
CPU
RAM
GPU
Disk
Network
Temperature
```

---

## Phase 9 — Settings

Implement:

```text
Monitoring interval
Theme
Chart history
Startup behavior
Visible metrics
```

---

## Phase 10 — Testing and Optimization

Implement:

```text
Unit tests
Error handling
Logging
Performance optimization
Memory leak checks
Thread safety checks
```

---

# 37. Coding Standards

Follow these rules strictly:

1. Use Python only.
2. Use Tkinter / ttk for GUI.
3. Do not use PySide6, PyQt, Electron, JavaScript, or web-based UI.
4. Keep UI and monitoring logic separated.
5. Use type hints.
6. Use dataclasses for monitoring models.
7. Use small functions.
8. Follow Single Responsibility Principle.
9. Avoid global state.
10. Avoid giant classes.
11. Avoid giant files.
12. Use meaningful names.
13. Add docstrings to important classes/functions.
14. Use logging instead of excessive `print()`.
15. Never fake hardware metrics.
16. Handle unavailable hardware gracefully.
17. Never update Tkinter widgets from background threads.
18. Use `queue.Queue` + `root.after()` or an equivalent safe mechanism.
19. Keep historical data bounded.
20. Make the application extensible.
21. Do not over-engineer.
22. Prefer simple, readable solutions.
23. Explain important architectural decisions.
24. Provide complete runnable files when implementing a phase.
25. Do not silently omit requested features; clearly explain limitations when a hardware API cannot provide a metric.

---

# 38. Response Format for the Coding Agent

For every implementation phase, respond using:

## 1. Goal

Explain what is being implemented.

## 2. Architecture

Explain how the components interact.

## 3. File Structure

Show created/modified files.

## 4. Code

Provide complete code for every created/modified file.

Do not provide incomplete code snippets when a complete file is expected.

## 5. Explanation

Explain important classes, functions, and design decisions.

## 6. Installation

Provide required commands.

## 7. Run

Provide the exact command to run the application.

## 8. Verification

Explain how to verify that the feature works.

## 9. Known Limitations

Clearly identify hardware/API limitations.

## 10. Next Phase

Explain what should be implemented next.

---

# 39. First Task

Start with **Phase 1 only**.

Do NOT implement all features yet.

First provide:

1. Overall architecture
2. Architecture diagram
3. Data flow diagram
4. Complete project tree
5. Responsibility of every folder
6. Responsibility of every important file
7. Main classes and their responsibilities
8. CPU monitoring architecture
9. How physical cores and logical processors will be represented
10. How per-logical-processor performance will be collected
11. How CPU frequency will be collected
12. How CPU temperature and power will be handled
13. How GPU-specific APIs will be abstracted
14. How background monitoring will work with Tkinter
15. How worker threads communicate safely with Tkinter
16. Recommended Python packages
17. Windows-specific limitations
18. Hardware sensor limitations
19. Recommended implementation order

After completing Phase 1, **stop and wait for my instruction to continue to Phase 2**.
