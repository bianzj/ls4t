@echo off
rem Start the LS4T GUI with the python311 conda environment (PATH must include its Library\bin).
setlocal
set "ENV=C:\work\miniconda\envs\python311"
if not "%LS4T_PYTHON_ENV%"=="" set "ENV=%LS4T_PYTHON_ENV%"
set "PATH=%ENV%;%ENV%\Library\mingw-w64\bin;%ENV%\Library\usr\bin;%ENV%\Library\bin;%ENV%\Scripts;%ENV%\bin;%PATH%"
set "PYTHONUTF8=1"
cd /d "%~dp0.."
"%ENV%\python.exe" gui\server.py %*
