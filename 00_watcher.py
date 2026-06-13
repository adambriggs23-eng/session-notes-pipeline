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
# -------------------------------------------------------------------------------

SCRIPTS_DIR = Path(__file__).resolve().parent


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


def run_pipeline(audio_path: Path):
    name = audio_path.stem
    print(f"\n{'='*70}")
    print(f"New recording detected: {audio_path.name}")
    print(f"{'='*70}")

    # Step 1: Transcribe
    print("\n[1/3] Transcribing audio (this can take several minutes)...")
    transcribe_script = SCRIPTS_DIR / "02_transcribe.bat"
    result = subprocess.run([str(transcribe_script), str(audio_path)], shell=True)
    if result.returncode != 0:
        print(f"ERROR: transcription failed for {audio_path.name}. Leaving file in place for review.")
        return

    # Step 2: Diarize
    print("\n[2/3] Identifying speakers...")
    venv_python = PIPELINE_DIR / "venv" / "Scripts" / "python.exe"
    diarize_script = SCRIPTS_DIR / "03_diarize.py"
    result = subprocess.run([str(venv_python), str(diarize_script), str(audio_path)])
    if result.returncode != 0:
        print(f"ERROR: diarization failed for {audio_path.name}. Leaving file in place for review.")
        return

    # Step 3: Merge
    print("\n[3/3] Merging transcript with speaker labels...")
    merge_script = SCRIPTS_DIR / "04_merge.py"
    result = subprocess.run([str(venv_python), str(merge_script), name])
    if result.returncode != 0:
        print(f"ERROR: merge failed for {audio_path.name}. Leaving file in place for review.")
        return

    # Step 4 (optional): Draft DAP note with local LLM via Ollama
    if AUTO_DRAFT_NOTE:
        speaker_transcript = PIPELINE_DIR / "transcripts" / f"{name}_speaker_transcript.txt"
        print("\n[4/4] Drafting DAP note with local AI (this is a DRAFT only)...")
        print("NOTE: this step uses the SPEAKER_00/SPEAKER_01 labels as-is unless")
        print("you've already renamed them. You can re-run 05_draft_note.py later")
        print("after renaming for a better draft.")
        draft_script = SCRIPTS_DIR / "05_draft_note.py"
        result = subprocess.run([str(venv_python), str(draft_script), name])
        if result.returncode != 0:
            print(f"WARNING: draft note generation failed for {name}. "
                  f"Transcript is still available; you can run "
                  f"05_draft_note.py manually later.")

    # Move the original recording to "processed" so it isn't reprocessed
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
    RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(exist_ok=True)

    print(f"Watching folder: {RECORDINGS_DIR}")
    print("Drop a new audio file in this folder to process it automatically.")
    print("Leave this window open. Press Ctrl+C to stop.\n")

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
