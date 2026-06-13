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

if "%PIPELINE_DIR%"=="" set PIPELINE_DIR=%USERPROFILE%\session-pipeline
if "%WHISPER_MODEL%"=="" set WHISPER_MODEL=large-v3

set WHISPER_BIN=%PIPELINE_DIR%\whisper.cpp\build\bin\Release\whisper-cli.exe
set MODEL_PATH=%PIPELINE_DIR%\whisper.cpp\models\ggml-%WHISPER_MODEL%.bin

if "%~1"=="" (
    echo Usage: %~nx0 "path\to\recording.m4a"
    exit /b 1
)

set INPUT=%~1
for %%F in ("%INPUT%") do set NAME=%%~nF

if not exist "%PIPELINE_DIR%\transcripts" mkdir "%PIPELINE_DIR%\transcripts"

set WAV_FILE=%PIPELINE_DIR%\transcripts\%NAME%_16k.wav

echo Converting audio to 16kHz mono WAV...
"%PIPELINE_DIR%\ffmpeg\bin\ffmpeg.exe" -y -i "%INPUT%" -ar 16000 -ac 1 -c:a pcm_s16le "%WAV_FILE%" -loglevel error

echo Running whisper.cpp (%WHISPER_MODEL%)...
"%WHISPER_BIN%" -m "%MODEL_PATH%" -f "%WAV_FILE%" --output-json-full --output-txt --output-file "%PIPELINE_DIR%\transcripts\%NAME%"

del "%WAV_FILE%"

echo.
echo Done.
echo   Plain transcript: %PIPELINE_DIR%\transcripts\%NAME%.txt
echo   Full JSON: %PIPELINE_DIR%\transcripts\%NAME%.json

endlocal
