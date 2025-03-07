@echo off
setlocal enabledelayedexpansion

REM Find Unreal Engine build location (this varies by installation)
set UE_ROOT=
for /f "tokens=*" %%i in ('dir /b /s /a:d "C:\Program Files\Epic Games\UE_5.5" 2^>nul') do (
    if exist "%%i\Engine\Build\BatchFiles\Build.bat" (
        set "UE_ROOT=%%i"
        goto :foundUE
    )
)

for /f "tokens=*" %%i in ('dir /b /s /a:d "C:\Program Files\Epic Games\UE_5.5.3" 2^>nul') do (
    if exist "%%i\Engine\Build\BatchFiles\Build.bat" (
        set "UE_ROOT=%%i"
        goto :foundUE
    )
)

echo Could not find Unreal Engine 5.5.3 installation. Please edit this script with the correct path.
goto :eof

:foundUE
echo Found Unreal Engine at: %UE_ROOT%

REM Get current directory
cd /d "%~dp0"
set PROJECT_ROOT=%CD%
set PROJECT_NAME=BlankTemplate
set PLUGIN_NAME=DreamwaveTexGen

REM Compile the plugin
echo Building plugin %PLUGIN_NAME%...
call "%UE_ROOT%\Engine\Build\BatchFiles\RunUAT.bat" BuildPlugin -Plugin="%PROJECT_ROOT%\Plugins\%PLUGIN_NAME%\%PLUGIN_NAME%.uplugin" -Package="%PROJECT_ROOT%\Plugins\%PLUGIN_NAME%" -TargetPlatforms=Win64 -VS2022

echo Build complete! 