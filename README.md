# tagfix - Audio Metadata Editor

A command-line and interactive tool for batch editing and organizing audio metadata.
Supports FLAC, MP3, M4A, OGG, OPUS, WMA, and WAV formats using Mutagen.
Includes album cover embedding and lyrics management (embed/rename).

---

## Requirements

* Python 3.8 or later
* Tkinter
* Mutagen library
* Pillow library (for album cover handling)
* Optional: musicbrainzngs (for online album cover search)

Install dependencies via pip:
```bash
pip install mutagen pillow musicbrainzngs tk
```
Or via system package manager:

* Fedora:
  
  ```bash
  sudo dnf install python-mutagen python3-Pillow python-musicbrainzngs python3-tkinter

* Arch Linux / Manjaro:
  
  ```bash
  sudo pacman -S python-mutagen python-pillow python-musicbrainzngs tk

* Debian / Ubuntu:
  
  ```bash
  sudo apt install python3-mutagen python3-pil python-musicbrainzngs python3-tk
  
* Windows users just use ```pip```

  

---

## Usage
Clone the repository and run the script:
```bash
git clone https://github.com/ext4zu/tagfix.git
cd tagfix
python3 tagfix.py
```

### Steps

1. Enter the directory path containing your audio files.
2. Select which metadata fields to edit from the setup menu.

   * Includes: Cover, Lyrics, Title, Artist, Album, Album Artist, Genre, Date, Track Number, Disc Number, Comment.
3. For each tag, choose between:

   * Global edits: Apply a single value to all files.
   * Per-file edits: Manually enter values for each file.
4. Album Cover Options:

   * Search online via MusicBrainz.
   * Use a local image file (jpg, png, bmp, gif).
5. Lyrics Options:

   * Embed a lyrics file into audio metadata.
   * Rename lyrics file to match song filename.
   * Or do both.
6. Confirm to begin batch editing.

---

## Supported Tags

| Number | Tag         | Description       |
| ------ | ----------- | ----------------- |
| 1      | cover       | Album cover image |
| 2      | lyrics      | Song lyrics       |
| 3      | title       | Track title       |
| 4      | artist      | Artist name       |
| 5      | album       | Album title       |
| 6      | albumartist | Album artist      |
| 7      | genre       | Music genre       |
| 8      | date        | Release year/date |
| 9      | tracknumber | Track number      |
| 10     | discnumber  | Disc number       |
| 11     | comment     | User comment      |

---

## Album Cover Handling

* All embedded covers are resized to 500x500 px JPEG for compatibility with DAPs.
* Supports online search via MusicBrainz (requires musicbrainzngs).
* Supports local image files (jpg, jpeg, png, bmp, gif).
* Images are previewed in a popup window before embedding.
  

---

## Lyrics Management

* Can embed lyrics into audio metadata (supports .lrc or .txt files).
* Can rename lyrics files to match audio filenames (again for DAPs).
* Supports single or multiple files, with interactive selection.
* Search function allows filtering lyrics files by song title.

---

## Notes

* Automatically detects and loads supported audio formats.
* Invalid or unreadable files are skipped with a warning.
* Global edits apply to all files for selected tags.
* Per-file edits allow manual entry for each file individually.
* You can cancel or skip files at any point during editing.

---

## Exit

* Type e in the main menu to exit the application.
* Press Ctrl + C anytime to stop safely.

---
