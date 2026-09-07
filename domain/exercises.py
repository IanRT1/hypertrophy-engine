from dataclasses import dataclass


# ===============================================================
# Exercise Profile
# ===============================================================
@dataclass(frozen=True)
class ExerciseProfile:
    """
    Defines how an exercise interacts with the muscular system.

    muscle_distribution:
        How stimulus & fatigue are distributed per muscle.
        Recommended: sum ~1.0.

    strength_contribution:
        How muscles contribute to 1RM for this lift.
        Recommended: sum ~1.0.
    """
    name: str
    muscle_distribution: dict[str, float]
    strength_contribution: dict[str, float]


# ===============================================================
# Exercise Catalog
# ===============================================================
EXERCISE_CATALOG: dict[str, ExerciseProfile] = {

    # -------------------------------
    # Upper Body Exercises
    # -------------------------------
    "Chest Press": ExerciseProfile(
        name="Chest Press",
        muscle_distribution={
            "Chest": 0.75,
            "Triceps": 0.20,
            "Shoulders": 0.05,
        },
        strength_contribution={
            "Chest": 0.70,
            "Triceps": 0.25,
            "Shoulders": 0.05,
        },
    ),

    "Lat Pulldown": ExerciseProfile(
        name="Lat Pulldown",
        muscle_distribution={
            "Back": 0.60,
            "Biceps": 0.25,
            "Shoulders": 0.15,
        },
        strength_contribution={
            "Back": 0.65,
            "Biceps": 0.25,
            "Shoulders": 0.10,
        },
    ),

    "Machine Row": ExerciseProfile(
        name="Machine Row",
        muscle_distribution={
            "Back": 0.65,
            "Biceps": 0.25,
            "Shoulders": 0.10,
        },
        strength_contribution={
            "Back": 0.70,
            "Biceps": 0.20,
            "Shoulders": 0.10,
        },
    ),

    "Cable Lateral Raises": ExerciseProfile(
        name="Cable Lateral Raises",
        muscle_distribution={
            "Shoulders": 0.85,
            "Triceps": 0.10,
            "Chest": 0.05,
        },
        strength_contribution={
            "Shoulders": 0.85,
            "Triceps": 0.10,
            "Chest": 0.05,
        },
    ),

    "Cable Tricep Pulldowns": ExerciseProfile(
        name="Cable Tricep Pulldowns",
        muscle_distribution={
            "Triceps": 0.90,
            "Shoulders": 0.05,
            "Chest": 0.05,
        },
        strength_contribution={
            "Triceps": 0.90,
            "Shoulders": 0.05,
            "Chest": 0.05,
        },
    ),

    "Bicep Bar Curl": ExerciseProfile(
        name="Bicep Bar Curl",
        muscle_distribution={
            "Biceps": 0.85,
            "Shoulders": 0.05,
        },
        strength_contribution={
            "Biceps": 0.85,
            "Shoulders": 0.05,
        },
    ),

    # -------------------------------
    # Lower Body Exercises
    # -------------------------------
    "Leg Press": ExerciseProfile(
        name="Leg Press",
        muscle_distribution={
            "Quads": 0.70,
            "Glutes": 0.20,
            "Hamstrings": 0.10,
        },
        strength_contribution={
            "Quads": 0.65,
            "Glutes": 0.25,
            "Hamstrings": 0.10,
        },
    ),

    "Leg Extension": ExerciseProfile(
        name="Leg Extension",
        muscle_distribution={
            "Quads": 0.90,
            "Hamstrings": 0.05,
            "Calves": 0.05,
        },
        strength_contribution={
            "Quads": 0.90,
            "Hamstrings": 0.05,
            "Calves": 0.05,
        },
    ),

    "Leg Curl": ExerciseProfile(
        name="Leg Curl",
        muscle_distribution={
            "Hamstrings": 0.85,
            "Glutes": 0.10,
            "Calves": 0.05,
        },
        strength_contribution={
            "Hamstrings": 0.85,
            "Glutes": 0.10,
            "Calves": 0.05,
        },
    ),

    "Calf Raise": ExerciseProfile(
        name="Calf Raise",
        muscle_distribution={
            "Calves": 0.95,
            "Quads": 0.05,
        },
        strength_contribution={
            "Calves": 0.95,
            "Quads": 0.05,
        },
    ),
}
