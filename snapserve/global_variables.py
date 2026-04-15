from pathlib import Path


BASE_DIR = Path.home() / ".snapserve"
PID_DIR = BASE_DIR / "pids"
LOG_DIR = BASE_DIR / "logs"

PID_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)