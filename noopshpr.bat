@echo off
setlocal

IF EXIST "%~dp0\..\python.exe" (
  "%~dp0\..\python.exe" %~dp0\noopshpr %*
) ELSE (
  python %~dp0\noopshpr %*
)
