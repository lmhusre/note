@echo off
setlocal EnableExtensions EnableDelayedExpansion

if "%~1"=="" (
    echo [ERROR] 请把 .tex 文件拖到这个 bat 上，或在命令行传入 tex 文件路径
    echo 用法：
    echo   run_latex_watch.bat "D:\paper\main.tex"
    echo   run_latex_watch.bat "D:\paper\main.tex" --once
    echo   run_latex_watch.bat "D:\paper\main.tex" --verbose
    pause
    exit /b 1
)

set "TEXFILE=%~1"
set "EXTRA_ARGS=%2 %3 %4 %5 %6 %7 %8 %9"
set "EXITCODE=1"

where python >nul 2>nul
if %errorlevel%==0 (
    python "%~dp0build_tex_watch.py" "%TEXFILE%" --engine xelatex --outdir out --auxdir auxil %EXTRA_ARGS%
    set "EXITCODE=!errorlevel!"
    goto :end
)

where py >nul 2>nul
if %errorlevel%==0 (
    py -3 "%~dp0build_tex_watch.py" "%TEXFILE%" --engine xelatex --outdir out --auxdir auxil %EXTRA_ARGS%
    set "EXITCODE=!errorlevel!"
    goto :end
)

echo [ERROR] 未找到 python 或 py 启动器
pause
set "EXITCODE=1"

:end
endlocal & exit /b %EXITCODE%
