@echo off
where py >nul 2>nul
if not errorlevel 1 (
  py -3 "%~dp0package_game.py" %*
  exit /b
)
where python >nul 2>nul
if errorlevel 1 (
  echo Python 3.9 or newer is required. Install Python 3 and enable its launcher or PATH option.
  exit /b 1
)
python "%~dp0package_game.py" %*
exit /b
