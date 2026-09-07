import pytest

from domain import Engine
from domain.athlete_profile import AthleteProfile


@pytest.fixture
def beginner_engine() -> Engine:
    return Engine(AthleteProfile(bodyweight=90.0, training_level="Beginner"), seed=1234)


@pytest.fixture
def deterministic_engine(beginner_engine: Engine, monkeypatch: pytest.MonkeyPatch) -> Engine:
    monkeypatch.setattr(beginner_engine, "_noise", lambda mean=1.0, variation=0.05: mean)
    return beginner_engine

