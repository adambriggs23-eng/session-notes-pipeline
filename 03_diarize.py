#!/usr/bin/env python3
"""
03_diarize.py  (Windows version)

Performs speaker diarization (identifying "who spoke when") using
pyannote.audio, fully offline after the initial one-time model download.

Usage (from the pipeline folder, with the venv activated):
    python 03_diarize.py "D:\\session-pipeline\\recordings\\session1.m4a"

Output:
    transcripts\\<name>_diarization.json
        A list of segments: [{"start": 0.0, "end": 4.2, "speaker": "SPEAKER_00"}, ...]

Environment variables:
    HF_TOKEN        - Hugging Face token (required on first run for model download)
    NUM_SPEAKERS    - Number of speakers to identify (default: 2). Set to None to auto-detect.

Notes:
    - pyannote labels speakers generically (SPEAKER_00, SPEAKER_01, ...).
      It does not know which speaker is the client vs. the clinician - you
      assign that mapping after, based on listening to a short portion of
      the recording.
    - For group/family sessions with 3+ speakers, set NUM_SPEAKERS=3 (etc.)
      before running.
"""

import sys
import os
import json
from pathlib import Path

PIPELINE_DIR = Path(os.environ.get("PIPELINE_DIR", Path.home() / "session-pipeline"))
TRANSCRIPTS_DIR = PIPELINE_DIR / "transcripts"

# Number of speakers to identify. Set via environment variable or default.
NUM_SPEAKERS = None
num_speakers_env = os.environ.get("NUM_SPEAKERS")
if num_speakers_env and num_speakers_env.lower() != "none":
    try:
        NUM_SPEAKERS = int(num_speakers_env)
    except ValueError:
        print(f"WARNING: NUM_SPEAKERS='{num_speakers_env}' is not a valid integer. Using auto-detect.")


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} \"path\\to\\recording.m4a\"")
        sys.exit(1)

    audio_path = Path(sys.argv[1])
    if not audio_path.exists():
        print(f"File not found: {audio_path}")
        sys.exit(1)

    name = audio_path.stem
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = TRANSCRIPTS_DIR / f"{name}_diarization.json"

    from pyannote.audio import Pipeline
    import torch

    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        print(
            "ERROR: HF_TOKEN environment variable not set.\n"
            "This is required to download the speaker identification model on first run.\n\n"
            "Set it with: set HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx\n\n"
            "You can get a token from: https://huggingface.co/settings/tokens\n"
            "(Make sure you've accepted the terms at https://huggingface.co/pyannote/speaker-diarization-3.1)"
        )
        sys.exit(1)

    print("Loading pyannote speaker-diarization pipeline...")
    try:
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=hf_token,
        )
    except Exception as e:
        print(f"ERROR: Failed to load pyannote pipeline: {e}")
        print("\nPossible causes:")
        print("  - HF_TOKEN is invalid or expired")
        print("  - You haven't accepted the terms at https://huggingface.co/pyannote/speaker-diarization-3.1")
        print("  - Network connection issue")
        sys.exit(1)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    pipeline.to(torch.device(device))
    print(f"Running diarization on device: {device}")
    if NUM_SPEAKERS:
        print(f"Identifying {NUM_SPEAKERS} speakers")
    else:
        print("Auto-detecting number of speakers")

    kwargs = {}
    if NUM_SPEAKERS:
        kwargs["num_speakers"] = NUM_SPEAKERS

    try:
        diarization = pipeline(str(audio_path), **kwargs)
    except Exception as e:
        print(f"ERROR: Diarization failed: {e}")
        sys.exit(1)

    segments = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        segments.append({
            "start": round(turn.start, 2),
            "end": round(turn.end, 2),
            "speaker": speaker,
        })

    if not segments:
        print("ERROR: No speaker segments detected. Audio may be empty or too short.")
        sys.exit(1)

    with open(out_path, "w") as f:
        json.dump(segments, f, indent=2)

    speakers_found = sorted(set(s["speaker"] for s in segments))
    print(f"\nDone. {len(segments)} segments written to: {out_path}")
    print(f"Speakers detected: {speakers_found}")


if __name__ == "__main__":
    main()
