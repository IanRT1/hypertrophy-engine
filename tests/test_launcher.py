from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = PROJECT_ROOT / "Run Hypertrophy Engine.bat"


def test_windows_launcher_uses_its_own_directory_and_project_environment():
    text = LAUNCHER.read_text(encoding="utf-8")
    assert 'pushd "%~dp0"' in text
    assert '.venv\\Scripts\\pythonw.exe' in text
    assert '"main.py"' in text


def test_windows_launcher_handles_missing_environment():
    text = LAUNCHER.read_text(encoding="utf-8")
    assert 'if not exist "%APP_PYTHON%"' in text
    assert "python -m venv .venv" in text
    assert "exit /b 1" in text
