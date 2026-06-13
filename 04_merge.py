#!/usr/bin/env python3
"""
04_merge.py

Combines the whisper.cpp transcript (with word-level timestamps) and the
pyannote diarization output (speaker turns) into a single readable
speaker-labelled transcript - ready to be used as input for note drafting.

Usage:
    python 04_merge.py <name>

    Where <name> matches the basename used in steps 02 and 03, e.g. if your
    recording was "session_2026-06-13.m4a", run:
        python 04_merge.py session_2026-06-13

Expects:
    transcripts/<name>.json                 (from 02_transcribe.sh, whisper --output-json-full)
    transcripts/<name>_diarization.json     (from 03_diarize.py)

Output:
    transcripts/<name>_speaker_transcript.txt
        A readable transcript like:

        [00:00:03] SPEAKER_00: How have you been since we last spoke?
        [00:00:08] SPEAKER_01: Honestly, this week has been pretty rough...

    After running this, open the .txt file and do a quick find/replace to
    rename SPEAKER_00 -> "Clinician" and SPEAKER_01 -> "Client" (or vice
    versa) based on listening to the start of the recording.
"""

import sys
import json
from pathlib import Path
import os

PIPELINE_DIR = Path(os.environ.get("PIPELINE_DIR", Path.home() / "session-pipeline"))
TRANSCRIPTS_DIR = PIPELINE_DIR / "transcripts"


def fmt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def find_speaker(t: float, segments):
    """Return the speaker label active at time t, or None."""
    for seg in segments:
        if seg["start"] <= t <= seg["end"]:
            return seg["speaker"]
    # fall back to nearest segment if t falls in a small gap
    best, best_dist = None, float("inf")
    for seg in segments:
        dist = min(abs(t - seg["start"]), abs(t - seg["end"]))
        if dist < best_dist:
            best, best_dist = seg["speaker"], dist
    return best


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <name>")
        sys.exit(1)

    name = sys.argv[1]
    whisper_json_path = TRANSCRIPTS_DIR / f"{name}.json"
    diarization_path = TRANSCRIPTS_DIR / f"{name}_diarization.json"
    out_path = TRANSCRIPTS_DIR / f"{name}_speaker_transcript.txt"

    if not whisper_json_path.exists():
        print(f"Missing: {whisper_json_path} (run 02_transcribe.sh first)")
        sys.exit(1)
    if not diarization_path.exists():
        print(f"Missing: {diarization_path} (run 03_diarize.py first)")
        sys.exit(1)

    with open(whisper_json_path) as f:
        whisper_data = json.load(f)
    with open(diarization_path) as f:
        diarization_segments = json.load(f)

    # whisper.cpp --output-json-full produces a "transcription" list of segments,
    # each with "offsets": {"from": ms, "to": ms} and "text"
    segments = whisper_data.get("transcription", [])
    if not segments:
        print("No transcription segments found in whisper JSON.")
        sys.exit(1)

    lines = []
    current_speaker = None
    current_text = []
    current_start = None

    for seg in segments:
        start_sec = seg["offsets"]["from"] / 1000.0
        text = seg["text"].strip()
        if not text:
            continue

        speaker = find_speaker(start_sec, diarization_segments) or "UNKNOWN"

        if speaker != current_speaker:
            if current_speaker is not None:
                lines.append(
                    f"[{fmt_time(current_start)}] {current_speaker}: {' '.join(current_text)}"
                )
            current_speaker = speaker
            current_text = [text]
            current_start = start_sec
        else:
            current_text.append(text)

    if current_speaker is not None:
        lines.append(
            f"[{fmt_time(current_start)}] {current_speaker}: {' '.join(current_text)}"
        )

    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Done. Speaker-labelled transcript written to: {out_path}")
    print("\nNext steps:")
    print("  1. Open the file and replace SPEAKER_00 / SPEAKER_01 with")
    print("     'Clinician' / 'Client' based on listening to the start of the recording.")
    print("  2. Review for any obvious transcription errors.")
    print("  3. Use the cleaned transcript as input when drafting the DAP note.")


if __name__ == "__main__":
    main()
