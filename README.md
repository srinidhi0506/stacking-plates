# Stacking Plates

A small arcade-style stacking plates game built with **Python** and **Pygame**.

## Demo / Repo
Add your GitHub repo link here after uploading (example: `https://github.com/srinidhi0506/stacking-plates`).

## Features
- Multi-level gameplay with increasing difficulty (additional plates and stacks per level).
- Time-limited levels with countdown and timeout handling.
- Click-to-move plates between stacks (enforces smaller-on-larger rule).
- Undo (press `Z`) and Pause/Resume functionality.
- Local leaderboard saved to `leaderboard.txt` (top 8 entries).
- Sound effects for moves, wins, and timeouts; background music support.
- Simple, easy-to-read GUI using Pygame.

## Requirements
- Python 3.8+
- `pygame` (installed via `pip`)

## Install locally (Windows)
```powershell
# open PowerShell in the project folder
python -m venv venv
# Activate venv (PowerShell)
.\venv\Scripts\Activate.ps1
# If Activation policy blocks scripts, run PowerShell as admin once and:
# Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
pip install -r requirements.txt
```

## Run
Make sure the following files are present in the same folder as `stackingplates.py`:
- `background.mp3` (optional — if not present, music will be skipped)
- `move.wav`, `win.wav`, `timeout.wav` (optional sound effects)
- `leaderboard.txt` will be created automatically after the first run (if it does not exist)

Then run:
```bash
python stackingplates.py
```

## Recommended repo contents before pushing to GitHub
- `stackingplates.py` (your game)
- `README.md` (this file)
- `requirements.txt`
- `background.mp3`, `move.wav`, `win.wav`, `timeout.wav` (or exclude large audio files if needed)
- `leaderboard.txt` (optional to include; can be generated on run)
- `.gitignore` (ignore venv, cache files)

## README tips for GitHub page
- Add 1-2 screenshots or a short GIF of gameplay.
- Add short run instructions and a bullet list of key features (done above).
- Add a LICENSE (MIT is fine for student projects).

---
