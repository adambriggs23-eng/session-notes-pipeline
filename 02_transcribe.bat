@echo off
REM ==============================================================================
REM 02_transcribe.bat
REM
REM Transcribes an audio file to text using whisper.cpp (fully offline).
REM
REM Usage:
REM   02_transcribe.bat "D:\session-pipeline\recordings\session1.m4a"
REM ==============================================================================

setlocal

if "%PIPELINE_DIR%"==\"\" set PIPELINE_DIR=%USERPROFILE%\session-pipeline
if "%WHISPER_MODEL%"==\"\" set WHISPER_MODEL=large-v3

set WHISPER_BIN=%PIPELINE_DIR%\whisper.cpp\build\bin\Release\whisper-cli.exe
set MODEL_PATH=%PIPELINE_DIR%\whisper.cpp\models\ggml-%WHISPER_MODEL%.bin
set FFMPEG_BIN=%PIPELINE_DIR%\ffmpeg\bin\ffmpeg.exe

if "%~1"==\"\" (
    echo Usage: %~nx0 \"path\to\recording.m4a\"
    exit /b 1
)

set INPUT=%~1
for %%F in ("%INPUT%") do set NAME=%%~nF

if not exist "%PIPELINE_DIR%\transcripts" mkdir "%PIPELINE_DIR%\transcripts"

REM ---- Pre-flight checks ----
if not exist "%FFMPEG_BIN%" (
    echo ERROR: ffmpeg not found at %FFMPEG_BIN%
    echo.
    echo Check the setup guide Part 1.5 - ffmpeg may have been extracted to the wrong location.
    echo The path should be exactly: %PIPELINE_DIR%\ffmpeg\bin\ffmpeg.exe
    exit /b 1
)

if not exist "%WHISPER_BIN%" (
    echo ERROR: whisper binary not found at %WHISPER_BIN%
    echo.
    echo Did you complete Part 5 of the setup guide?
    echo Try running these commands in Command Prompt:
    echo   cd %PIPELINE_DIR%\whisper.cpp
    echo   cmake -B build
    echo   cmake --build build --config Release
    exit /b 1
)

if not exist "%MODEL_PATH%" (
    echo ERROR: model file not found at %MODEL_PATH%
    echo.
    echo Did you download the model in Part 5?
    echo Try running this command in Command Prompt:
    echo   cd %PIPELINE_DIR%\whisper.cpp\models
    echo   download-ggml-model.cmd %WHISPER_MODEL%
    exit /b 1
)

if not exist "%INPUT%" (
    echo ERROR: input file not found: %INPUT%
    exit /b 1
)

set WAV_FILE=%PIPELINE_DIR%\transcripts\%NAME%_16k.wav

echo Converting audio to 16kHz mono WAV...
"%FFMPEG_BIN%" -y -i "%INPUT%" -ar 16000 -ac 1 -c:a pcm_s16le "%WAV_FILE%" -loglevel error

if errorlevel 1 (
    echo ERROR: ffmpeg conversion failed
    exit /b 1
)

echo Running whisper.cpp (%WHISPER_MODEL%)...
"%WHISPER_BIN%" -m "%MODEL_PATH%" -f "%WAV_FILE%" --output-json-full --output-txt --output-file "%PIPELINE_DIR%\transcripts\%NAME%"

if errorlevel 1 (
    echo ERROR: whisper transcription failed
    del "%WAV_FILE%" 2>nul
    exit /b 1
)

del "%WAV_FILE%"

echo.
echo Done.
echo   Plain transcript: %PIPELINE_DIR%\transcripts\%NAME%.txt
echo   Full JSON: %PIPELINE_DIR%\transcripts\%NAME%.json

endlocal
exit /b 0
