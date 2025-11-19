
![Python](https://img.shields.io/badge/python-3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

# TagFix 

A modern, beautiful web-based audio metadata editor with Material You design.

![TagFix Interface](https://via.placeholder.com/800x450/6750A4/FFFFFF?text=TagFix+Material+You+Interface)

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
git clone https://github.com/yourusername/tagfix.git
cd tagfix

# Install Python dependencies
pip install -r requirements.txt

# (Optional) Install FFmpeg for conversion features
# Ubuntu/Debian:
sudo apt install ffmpeg

# Fedora:
sudo dnf install ffmpeg

# macOS:
brew install ffmpeg
```

### 2. Run the Application

**Web Interface:**
```bash
python3 app.py
```
Then open your browser to: **http://127.0.0.1:5000**

**Command Line (Classic):**
```bash
python3 tagfix.py
```

## 📖 Usage

1. **Enter a folder path** in the input field (e.g., `/home/user/Music`)
2. **Click Scan** to load all audio files
3. **Edit metadata** directly in the cards
4. **Upload cover art** by clicking "Change Cover"
5. **Rename files** using the filename field
6. **Click Save All** to apply changes
7. **Convert files** using the Convert button

## Screenshots

### Light Mode
![Light Mode](https://via.placeholder.com/800x450/FFFBFE/1C1B1F?text=Light+Mode)

### Dark Mode
![Dark Mode](https://via.placeholder.com/800x450/1C1B1F/E6E1E5?text=Dark+Mode)

### Editing Metadata
![Editing](https://via.placeholder.com/800x450/EADDFF/21005D?text=Metadata+Editing)

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

## Acknowledgments

- Material Design 3 by Google
- Mutagen library for audio metadata handling
- Flask framework for the web backend

## Contact

For questions or support, please open an issue on GitHub.

---
