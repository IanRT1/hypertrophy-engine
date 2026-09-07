# Model Evidence Registry

This registry connects empirical behavior to source IDs in calibration/SOURCES.md. A source
supports only the stated relationship, not every coefficient in its implementation.

| Behavior | Evidence | Status | Implementation decision |
|---|---|---|---|
| Baseline 1RM from an all-out set | STRENGTH-001, STRENGTH-002 | Direct/inferred | Brzycki equation, restricted to 1-10 reps; UI recommends 4-10. Exercise-specific error remains. |
| Reps decline as relative load rises | REPS-001, REPS-002 | Direct | Broad calibration bands at 50-95% 1RM. |
| Lower-body lifts may permit more reps | REPS-001 | Inferred | Lower-body modifiers; exact values remain unvalidated. |
| Longer inter-set rest preserves volume | REST-001, REST-002 | Direct/inferred | Monotonic recovery function; exact decay coefficient remains unvalidated. |
| Fatigue can persist for 48-72 hours | RECOVERY-001, RECOVERY-002 | Direct/inferred | Calibration checks declining residual fatigue through 72 hours. |
| Multi-month hypertrophy progression | None | Unvalidated | Current adaptation coefficients are simulation assumptions, not forecasts. |

## Updating the model

When changing an evidence-sensitive formula, add or update its source ID, state whether the
exact coefficient is direct or inferred, and add a deterministic calibration test. Record
unsupported behavior as **Unvalidated** rather than assigning a convenient citation.
