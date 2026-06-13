# Complete Setup Guide
## Offline session recording -> automatic transcription pipeline
### For Windows (Lenovo Yoga) + external SSD

This guide assumes no prior technical experience. Follow the steps in order.
Set aside about 1-2 hours for the one-time setup (mostly waiting for
downloads and installations).

Where you see `D:\`, that refers to your external SSD's drive letter.
**Check your actual drive letter first**: plug in the SSD, open "This PC"
in File Explorer, and see what letter Windows assigned it (often D, E, or
F). Replace `D:\` everywhere below with your actual letter.

---

## Part 1: Install the required programs

You'll install five things. All are free and from official sources.

### 1.1 Git
Used to download whisper.cpp's source code.

1. Go to https://git-scm.com/download/win
2. Download will start automatically. Run the installer.
3. Click "Next" through all screens, accepting the defaults. Click "Install".

### 1.2 CMake
Used to build whisper.cpp.

1. Go to https://cmake.org/download/
2. Under "Binary distributions", download the **Windows x64 Installer** (.msi)
3. Run the installer.
4. **Important**: on the "Install Options" screen, select **"Add CMake to the system PATH for all users"**
5. Continue with defaults and finish.

### 1.3 Visual Studio Build Tools (C++ compiler)
Needed to compile whisper.cpp.

1. Go to https://visualstudio.microsoft.com/downloads/
2. Scroll to "Tools for Visual Studio" and download **"Build Tools for Visual Studio"**
3. Run the installer. When the installer window opens, check the box for
   **"Desktop development with C++"**
4. Click "Install" (this is a large download, ~6-7 GB, may take a while)
5. Restart your computer when it finishes.

### 1.4 Python
Used for the speaker-identification and automation scripts.

1. Go to https://www.python.org/downloads/
2. Click the big "Download Python 3.x.x" button
3. Run the installer
4. **Important**: on the first screen, check the box at the bottom that says
   **"Add python.exe to PATH"** before clicking "Install Now"

### 1.5 ffmpeg (audio conversion tool)
1. Go to https://www.gyan.dev/ffmpeg/builds/
2. Under "release builds", download **ffmpeg-release-essentials.zip**
3. Once downloaded, right-click the zip file and choose "Extract All"
4. Extract it directly to `D:\session-pipeline\ffmpeg` on your SSD
   (you'll create the `session-pipeline` folder in Part 2 - if it doesn't
   exist yet, create it now)
5. After extracting, you should have a folder structure like
   `D:\session-pipeline\ffmpeg\ffmpeg-7.x-essentials_build\bin\ffmpeg.exe`
6. Rename that inner folder (the long one with version numbers) to just `bin`,
   so the path becomes `D:\session-pipeline\ffmpeg\bin\ffmpeg.exe`
   - To rename: navigate into `D:\session-pipeline\ffmpeg`, right-click the
     long folder name, choose "Rename", type `bin`, press Enter
   - If there's already an empty `ffmpeg` folder wrapping it, move the `bin`
     folder up one level so the final path is exactly
     `D:\session-pipeline\ffmpeg\bin\ffmpeg.exe`

---

## Part 2: Set up the folder structure

1. Open File Explorer, go to your external SSD (e.g. `D:\`)
2. Create a new folder called `session-pipeline`
3. Inside `D:\session-pipeline`, create these folders:
   - `recordings`
   - `transcripts`
   - `notes`
   - `scripts`
   - `templates`

You should now have:
```
D:\session-pipeline\
    ffmpeg\bin\ffmpeg.exe
    recordings\
    transcripts\
    notes\
    scripts\
    templates\
