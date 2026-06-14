#!/usr/bin/env python3
"""
00_watcher.py

Watches the "recordings" folder on your external SSD. Whenever a new audio
file appears (and finishes copying), it automatically runs:

    1. Transcription (whisper.cpp)
    2. Speaker diarization (pyannote)
    3. Merge into a speaker-labelled transcript

The finished transcript appears in the "transcripts" folder, and the
original recording is moved into "recordings/processed" so it doesn't get
processed twice.

USAGE:
    Just run this script and leave the window open. Then plug in your phone,
    copy a new recording into the "recordings" folder, and processing will
    start automatically within a few seconds.

    To stop: close the window, or press Ctrl+C.
"""

import os
import sys
import time
import shutil
import subprocess
from pathlib import Path

# ---- CONFIG -----------------------------------------------------------------
PIPELINE_DIR = Path(os.environ.get("PIPELINE_DIR", Path.home() / "session-pipeline"))
RECORDINGS_DIR = PIPELINE_DIR / "recordings"
PROCESSED_DIR = RECORDINGS_DIR / "processed"
ERRORS_DIR = RECORDINGS_DIR / "errors"
AUDIO_EXTENSIONS = {".wav", ".m4a", ".mp3", ".aac", ".ogg", ".flac"}

# How many seconds a file's size must stay unchanged before we consider it
# "fully copied" and safe to process. Helps avoid grabbing a half-copied file.
STABLE_SECONDS = 5
POLL_INTERVAL = 2

# Set to True to automatically generate a draft DAP note (via local Ollama
# LLM) after each recording is processed. Set to False if you'd rather run
# 05_draft_note.py manually after doing the Clinician/Client rename in the
# transcript (recommended for better-quality drafts).
AUTO_DRAFT_NOTE = False

# Ollama timeout in seconds. Increase if processing long transcripts.
OLLAMA_TIMEOUT = 1200  # 20 minutes
# -------------------------------------------------------------------------------

SCRIPTS_DIR = Path(__file__).resolve().parent


def validate_environment():
    """Check that PIPELINE_DIR exists and all required directories can be created."""
    if not PIPELINE_DIR.exists():
        print(f"ERROR: PIPELINE_DIR not found: {PIPELINE_DIR}")
        print(f"\nCheck that:")
        print(f"  1. Your external SSD is plugged in")
        print(f"  2. The environment variable PIPELINE_DIR is set correctly")
        print(f"  3. You restarted your computer after setting the environment variable (Part 3 of setup)")
        print(f"\nIf you moved your pipeline to a different location, update PIPELINE_DIR and restart.")
        sys.exit(1)

    # Create standard directories
    for dir_path in [RECORDINGS_DIR, PROCESSED_DIR, ERRORS_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)


def is_stable(path: Path) -> bool:
    """Check whether a file's size has stopped changing."""
    try:
        size1 = path.stat().st_size
    except FileNotFoundError:
        return False
    time.sleep(STABLE_SECONDS)
    try:
        size2 = path.stat().st_size
    except FileNotFoundError:
        return False
    return size1 == size2 and size1 > 0


