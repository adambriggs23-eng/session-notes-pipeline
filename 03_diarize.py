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

Notes:
    - pyannote labels speakers generically (SPEAKER_00, SPEAKER_01, ...).
      It does not know which speaker is the client vs. the clinician - you
      assign that mapping after, based on listening to a short portion of
      the recording.
    - NUM_SPEAKERS = 2 assumes a 1:1 session. Change to 3+ for group/family
      sessions.
"""

import sys
import os
import json
from pathlib import Path

NUM_SPEAKERS = 2  # set to None to let pyannote estimate automatically

PIPELINE_DIR = Path(os.environ.get("PIPELINE_DIR", Path.home() / "session-pipeline"))
TRANSCRIPTS_DIR = PIPELINE_DIR / "transcripts"


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
            "NOTE: HF_TOKEN not set. This is only required the first time, to "
            "download the pretrained model. If the model is already cached "
            "locally, this should still work."
        )

    print("Loading pyannote speaker-diarization pipeline...")
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=hf_token,
    )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    pipeline.to(torch.device(device))
    print(f"Running diarization on device: {device}")

    kwargs = {}
    if NUM_SPEAKERS:
        kwargs["num_speakers"] = NUM_SPEAKERS

    diarization = pipeline(str(audio_path), **kwargs)

    segments = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        segments.append({
            "start": round(turn.start, 2),
            "end": round(turn.end, 2),
            "speaker": speaker,
        })

    with open(out_path, "w") as f:
        json.dump(segments, f, indent=2)

    speakers_found = sorted(set(s["speaker"] for s in segments))
    print(f"\nDone. {len(segments)} segments written to: {out_path}")
    print(f"Speakers detected: {speakers_found}")


if __name__ == "__main__":
    main()
