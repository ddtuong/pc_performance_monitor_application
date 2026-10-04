"""PC Performance Monitor entry point:  python app.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def main() -> int:
    from core.application import Application
    Application().run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