def check_ollama_available() -> bool:
    """Check if Ollama is running and reachable."""
    if not AUTO_DRAFT_NOTE:
        return True
    
    import json
    import urllib.request
    
    try:
        req = urllib.request.Request(
            "http://localhost:11434/api/tags",
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return True
    except Exception:
        return False


def run_pipeline(audio_path: Path):
    """Run the full transcription-diarization-merge pipeline.
    
    Only move files to processed/ if ALL steps succeed.
    Move to errors/ if ANY step fails.
    """
    # Safety check: file must still exist
    if not audio_path.exists():
        print(f"ERROR: File disappeared before processing: {audio_path}")
        return

    name = audio_path.stem
    print(f"\n{'='*70}")
    print(f"New recording detected: {audio_path.name}")
    print(f"{'='*70}")

    # Step 1: Transcribe
    print("\n[1/3] Transcribing audio (this can take several minutes)...")
    transcribe_script = SCRIPTS_DIR / "02_transcribe.bat"
    result = subprocess.run(
        [str(transcribe_script), str(audio_path)],
        shell=True
    )
    if result.returncode != 0:
        print(f"ERROR: transcription failed for {audio_path.name}.")
        print(f"Moving to {ERRORS_DIR.name}/ for review.")
        ERRORS_DIR.mkdir(exist_ok=True)
        shutil.move(str(audio_path), str(ERRORS_DIR / audio_path.name))
        return

    # Step 2: Diarize
    print("\n[2/3] Identifying speakers...")
    venv_python = PIPELINE_DIR / "venv" / "Scripts" / "python.exe"
    diarize_script = SCRIPTS_DIR / "03_diarize.py"
    result = subprocess.run(
        [str(venv_python), str(diarize_script), str(audio_path)],
        shell=True
    )
    if result.returncode != 0:
        print(f"ERROR: diarization failed for {audio_path.name}.")
        print(f"Moving to {ERRORS_DIR.name}/ for review.")
        ERRORS_DIR.mkdir(exist_ok=True)
        shutil.move(str(audio_path), str(ERRORS_DIR / audio_path.name))
        return

    # Step 3: Merge
    print("\n[3/3] Merging transcript with speaker labels...")
    merge_script = SCRIPTS_DIR / "04_merge.py"
    result = subprocess.run(
        [str(venv_python), str(merge_script), name],
        shell=True
    )
    if result.returncode != 0:
        print(f"ERROR: merge failed for {audio_path.name}.")
        print(f"Moving to {ERRORS_DIR.name}/ for review.")
        ERRORS_DIR.mkdir(exist_ok=True)
        shutil.move(str(audio_path), str(ERRORS_DIR / audio_path.name))
        return

    # Step 4 (optional): Draft DAP note with local LLM via Ollama
    if AUTO_DRAFT_NOTE:
        speaker_transcript = PIPELINE_DIR / "transcripts" / f"{name}_speaker_transcript.txt"
        print("\n[4/4] Drafting DAP note with local AI (this is a DRAFT only)...")
        print("NOTE: this step uses the SPEAKER_00/SPEAKER_01 labels as-is unless")
        print("you've already renamed them. You can re-run 05_draft_note.py later")
        print("after renaming for a better draft.")
        draft_script = SCRIPTS_DIR / "05_draft_note.py"
        result = subprocess.run(
            [str(venv_python), str(draft_script), name],
            shell=True
        )
        if result.returncode != 0:
            print(f"WARNING: draft note generation failed for {name}. ")
            print(f"Transcript is still available; you can run ")
            print(f"05_draft_note.py manually later.")

    # All steps succeeded - move to processed folder
    PROCESSED_DIR.mkdir(exist_ok=True)
    dest = PROCESSED_DIR / audio_path.name
    shutil.move(str(audio_path), str(dest))

    print(f"\nDone! Speaker-labelled transcript ready at:")
    print(f"  {PIPELINE_DIR / 'transcripts' / (name + '_speaker_transcript.txt')}")
    if AUTO_DRAFT_NOTE:
        print(f"Draft note ready at:")
        print(f"  {PIPELINE_DIR / 'notes' / (name + '_DRAFT.docx')}")
    print(f"\nOriginal recording moved to: {dest}")
    print(f"\nWatching for new recordings... (leave this window open)")


def main():
    validate_environment()

    print(f"Watching folder: {RECORDINGS_DIR}")
    print("Drop a new audio file in this folder to process it automatically.")
    print("Leave this window open. Press Ctrl+C to stop.\n")

    if AUTO_DRAFT_NOTE:
        print("AUTO_DRAFT_NOTE is enabled. Checking if Ollama is available...")
        if not check_ollama_available():
            print("WARNING: Ollama is not running or not responding.")
            print("Start Ollama before copying recordings, or set AUTO_DRAFT_NOTE=False.\n")
        else:
            print("Ollama is available. Auto-drafting enabled.\n")

    seen = set(p.name for p in RECORDINGS_DIR.iterdir() if p.is_file())

    try:
        while True:
            time.sleep(POLL_INTERVAL)
            current_files = [
                p for p in RECORDINGS_DIR.iterdir()
                if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS
            ]
            for p in current_files:
                if p.name in seen:
                    continue
                # Wait until the file is fully copied
                if not is_stable(p):
                    continue
                seen.add(p.name)
                run_pipeline(p)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
