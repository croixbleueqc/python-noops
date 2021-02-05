@echo off
setlocal

IF EXIST "%~dp0\..\python.exe" (
  "%~dp0\..\python.exe" %~dp0\noopsctl %*
) ELSE (
  python %~dp0\noopsctl %*
)
