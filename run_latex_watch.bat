@echo off
setlocal EnableExtensions EnableDelayedExpansion

if "%~1"=="" (
    echo [ERROR] Please pass a .tex file path.
    echo Usage:
    echo   run_latex_watch.bat "D:\paper\main.tex"
    echo   run_latex_watch.bat "D:\paper\main.tex" --once
    echo   run_latex_watch.bat "D:\paper\main.tex" --verbose
    pause
    exit /b 1
)

set "TEXFILE=%~1"
set "EXTRA_ARGS=%2 %3 %4 %5 %6 %7 %8 %9"
set "EXITCODE=1"
set "PYTHON_EXE="

for /f "delims=" %%D in ('dir /b /ad /o-n "%LocalAppData%\Programs\Python\Python*" 2^>nul') do (
    if exist "%LocalAppData%\Programs\Python\%%D\python.exe" (
        set "PYTHON_EXE=%LocalAppData%\Programs\Python\%%D\python.exe"
        goto :run_python
    )
)

where python >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON_EXE=python"
    goto :run_python
)

where py >nul 2>nul
if %errorlevel%==0 (
    py -3 "%~dp0build_tex_watch.py" "%TEXFILE%" --engine xelatex --outdir out --auxdir auxil %EXTRA_ARGS%
    set "EXITCODE=!errorlevel!"
    goto :end
)

echo [ERROR] No usable Python launcher was found.
pause
set "EXITCODE=1"
goto :end

:run_python
"%PYTHON_EXE%" "%~dp0build_tex_watch.py" "%TEXFILE%" --engine xelatex --outdir out --auxdir auxil %EXTRA_ARGS%
set "EXITCODE=!errorlevel!"

:end
endlocal & exit /b %EXITCODE%
