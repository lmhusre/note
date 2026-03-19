@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

if "%~1"=="" (
  set "MD=高分子化学\高分子化学.md"
) else (
  set "MD=%~1"
)

if not exist "%MD%" (
  echo [ERROR] File not found: %MD%
  exit /b 1
)

for %%F in ("%MD%") do (
  set "DIR=%%~dpF"
  set "BASE=%%~nF"
)

set "TEX=!DIR!!BASE!_xelatex.tex"

echo [1/2] Converting markdown to LaTeX...
pandoc "%MD%" -o "!TEX!" --standalone --from=markdown+tex_math_dollars+raw_tex -V documentclass=ctexart
if errorlevel 1 (
  echo [ERROR] Pandoc conversion failed.
  exit /b 1
)

echo [2/2] Compiling with XeLaTeX...
xelatex -interaction=nonstopmode -halt-on-error -output-directory="!DIR!" "!TEX!"
if errorlevel 1 (
  echo [ERROR] XeLaTeX compilation failed.
  exit /b 1
)

echo [OK] Generated: !DIR!!BASE!_xelatex.pdf
exit /b 0
