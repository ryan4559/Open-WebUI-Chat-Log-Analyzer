@echo off
setlocal enabledelayedexpansion

:: ====================================================================
:: Batch script to automate the JSON to SQLite analysis pipeline.
:: ====================================================================

:: --- Configuration ---
SET "PYTHON_EXE=python"
SET "VENV_DIR=venv"
SET "CONVERT_SCRIPT=json_to_sqlite.py"
SET "ANALYZE_SCRIPT=analyze_monthly_usage.py"

:: --- Script Body ---

echo.
echo [Step 1/5] Setting up Python virtual environment...

:: Check if the virtual environment directory exists
IF NOT EXIST "%VENV_DIR%\" (
    echo Creating virtual environment in '%VENV_DIR%' folder...
    %PYTHON_EXE% -m venv %VENV_DIR%
    IF %ERRORLEVEL% NEQ 0 (
        echo.
        echo ERROR: Failed to create the virtual environment.
        echo Please make sure Python is installed and accessible in your PATH.
        goto :error
    )
) ELSE (
    echo Virtual environment already exists.
)

echo.
echo [Step 2/5] Installing required Python packages...

:: Install dependencies using the venv's pip
call "%VENV_DIR%\Scripts\pip.exe" install ijson > nul
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Failed to install required Python packages.
    goto :error
)
echo Packages are up to date.

echo.
echo [Step 3/5] Finding JSON file to process...

:: Find the JSON file
set "JSON_FILE="
for %%f in (*.json) do (
    if not defined JSON_FILE (
        set "JSON_FILE=%%f"
    ) else (
        echo.
        echo ERROR: More than one JSON file found in this directory.
        echo Please keep only one JSON file here to run the script automatically.
        goto :error
    )
)

if not defined JSON_FILE (
    echo.
    echo ERROR: No JSON file found in this directory.
    goto :error
)

echo Found JSON file: %JSON_FILE%

echo.
echo [Step 4/5] Converting JSON data to SQLite database...

:: Run the conversion script, passing the found JSON file as an argument
call "%VENV_DIR%\Scripts\python.exe" %CONVERT_SCRIPT% "%JSON_FILE%"
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: The data conversion script failed.
    goto :error
)

echo.
echo [Step 5/5] Analyzing and displaying monthly usage...

:: Run the analysis script
call "%VENV_DIR%\Scripts\python.exe" %ANALYZE_SCRIPT%
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: The analysis script failed.
    goto :error
)

echo.
echo ==================================================
echo  Script finished successfully!
echo ==================================================
goto :end

:error
_:

echo.
echo An error occurred. The script will now exit.

:end

echo.
pause
endlocal
