@echo off
setlocal
pushd "%~dp0"

set "APP_PYTHON=.venv\Scripts\pythonw.exe"
if not exist "%APP_PYTHON%" (
    echo Hypertrophy Engine is not set up yet.
    echo.
    echo Create the environment and install the application with:
    echo   python -m venv .venv
    echo   .venv\Scripts\python.exe -m pip install -e .
    echo.
    pause
    popd
    exit /b 1
)

start "" "%APP_PYTHON%" "main.py"
popd
exit /b 0
