"""Application-wide constants (not user-configurable)."""
APP_NAME = "PC Performance Monitor"
APP_VERSION = "1.0.0"

INTERVAL_CHOICES_MS = {
    "100 ms": 100, "250 ms": 250, "500 ms": 500,
    "1 second": 1000, "2 seconds": 2000, "5 seconds": 5000,
}
HISTORY_CHOICES_S = {"1 minute": 60, "2 minutes": 120, "5 minutes": 300, "10 minutes": 600}
MAX_HISTORY_POINTS = 600          # hard cap per series, regardless of settings
MIN_PROCESS_INTERVAL_S = 2.0      # processes are expensive: never collect faster
ADDRESS_REFRESH_S = 10.0          # NIC addresses change rarely
MAX_PROCESS_ROWS = 400            # rows rendered in the process table
QUEUE_MAXSIZE = 2                 # worker -> UI; the UI only wants the freshest data

# (moderate, high, critical) lower bounds
DEFAULT_USAGE_THRESHOLDS = (50.0, 80.0, 95.0)
# Generic defaults only. Real limits vary per CPU/GPU model - users should tune these.
DEFAULT_TEMP_THRESHOLDS_C = (60.0, 80.0, 90.0)

PAGES = ("Dashboard", "CPU", "Memory", "GPU", "Disk", "Network", "Processes", "System", "Settings")
