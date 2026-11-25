
@echo off
setlocal

cd /d "%~dp0"

set "PYINSTALLER=%~dp0.build\venv\Scripts\pyinstaller.exe"
set "DIST=%~dp0.build\numpy-test-dist"
set "WORK=%~dp0.build\numpy-test-work"

if exist "%DIST%" rmdir /s /q "%DIST%"
if exist "%WORK%" rmdir /s /q "%WORK%"

"%PYINSTALLER%" --noconfirm --clean --onedir --console --debug=imports --name GeometryPlaygroundTest --distpath "%DIST%" --workpath "%WORK%" --specpath "%~dp0.build" --paths "%~dp0." --collect-all numpy --hidden-import numpy.linalg._umath_linalg --collect-all vtkmodules --collect-all pyvista --collect-all pyvistaqt --collect-all pyqtgraph "%~dp0run.py"

echo.
echo Build exit code: %ERRORLEVEL%
pause
