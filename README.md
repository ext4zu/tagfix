![Python](https://img.shields.io/badge/python-3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

# TagFix 

A modern, beautiful web-based audio metadata editor with Material You design.


## Features

- **Material You Design** - Beautiful, modern interface with light/dark mode
- **Metadata Editing** - Edit title, artist, album, genre, and more
- **File Renaming** - Rename audio files directly from the UI
- **Cover Art Management** - View, upload, and change album artwork
- **Format Conversion** - Convert audio files to WAV or FLAC
- **Recursive Scanning** - Scan entire music libraries with nested folders
- **Dark Mode** - Toggle between light and dark themes
- **Fast & Lightweight** - Minimal dependencies, runs locally

## Supported Formats

- MP3 (ID3v2)
- FLAC (Vorbis Comments)
- M4A/MP4 (iTunes-style)
- WAV
- OGG Vorbis

## Requirements

- **Python 3.7+**
- **FFmpeg** (optional, for audio conversion)

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/k44yn3/tagfix.git
cd tagfix

# (Optional but recommended) Create and activate a virtual environment
python -m venv .venv
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
# Windows (cmd.exe)
.\.venv\Scripts\activate.bat
# macOS / Linux
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### Installing FFmpeg (optional, for conversion features)

- Windows:
  - Option A (chocolatey):
    - Install Chocolatey if you don't have it: https://chocolatey.org/install
    - Then run (in an elevated Command Prompt or PowerShell):
      ```bash
      choco install ffmpeg -y
      ```
    - Ensure ffmpeg is available on PATH (restart terminal if needed).
  - Option B (manual):
    - Download a static build from https://ffmpeg.org/download.html#windows or https://www.gyan.dev/ffmpeg/builds/
    - Extract and add the `bin` folder to your PATH (System Properties → Environment Variables → Path → Edit).

- Ubuntu/Debian:
  ```bash
  sudo apt install ffmpeg
  ```

- Fedora:
  ```bash
  sudo dnf install ffmpeg
  ```

- macOS:
  ```bash
  brew install ffmpeg
  ```

### 2. Run the Application

**Web Interface (local):**
```bash
python app.py
```
Then open your browser to: **http://127.0.0.1:5000**

**Command Line (Classic):**
```bash
python tagfix.py
```

## Usage

1. **Enter a folder path** in the input field (e.g., `/home/user/Music` or `C:\Users\YourName\Music`)
2. **Click Scan** to load all audio files
3. **Edit metadata** directly in the cards
4. **Upload cover art** by clicking "Change Cover"
5. **Rename files** using the filename field
6. **Click Save All** to apply changes
7. **Convert files** using the Convert button

## Screenshots

### Light Mode
![Light Mode](https://github.com/k44yn3/tagfix/blob/c9decf1d492c8e0358754f652e131b4ac7dd603a/screenshots/LightMode.png)

### Dark Mode
![Dark Mode](https://github.com/k44yn3/tagfix/blob/a1191ea1444fbb861beb63ac92d0673360ed705c/screenshots/DarkMode.png)


## Technology Stack

- **Backend:** Flask (Python)
- **Frontend:** Vanilla JavaScript, HTML5, CSS3
- **Design:** Material Design 3 (Material You)
- **Audio Processing:** Mutagen, FFmpeg
- **Image Processing:** Pillow (PIL)

## Dependencies

```
Flask>=3.0.0
mutagen>=1.47.0
Pillow>=10.0.0
requests>=2.31.0
```

## Contributing

Contributions are welcome! Feel free to:

- Report bugs
- Suggest new features
- Submit pull requests

## License

MIT License - See [LICENSE](LICENSE) file for details
