# Calibration Review

## Verdict

The engine's short-term behavior is directionally credible. Exercise-specific baselines make
initial strength personal when supplied. Long-term hypertrophy and neural adaptation are now
separate and asymptotic, but outputs remain simulations rather than individual forecasts.

## Findings

1. **Fixed — progress ceiling crash.** A sufficiently long simulation could raise progress
   above `1.0`; fractional exponentiation then produced a complex number and crashed the next
   training day. Progress is now clamped to `[0, 1]`, with a regression test covering the
   ceiling and a deterministic 52-week test covering the original failure path.
2. **Mitigated — fallback strength is undercalibrated.** For a 90 kg athlete, advanced Chest
   Press falls back to 32.58 kg (`0.362x` bodyweight). Users can now replace that guess per
   exercise with a recent 1–10RM set. Machine loads differ, so calibration is intentionally
   exercise-specific; uncalibrated values are visibly labeled as fallbacks.
3. **Mitigated — progression previously reached the ceiling too quickly.** The intermediate
   scenario now moves from progress `0.35` to about `0.455` after one year and `0.543` after
   two years, rather than reaching `1.0` in year one. Neural/skill adaptation has a separate
   finite reserve and slows over time.
4. **Medium — lower-body repetition uplift needs refinement.** Every repetition curve falls
   within the deliberately broad target bands, but the lower-body advantage remains strong at
   90–95% 1RM. Published comparisons indicate that exercise differences narrow at heavier
   loads.
5. **Plausible — rest and recovery direction.** Five-set volume rises from 26 repetitions at
   30 seconds rest to 35 at 300 seconds. Residual fatigue declines across 72 hours. Both trends
   agree with the cited experimental literature, though their exact magnitudes remain
   unvalidated.

## Recommended Next Change

Add age and sex as calibration inputs and test multiple training volumes. The current
longitudinal bands span heterogeneous populations, so they should not be narrowed until the
profile can represent those important moderators.
