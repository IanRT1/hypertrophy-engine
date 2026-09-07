# Engine Calibration

Run the diagnostics from the repository root:

```powershell
python -m calibration.generate
```

Reports are written to `calibration/output/` as CSV files plus a compact HTML review.
They are generated artifacts and are intentionally ignored by Git.

The reference bands in `targets.py` are broad plausibility ranges, not medical truths.
Repetitions at a given percentage of 1RM vary substantially between people and exercises.
Use these diagnostics to detect implausible behavior and monotonicity failures, not to tune
the simulation to a single exact repetition table.

Primary sources supporting the initial targets are listed in `SOURCES.md`.
The current interpretation and prioritized model changes are documented in `REVIEW.md`.
