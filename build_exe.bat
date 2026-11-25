
@echo off
setlocal EnableExtensions

cd /d "%~dp0"
title Geometry Playground 2.0 - EXE Builder

set "BUILD_DIR=%~dp0.build"
set "VENV_DIR=%BUILD_DIR%\venv"
set "PYTHON=%VENV_DIR%\Scripts\python.exe"
set "PYINSTALLER=%VENV_DIR%\Scripts\pyinstaller.exe"
set "DIST_DIR=%BUILD_DIR%\dist"
set "WORK_DIR=%BUILD_DIR%\work"
set "EXE_PATH=%DIST_DIR%\GeometryPlayground.exe"

echo.
echo ============================================
echo   Geometry Playground 2.0 - EXE Builder
echo ============================================
echo.

if not exist "%~dp0run.py" (
    echo [ERROR] run.py not found.
    goto :error
)

if not exist "%~dp0requirements.txt" (
    echo [ERROR] requirements.txt not found.
    goto :error
)

py -3.12 --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.12 was not found.
    echo Install Python 3.12 x64 and enable the Python Launcher.
    goto :error
)

if not exist "%PYTHON%" (
    echo [1/5] Creating isolated build environment...

    if not exist "%BUILD_DIR%" mkdir "%BUILD_DIR%"

    py -3.12 -m venv "%VENV_DIR%"
    if errorlevel 1 goto :error
) else (
    echo [1/5] Reusing build environment...
)

echo.
echo [2/5] Updating pip...

"%PYTHON%" -m pip install --upgrade pip
if errorlevel 1 goto :error

echo.
echo [3/5] Installing application dependencies...

"%PYTHON%" -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 goto :error

echo.
echo [4/5] Installing PyInstaller...

"%PYTHON%" -m pip install --upgrade "pyinstaller>=6.22,<7"
if errorlevel 1 goto :error

if not exist "%PYINSTALLER%" (
    echo [ERROR] PyInstaller executable not found:
    echo "%PYINSTALLER%"
    goto :error
)

echo.
echo [5/5] Building single-file executable...

if exist "%WORK_DIR%" rmdir /s /q "%WORK_DIR%"
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"

"%PYINSTALLER%" --noconfirm --clean --onefile --windowed --name GeometryPlayground --distpath "%DIST_DIR%" --workpath "%WORK_DIR%" --specpath "%BUILD_DIR%" --paths "%~dp0." --collect-all vtkmodules --collect-all pyvista --collect-all pyvistaqt --collect-all pyqtgraph --collect-all numpy --hidden-import numpy.linalg._umath_linalg --hidden-import vtkmodules.qt.QVTKRenderWindowInteractor --hidden-import vtkmodules.vtkRenderingOpenGL2 --hidden-import vtkmodules.vtkInteractionStyle --hidden-import vtkmodules.vtkRenderingFreeType --hidden-import vtkmodules.vtkRenderingUI --hidden-import vtkmodules.vtkRenderingCore --hidden-import vtkmodules.vtkRenderingAnnotation --hidden-import vtkmodules.vtkRenderingVolumeOpenGL2 --hidden-import vtkmodules.vtkIOXML "%~dp0run.py"

if errorlevel 1 goto :error

if not exist "%EXE_PATH%" (
    echo [ERROR] PyInstaller finished, but the EXE file was not created.
    goto :error
)

echo.
echo ============================================
echo   BUILD SUCCESSFUL
echo ============================================
echo.
echo Executable:
echo "%EXE_PATH%"
echo.
echo Copy this single EXE to another Windows x64 computer.
echo The first launch may take longer because one-file mode
echo extracts its bundled files into a temporary directory.
echo.
pause
exit /b 0

:error
echo.
echo ============================================
echo   BUILD FAILED
echo ============================================
echo Check the error messages above.
echo.
pause
exit /b 1
