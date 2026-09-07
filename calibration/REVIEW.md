# Calibration Review

## Verdict

The engine's short-term behavior is directionally credible, but its absolute strength and
year-long progression are not yet realistic enough to treat as predictions. The reports are
best used as regression diagnostics while those parts of the model are redesigned.

## Findings

1. **Fixed — progress ceiling crash.** A sufficiently long simulation could raise progress
   above `1.0`; fractional exponentiation then produced a complex number and crashed the next
   training day. Progress is now clamped to `[0, 1]`, with a regression test covering the
   ceiling and a deterministic 52-week test covering the original failure path.
2. **High — starting strength is undercalibrated.** For a 90 kg athlete, advanced Chest Press
   starts at 32.58 kg (`0.362x` bodyweight). That is not a defensible bench-like strength
   baseline. Machine loads also differ by equipment, so a universal exercise-load standard
   would create false precision.
3. **High — progression reaches the model ceiling too quickly.** The intermediate Chest Press
   scenario reaches progress `1.0` within 52 weeks on three weekly sessions. The meaning of
   that ceiling and its time scale need to be explicitly defined before growth coefficients
   are tuned.
4. **Medium — lower-body repetition uplift needs refinement.** Every repetition curve falls
   within the deliberately broad target bands, but the lower-body advantage remains strong at
   90–95% 1RM. Published comparisons indicate that exercise differences narrow at heavier
   loads.
5. **Plausible — rest and recovery direction.** Five-set volume rises from 26 repetitions at
   30 seconds rest to 35 at 300 seconds. Residual fatigue declines across 72 hours. Both trends
   agree with the cited experimental literature, though their exact magnitudes remain
   unvalidated.

## Recommended Next Change

Replace inferred absolute starting loads with user-entered baseline performance (an estimated
1RM or recent load/repetitions for each exercise), retaining the current bodyweight/experience
calculation only as a clearly labeled fallback. Then define what `progress = 1` represents and
calibrate multi-month adaptation against longitudinal resistance-training data. Do not tighten
the broad repetition bands until exercise-specific datasets justify narrower limits.