```

---

## Part 3: Set a permanent environment variable

This tells all the scripts where your pipeline folder lives, so you don't
have to type the full path every time.

1. Press the **Windows key**, type `environment variables`, and click
   **"Edit environment variables for your account"**
2. In the top box ("User variables"), click **"New..."**
3. Variable name: `PIPELINE_DIR`
4. Variable value: `D:\session-pipeline`
5. Click OK, then OK again to close.

**Restart your computer now** so this takes effect everywhere.

---

## Part 4: Get the pipeline scripts

These files live in the `session-notes-pipeline` GitHub repository
(`scripts/` and `templates/` folders).

If you're comfortable with GitHub Desktop or `git`, clone the repository.
Otherwise, the simplest approach:

1. On the GitHub repository page, click the green **"Code"** button, then
   **"Download ZIP"**
2. Once downloaded, right-click the zip file and choose "Extract All"
3. Open the extracted folder. You should see `scripts/`, `templates/`,
   `docs/`, `README.md`, and `.gitignore`

Now copy the contents into your pipeline folder on the SSD:

1. Copy everything inside the repo's `scripts/` folder
   (`00_watcher.py`, `02_transcribe.bat`, `03_diarize.py`, `04_merge.py`,
   `05_draft_note.py`) into `D:\session-pipeline\scripts\`
2. Copy `templates\DAP_Note_Template.docx` into
   `D:\session-pipeline\templates\` (create this folder if it doesn't exist)

You can delete the extracted ZIP folder afterward - the working copies are
now on your SSD.

---

## Part 5: Build whisper.cpp

1. Open the **Start Menu**, type `cmd`, and open **Command Prompt**
2. Type the following commands one at a time, pressing Enter after each
   and waiting for it to finish before typing the next:

```
D:
cd session-pipeline
git clone https://github.com/ggerganov/whisper.cpp.git
cd whisper.cpp
cmake -B build
cmake --build build --config Release
```

The last step (`cmake --build`) takes the longest - it may run for
10-20 minutes. Wait until you see the command prompt return to a normal
line (e.g. `D:\session-pipeline\whisper.cpp>`) before continuing.

3. Now download the speech-recognition model. Still in the same window, type:

```
cd models
download-ggml-model.cmd large-v3
```

This downloads ~3 GB and may take a while depending on your internet speed.

---

## Part 6: Set up Python environment for speaker identification

1. In the same Command Prompt window, type:

```
cd D:\session-pipeline
python -m venv venv
venv\Scripts\activate
```

You should now see `(venv)` at the start of the line.

2. Now install the required packages:

```
pip install --upgrade pip
pip install pyannote.audio torch torchaudio watchdog
```

This will take several minutes and download a few GB of data.

---

## Part 7: Get a free Hugging Face account & token

pyannote (the speaker-identification tool) needs you to accept its usage
terms once, via a free account.

1. Go to https://huggingface.co and click "Sign Up" (free)
2. Once logged in, go to https://huggingface.co/pyannote/speaker-diarization-3.1
3. Click "Agree and access repository" (you may need to fill in a short form)
4. Go to https://huggingface.co/pyannote/segmentation-3.0 and do the same
   ("Agree and access repository")
5. Now go to https://huggingface.co/settings/tokens
6. Click "New token", give it any name (e.g. "pipeline"), choose "Read" access,
   click "Create token"
7. **Copy the token** - it starts with `hf_`. You'll need it for the next step.

---

## Part 8: First test run

This is where everything comes together. We'll do one manual test before
setting up full automation.

### 8.1 Get a test recording onto the SSD

1. Connect your phone to the laptop with a USB cable
2. On your phone, if prompted, allow "File Transfer" mode
3. In File Explorer on your laptop, find your phone, navigate to where your
   voice recordings are saved (often a "Recordings" or "Voice Recorder" folder)
4. Copy one short test recording (under 1 minute is fine for testing) to
   `D:\session-pipeline\recordings\`

### 8.2 Run transcription

In your Command Prompt window (with `(venv)` still showing), type:

```
cd D:\session-pipeline\scripts
02_transcribe.bat "D:\session-pipeline\recordings\YOUR_FILE_NAME.m4a"
```

Replace `YOUR_FILE_NAME.m4a` with the actual filename. This may take a
few minutes the first time.

When done, check `D:\session-pipeline\transcripts\` - you should see a
`.txt` file and a `.json` file with the same name as your recording.

### 8.3 Run speaker identification

Still in the same window, type (replacing the token with the one you copied):

```
set HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx
python 03_diarize.py "D:\session-pipeline\recordings\YOUR_FILE_NAME.m4a"
```

This downloads the diarization model the first time (a few hundred MB),
then runs. You should see a `_diarization.json` file appear in
`transcripts\`.

### 8.4 Merge into a readable transcript

```
python 04_merge.py YOUR_FILE_NAME
```

(Use the filename **without** the extension, e.g. just `session1` not
`session1.m4a`)

Check `D:\session-pipeline\transcripts\` for a file ending in
`_speaker_transcript.txt`. Open it - you should see lines like:

```
[00:00:03] SPEAKER_00: How have you been since we last spoke?
[00:00:08] SPEAKER_01: Honestly, this week has been pretty rough...
```

Listen to the first minute of your recording and figure out which speaker
number is you and which is the client, then use Find & Replace (Ctrl+H in
Notepad) to swap `SPEAKER_00`/`SPEAKER_01` for `Clinician`/`Client`.

If all of this worked - **you're ready to automate it.**

---

## Part 9: Set up automatic processing

Now we'll set up the watcher so you never need to type commands again.
You just copy a recording into the `recordings` folder and everything
happens by itself.

### 9.1 Create a simple start-up shortcut

1. Open Notepad
2. Type the following exactly:

```
@echo off
set PIPELINE_DIR=D:\session-pipeline
set HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx
call D:\session-pipeline\venv\Scripts\activate.bat
python D:\session-pipeline\scripts\00_watcher.py
pause
```

3. Replace `hf_xxxxxxxxxxxxxxxxxxxx` with your actual Hugging Face token
   from Part 7
4. Save the file as `Start_Pipeline.bat` (in Notepad's Save dialog, set
   "Save as type" to "All Files" and make sure the filename ends in `.bat`,
   not `.txt`) - save it to `D:\session-pipeline\`

### 9.2 Run it

1. Double-click `Start_Pipeline.bat`
2. A black window will open and say "Watching folder: D:\session-pipeline\recordings"
3. **Leave this window open** while you work. Minimize it if you like, but
   don't close it.

### 9.3 Use it

Whenever you have a new recording:
1. Plug in your phone, copy the audio file into `D:\session-pipeline\recordings\`
2. Within a few seconds, the black window will show it's been detected and
   start processing automatically
3. When done, your speaker-labelled transcript appears in
   `D:\session-pipeline\transcripts\`
4. The original recording is automatically moved to
   `D:\session-pipeline\recordings\processed\` so it won't be processed again

You can then open `D:\session-pipeline\templates\DAP_Note_Template.docx`
and use the transcript to write your session note.

---

## Day-to-day summary (once everything is set up)

1. Double-click `Start_Pipeline.bat` (leave the window open)
2. Plug in phone -> copy new recording(s) into `recordings` folder
3. Wait for processing to finish (a few minutes per recording)
4. Open the `_speaker_transcript.txt` file, do the Clinician/Client
   find-and-replace
5. Use it alongside `templates\DAP_Note_Template.docx` to write your note
6. Delete the recording from your phone once confirmed copied

---

## If something goes wrong

- **"git is not recognized" / "cmake is not recognized" / "python is not recognized"**:
  the program wasn't added to PATH, or you haven't restarted your computer
  since installing. Restart and try again.
- **The build step fails with compiler errors**: confirm Visual Studio Build
  Tools installed with "Desktop development with C++" checked, and restart.
- **pyannote download fails / "access denied"**: double check you accepted
  the terms on **both** Hugging Face model pages in Part 7, and that your
  `HF_TOKEN` is correct (no extra spaces).
- **Transcription is slow**: this is normal on a laptop CPU - a 50-minute
  session might take 15-30+ minutes to transcribe with the `large-v3` model.
  If it's too slow, you can switch to a smaller model (edit
  `02_transcribe.bat` and `00_watcher.py` references, changing `large-v3`
  to `medium`, then re-run the download command from Part 5 step 3 with
  `medium` instead of `large-v3`). Smaller = faster but less accurate.
- **Nothing happens when I copy a file in**: make sure the watcher window
  (`Start_Pipeline.bat`) is still open and running, and that the file
  extension is one of `.wav .m4a .mp3 .aac .ogg .flac`.

---

## Part 10 (Optional): Auto-draft the DAP note with a local AI

This adds one more step: after you have the speaker-labelled transcript,
a local AI model reads it and writes a **draft** DAP note into a Word
document. You then review and rewrite it - this is explicitly a starting
point, not a finished note.

### 10.1 Install Ollama (runs the AI model locally)

1. Go to https://ollama.com/download
2. Download and run the Windows installer (defaults are fine)
3. Once installed, open Command Prompt and type:

```
ollama pull llama3.1:8b
```

This downloads the model (~4.7 GB), one-time only. Wait for it to finish.

4. Test it's working:

```
ollama run llama3.1:8b
```

Type a test message like "hello", confirm you get a response, then type
`/bye` to exit.

### 10.2 Install one more Python package

```
cd D:\session-pipeline
venv\Scripts\activate
pip install python-docx
```

### 10.3 Confirm the drafting script is in place

`05_draft_note.py` should already be in `D:\session-pipeline\scripts\` if you
copied the full `scripts\` folder from the repo in Part 4. If it's missing,
go back to the repo and copy it across now.

### 10.4 Generate a draft note

After you've run the pipeline (Parts 8/9) and renamed `SPEAKER_00`/`SPEAKER_01`
to `Clinician`/`Client` in the transcript file, run:

```
cd D:\session-pipeline\scripts
python 05_draft_note.py YOUR_FILE_NAME
```

(again, no file extension - e.g. `session1` not `session1.m4a`)

This will take a few minutes. When done, open
`D:\session-pipeline\notes\YOUR_FILE_NAME_DRAFT.docx`

### 10.5 What to do with the draft

The draft document has a red banner reminding you it's AI-generated. Before
this becomes a real clinical note:

- **Read the whole transcript yourself** alongside the draft - don't rely on
  the AI's summary alone
- **Rewrite the Safety/Risk section yourself** based on your own assessment
  of the transcript - this is the highest-stakes section and the local model
  is the least reliable here
- **Add your clinical judgment** to the Assessment section - prognosis,
  diagnostic considerations, and interpretation are deliberately left for you
- **Verify every quoted statement** against the transcript for accuracy
- **Rewrite in your own clinical voice** - an unedited AI draft filed as-is
  is the same "cloned note" compliance problem as copy-pasting between
  sessions, just with a different source

### 10.6 (Optional) Fully automatic drafting

If you'd rather have the draft generated automatically every time, without
running step 10.4 manually:

1. Open `00_watcher.py` in Notepad
2. Find the line `AUTO_DRAFT_NOTE = False`
3. Change it to `AUTO_DRAFT_NOTE = True`
4. Save the file

Note that this will use whatever speaker labels exist at that point
(possibly still `SPEAKER_00`/`SPEAKER_01` if you haven't renamed them yet) -
the draft will be less useful in that case, but you can always re-run
`05_draft_note.py` manually afterward once you've done the rename.

### Troubleshooting Part 10

- **"could not reach Ollama"**: make sure Ollama is installed and has run at
  least once (it runs as a background service after installation - try
  restarting your computer if it's not responding)
- **Drafting is very slow**: an 8B model on a laptop CPU can take several
  minutes per section (3 sections per note). This is expected. If it's too
  slow, a smaller model like `llama3.1:8b` is already a reasonably small
  choice - going smaller (e.g. `mistral:7b`) won't help much and may reduce
  quality further
- **Output looks generic or misses things**: this is the expected limitation
  of a small local model - treat it as a rough first pass, not a substitute
  for writing the note yourself

---

## Appendix: Putting this on GitHub (private repository)

This is optional - it's just a way to keep a backup of the scripts and
template, and to track changes over time. None of your client data ever
goes here; only the code and the blank template.

### A.1 Create a GitHub account (if you don't have one)

Go to https://github.com and sign up (free).

### A.2 Create a new private repository

1. Click the **"+"** in the top right, then **"New repository"**
2. Name it something like `session-notes-pipeline`
3. **Set visibility to "Private"** - this is important
4. Leave "Initialize with a README" unchecked if you already have the files
   from this project; check it if starting empty
5. Click "Create repository"

### A.3 Upload the files (easiest method - no command line)

1. On your new repository's page, click **"uploading an existing file"**
   (or "Add file" -> "Upload files")
2. Drag in the folders: `scripts/`, `templates/`, `docs/`, plus `README.md`
   and `.gitignore` from the project files provided
3. Scroll down and click **"Commit changes"**

### A.4 Keeping it updated

If I (or you) make changes to any script later:
1. Go to the file on GitHub, click the pencil ("Edit") icon, paste in the
   updated content, and commit
2. Or delete the old file and re-upload the new version via "Add file" ->
   "Upload files"

### A.5 Getting files onto your laptop

Whenever you need a fresh copy on your Lenovo (e.g. after the laptop is
reset, or you're setting up a second machine):
1. Go to the repository page
2. Click the green **"Code"** button -> **"Download ZIP"**
3. Extract and copy `scripts/` and `templates/` contents into
   `D:\session-pipeline\` as described in Part 4

### A.6 Double-check before every upload

Before uploading or committing anything, glance through what you're about
to upload and confirm there are no:
- Audio files (`.wav`, `.m4a`, `.mp3`, etc.)
- Transcript files (`.txt` files with session content)
- `.docx` files other than the blank `DAP_Note_Template.docx`

The `.gitignore` file helps prevent these being added if you ever use the
command-line `git` tool, but the upload-via-website method doesn't check
this automatically - so a quick visual check before clicking "Commit
changes" is good practice.
