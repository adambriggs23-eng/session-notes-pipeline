# Session Notes Pipeline

A fully offline pipeline that turns a session audio recording into a
speaker-labelled transcript and a draft DAP progress note.

```
Recording (phone) -> Transcription (whisper.cpp) -> Speaker ID (pyannote)
                   -> Speaker-labelled transcript -> Draft DAP note (local AI)
```

Everything runs locally. No audio, transcripts, or notes are sent to any
cloud service at any point.

## Repository structure

```
session-notes-pipeline/
├── README.md              <- you are here
├── .gitignore              <- prevents client data from ever being committed
├── docs/
│   └── SETUP_GUIDE.md      <- full step-by-step setup instructions (Windows)
├── templates/
│   └── DAP_Note_Template.docx   <- blank DAP note template
└── scripts/
    ├── 00_watcher.py        <- watches the recordings folder, runs everything automatically
    ├── 02_transcribe.bat    <- transcribes audio with whisper.cpp
    ├── 03_diarize.py        <- identifies speakers (pyannote)
    ├── 04_merge.py          <- combines transcript + speaker labels
    └── 05_draft_note.py     <- drafts a DAP note with a local AI (Ollama)
```

Note: `01_setup.sh` and `02_transcribe.sh` (the Mac/Linux versions) are not
included here since this setup targets Windows - see `docs/SETUP_GUIDE.md`.

## Where this lives

This repository contains only code and a blank template - no client data.
The actual working pipeline (models, recordings, transcripts, notes) lives
on your external SSD, in a separate folder structure described in the setup
guide. You'll typically place a copy of this repo's `scripts/` and
`templates/` folders inside that pipeline folder (e.g.
`D:\session-pipeline\scripts\`, `D:\session-pipeline\templates\`).

## Getting started

Follow `docs/SETUP_GUIDE.md` from the beginning. It covers:

1. Installing required software (Git, CMake, Python, ffmpeg, etc.)
2. Setting up the folder structure on your external SSD
3. Building whisper.cpp and downloading models
4. Setting up speaker identification (pyannote)
5. Running a manual test
6. Setting up the automatic watcher
7. (Optional) Drafting notes with a local AI (Ollama)

## Important: this produces drafts, not finished notes

The output of `05_draft_note.py` is explicitly a **draft**. Every note must
be reviewed, verified against the transcript, and rewritten in your own
clinical voice before it becomes part of the client record - particularly
the Safety/Risk and Assessment sections, which require professional
judgment a local AI model cannot provide.

## Privacy and compliance

- Nothing in this pipeline is configured to send data off your machine
- You are responsible for ensuring your use of recording, AI drafting, and
  record-keeping complies with your professional body's code of ethics,
  your state/country's recording consent laws, and your data retention
  obligations
- Keep this repository **private** if hosted on GitHub
