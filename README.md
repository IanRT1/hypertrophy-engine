# Hypertrophy Engine

A PySide6 desktop application for simulating resistance-training performance, fatigue,
recovery, hypertrophy, and strength adaptation over time.

## Development

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
```

Launch from a source checkout with `python main.py`. After installation, the
`hypertrophy-engine` command launches the application from any working directory.

Model assumptions and supporting research are tracked in `docs/evidence.md`; calibration
sources and reproducible diagnostics live under `calibration/`.
