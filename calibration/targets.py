"""Broad literature-informed targets used by calibration diagnostics."""

# Evidence: REPS-001, REPS-002. Approximate repetitions to momentary failure.
# Bands deliberately accommodate inter-individual and exercise-specific variation.
GENERAL_REP_BANDS = {
    0.50: (20, 40),
    0.60: (14, 28),
    0.70: (9, 19),
    0.75: (7, 16),
    0.80: (5, 13),
    0.85: (3, 9),
    0.90: (2, 6),
    0.95: (1, 4),
}

# Evidence: REPS-001 (inferred coefficient, not directly validated).
LOWER_BODY_REP_BANDS = {
    fraction: (lower, round(upper * 1.35))
    for fraction, (lower, upper) in GENERAL_REP_BANDS.items()
}

REST_SECONDS = (30, 60, 120, 180, 300)
LEVELS = ("Beginner", "Intermediate", "Advanced")
REP_FRACTIONS = tuple(GENERAL_REP_BANDS)
