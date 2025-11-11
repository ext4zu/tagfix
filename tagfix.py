#!/usr/bin/env python3
"""
Audio Metadata Editor - Complete Version
Supports FLAC, MP3, M4A, OGG, OPUS, WMA, and WAV formats.
Includes Album Cover (option 1) with online/local selection and popup preview.
"""
import os
import sys
import tempfile
import requests
from PIL import Image, ImageTk
import tkinter as tk
from mutagen.flac import FLAC, Picture
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4, MP4Cover
from mutagen.oggvorbis import OggVorbis
from mutagen.oggopus import OggOpus
from mutagen.wave import WAVE
from mutagen.asf import ASF
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TPE2, TCON, TDRC, TRCK, TPOS, COMM, APIC
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

try:
    import musicbrainzngs
    musicbrainzngs.set_useragent("AudioMetadataEditor", "1.0", "")
except ImportError:
    print("Warning: musicbrainzngs not installed. Online cover fetch will not work.")

# ===================== SETTINGS =====================
AVAILABLE_TAGS = {
    "1": "cover",
    "2": "lyrics",
    "3": "title",
    "4": "artist",
    "5": "album",
    "6": "albumartist",
    "7": "genre",
    "8": "date",
    "9": "tracknumber",
    "10": "discnumber",
    "11": "comment"
}

GLOBAL_TAGS = {"artist", "albumartist", "album", "date", "genre"}
SUPPORTED_EXTENSIONS = {'.flac', '.mp3', '.m4a', '.ogg', '.opus', '.wma', '.wav'}

ID3_TAG_MAP = {
    'title': TIT2,
    'artist': TPE1,
    'album': TALB,
    'albumartist': TPE2,
    'genre': TCON,
    'date': TDRC,
    'tracknumber': TRCK,
    'discnumber': TPOS,
    'comment': COMM
}

MP4_TAG_MAP = {
    'title': '\xa9nam',
    'artist': '\xa9ART',
    'album': '\xa9alb',
    'albumartist': 'aART',
    'genre': '\xa9gen',
    'date': '\xa9day',
    'tracknumber': 'trkn',
    'discnumber': 'disk',
    'comment': '\xa9cmt'
}

# ===================== AUDIO UTILITIES =====================
def find_audio_files(base_dir: str) -> List[str]:
    base_dir = os.path.expanduser(base_dir.strip().strip('"').strip("'"))
    if not os.path.exists(base_dir):
        print(f"Error: Directory '{base_dir}' does not exist.")
        return []
    if not os.path.isdir(base_dir):
        print(f"Error: '{base_dir}' is not a directory.")
        return []
    audio_files = []
    for root, _, files in os.walk(base_dir):
        for file in files:
            if os.path.splitext(file.lower())[1] in SUPPORTED_EXTENSIONS:
                audio_files.append(os.path.join(root, file))
    return sorted(audio_files)

def load_audio_file(filepath: str):
    ext = os.path.splitext(filepath.lower())[1]
    try:
        if ext == '.flac':
            return FLAC(filepath)
        elif ext == '.mp3':
            return MP3(filepath)
        elif ext == '.m4a':
            return MP4(filepath)
        elif ext == '.ogg':
            return OggVorbis(filepath)
        elif ext == '.opus':
            return OggOpus(filepath)
        elif ext == '.wma':
            return ASF(filepath)
        elif ext == '.wav':
            return WAVE(filepath)
    except Exception as e:
        print(f"Error loading file: {e}")
        return None
    return None

def get_tag_value(audio, tag: str, filepath: str) -> Optional[str]:
    ext = os.path.splitext(filepath.lower())[1]
    try:
        if ext in ('.mp3', '.wav'):
            if not hasattr(audio, 'tags') or audio.tags is None:
                return None
            tag_class = ID3_TAG_MAP.get(tag)
            if tag_class and tag_class.__name__ in audio.tags:
                return str(audio.tags[tag_class.__name__].text[0])
            return None
        elif ext == '.m4a':
            mp4_tag = MP4_TAG_MAP.get(tag)
            if mp4_tag and mp4_tag in audio.tags:
                value = audio.tags[mp4_tag]
                if tag in ('tracknumber', 'discnumber'):
                    return str(value[0][0]) if value and value[0] else None
                return str(value[0]) if value else None
            return None
        else:
            if tag in audio:
                return str(audio[tag][0]) if audio[tag] else None
            return None
    except Exception:
        return None

def set_tag_value(audio, tag: str, value: str, filepath: str) -> bool:
    ext = os.path.splitext(filepath.lower())[1]
    try:
        if ext in ('.mp3', '.wav'):
            if not hasattr(audio, 'tags') or audio.tags is None:
                audio.add_tags()
            tag_class = ID3_TAG_MAP.get(tag)
            if tag_class:
                if tag == 'comment':
                    audio.tags[tag_class.__name__] = tag_class(encoding=3, lang='eng', desc='', text=value)
                else:
                    audio.tags[tag_class.__name__] = tag_class(encoding=3, text=value)
            elif tag == 'lyrics':
                from mutagen.id3 import USLT
                audio.tags['USLT::eng'] = USLT(encoding=3, lang='eng', desc='', text=value)
            return True
        elif ext == '.m4a':
            mp4_tag = MP4_TAG_MAP.get(tag)
            if mp4_tag:
                if tag in ('tracknumber', 'discnumber'):
                    audio.tags[mp4_tag] = [(int(value), 0)]
                else:
                    audio.tags[mp4_tag] = [value]
            elif tag == 'lyrics':
                audio.tags['\xa9lyr'] = [value]
            return True
        else:
            if tag == 'lyrics':
                audio['lyrics'] = [value]
            else:
                audio[tag] = [value]
            return True
    except Exception as e:
        print(f"  Warning: Could not set {tag}: {e}")
        return False

# ===================== METADATA ANALYSIS =====================
def analyze_metadata(audio_files: List[str], selected_tags: List[str]) -> Dict[str, Dict]:
    metadata_map = defaultdict(lambda: defaultdict(list))
    for filepath in audio_files:
        audio = load_audio_file(filepath)
        if audio is None:
            continue
        filename = os.path.basename(filepath)
        for tag in selected_tags:
            value = get_tag_value(audio, tag, filepath)
            metadata_map[tag][value if value else "[Not Set]"].append(filename)
    return metadata_map

def display_metadata_analysis(metadata_map: Dict[str, Dict], tag: str, audio_files: List[str]) -> None:
    print(f"\nCurrent {tag.title()} Values:")
    print("-" * 60)
    tag_data = metadata_map.get(tag, {})
    if not tag_data:
        print("  No metadata found")
        return
    sorted_values = sorted(tag_data.items(), key=lambda x: (x[0] == "[Not Set]", x[0]))
    for value, files in sorted_values:
        count = len(files)
        total = len(audio_files)
        percentage = (count / total * 100) if total > 0 else 0
        print(f"  '{value}' - {count} file(s) ({percentage:.1f}%)")
        if count <= 3:
            for f in files:
                print(f"    - {f}")
        else:
            for f in files[:2]:
                print(f"    - {f}")
            print(f"    ... and {count - 2} more")

# ===================== ALBUM COVER FUNCTIONS =====================
def fetch_cover_musicbrainz(artist: str, album: str) -> Optional[str]:
    """Fetch album cover from MusicBrainz and save to temp file."""
    try:
        # Search for the release
        results = musicbrainzngs.search_releases(artist=artist, release=album, limit=1)
        if not results.get('release-list'):
            print("No releases found on MusicBrainz.")
            return None
        
        # Get the MusicBrainz ID
        mbid = results['release-list'][0]['id']
        print(f"Found release: {results['release-list'][0].get('title', 'Unknown')}")
        
        # Get cover art
        try:
            image_info = musicbrainzngs.get_image_list(mbid)
        except musicbrainzngs.ResponseError:
            print("No cover art available for this release.")
            return None
        
        if not image_info.get('images'):
            print("No images found in cover art archive.")
            return None
        
        # Download the cover image
        image_url = image_info['images'][0]['image']
        print(f"Downloading cover from: {image_url}")
        
        resp = requests.get(image_url, timeout=10)
        if resp.status_code != 200:
            print(f"Failed to download image. Status code: {resp.status_code}")
            return None
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        temp_file.write(resp.content)
        temp_file.close()
        
        print("Cover downloaded successfully!")
        return temp_file.name
        
    except Exception as e:
        print(f"Error fetching cover: {e}")
        return None

def show_image_popup(image_path: str):
    img = Image.open(image_path).convert("RGB")
    original_width, original_height = img.size
    
    # Smart scaling: fit to screen while maintaining aspect ratio
    max_width = 1200
    max_height = 900
    
    # Calculate scaling factor
    scale_w = max_width / original_width if original_width > max_width else 1
    scale_h = max_height / original_height if original_height > max_height else 1
    scale = min(scale_w, scale_h)
    
    # Only downscale if image is too large
    if scale < 1:
        new_width = int(original_width * scale)
        new_height = int(original_height * scale)
        display_img = img.resize((new_width, new_height), Image.LANCZOS)
    else:
        display_img = img
    
    root = tk.Tk()
    root.title(f"Album Cover Preview - {original_width}x{original_height}px")
    
    # Window size adapts to image size (with padding)
    window_width = min(display_img.width + 20, max_width)
    window_height = min(display_img.height + 20, max_height)
    
    canvas = tk.Canvas(root, width=window_width, height=window_height)
    hbar = tk.Scrollbar(root, orient=tk.HORIZONTAL, command=canvas.xview)
    vbar = tk.Scrollbar(root, orient=tk.VERTICAL, command=canvas.yview)
    canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
    
    # Only show scrollbars if needed
    if display_img.width > window_width:
        hbar.pack(side=tk.BOTTOM, fill=tk.X)
    if display_img.height > window_height:
        vbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    tk_img = ImageTk.PhotoImage(display_img)
    canvas.create_image(0, 0, anchor="nw", image=tk_img)
    canvas.config(scrollregion=(0, 0, display_img.width, display_img.height))
    canvas.image = tk_img
    
    root.update()
    return root, img

def process_album_cover(audio_folder: str):
    audio_files = find_audio_files(audio_folder)
    if not audio_files:
        print("No audio files found in the folder.")
        return
    
    first_audio = load_audio_file(audio_files[0])
    album = get_tag_value(first_audio, 'album', audio_files[0]) or ""
    artist = get_tag_value(first_audio, 'artist', audio_files[0]) or ""
    
    print(f"\nAlbum detected: {album}")
    print(f"Artist detected: {artist}\n")
    print("Choose album cover source:")
    print("  [1] Search online (MusicBrainz)")
    print("  [2] Provide local image file")
    print("  [b] Back to setup menu")
    
    while True:
        choice = input("\nYour choice: ").strip().lower()
        if choice in ('1', '2', 'b'):
            break
    
    if choice == 'b':
        return
    
    cover_path = None
    
    if choice == '1':
        if 'musicbrainzngs' not in sys.modules:
            print("MusicBrainz module not available. Switching to local image.")
            choice = '2'
        else:
            print("Searching online for album cover...")
            cover_path = fetch_cover_musicbrainz(artist, album)
            if not cover_path:
                print("No online cover found. Switching to local image.")
                choice = '2'
    
    if choice == '2':
        while True:
            local_path = input("Enter local image path (or 'b' to go back): ").strip()
            if local_path.lower() == 'b':
                return
            if os.path.exists(local_path) and os.path.isfile(local_path):
                ext = os.path.splitext(local_path)[1].lower()
                if ext in ('.jpg', '.jpeg', '.png', '.bmp', '.gif'):
                    cover_path = local_path
                    break
                else:
                    print("Unsupported image format. Try jpg/jpeg/png/bmp/gif.")
            else:
                print("File not found. Try again.")
    
    root, img = show_image_popup(cover_path)
    img_size = os.path.getsize(cover_path)
    print(f"\nCover file: {cover_path}")
    print(f"Dimensions: {img.width}x{img.height}")
    print(f"Size: {img_size // 1024} KB")
    
    while True:
        confirm = input("\nUse this cover? [y]es / [s]kip: ").strip().lower()
        if confirm in ('y', 's'):
            break
    
    root.destroy()
    
    if confirm == 's':
        print("Album cover embedding skipped.")
        return
    
    img = Image.open(cover_path).convert("RGB")
    img = img.resize((500, 500))
    converted_path = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg").name
    img.save(converted_path, format="JPEG")
    
    for fpath in audio_files:
        audio = load_audio_file(fpath)
        ext = os.path.splitext(fpath.lower())[1]
        with open(converted_path, 'rb') as imgfile:
            img_data = imgfile.read()
        
        if ext == '.mp3':
            if not hasattr(audio, 'tags') or audio.tags is None:
                audio.add_tags()
            audio.tags.add(APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=img_data))
            audio.save()
        elif ext == '.flac':
            pic = Picture()
            pic.type = 3
            pic.mime = 'image/jpeg'
            pic.desc = 'Cover'
            pic.data = img_data
            audio.clear_pictures()
            audio.add_picture(pic)
            audio.save()
        elif ext == '.m4a':
            audio.tags['covr'] = [MP4Cover(img_data, imageformat=MP4Cover.FORMAT_JPEG)]
            audio.save()
        elif ext in ('.ogg', '.opus', '.wma'):
            pic = Picture()
            pic.type = 3
            pic.mime = 'image/jpeg'
            pic.desc = 'Cover'
            pic.data = img_data
            audio.clear_pictures()
            audio.add_picture(pic)
            audio.save()
    
    print(f"Album cover embedded into {len(audio_files)} file(s).")

# ===================== LYRICS FUNCTIONS =====================
def find_lyrics_files(base_dir: str) -> List[str]:
    """Recursively find all lyrics files in directory."""
    base_dir = os.path.expanduser(base_dir.strip().strip('"').strip("'"))
    if not os.path.exists(base_dir):
        print(f"Error: Directory '{base_dir}' does not exist.")
        return []
    if not os.path.isdir(base_dir):
        print(f"Error: '{base_dir}' is not a directory.")
        return []
    
    lyrics_files = []
    for root, _, files in os.walk(base_dir):
        for file in files:
            if os.path.splitext(file.lower())[1] in ('.lrc', '.txt'):
                lyrics_files.append(os.path.join(root, file))
    return sorted(lyrics_files)

def display_lyrics_files(lyrics_files: List[str], max_display: int = 10):
    """Display lyrics files with limit."""
    total = len(lyrics_files)
    display_count = min(max_display, total)
    
    print(f"\nFound {total} lyrics file(s):")
    print("-" * 60)
    for i in range(display_count):
        filename = os.path.basename(lyrics_files[i])
        print(f"  {filename}")
    
    if total > max_display:
        print(f"  ... and {total - max_display} more file(s)")
    print("-" * 60)

def search_lyrics_files(lyrics_files: List[str], search_term: str) -> List[str]:
    """Search lyrics files by filename match."""
    search_term = search_term.lower().strip()
    matches = []
    for filepath in lyrics_files:
        filename = os.path.basename(filepath).lower()
        if search_term in filename:
            matches.append(filepath)
    return matches

def process_lyrics(audio_folder: str):
    """Handle lyrics embedding and/or file renaming."""
    audio_files = find_audio_files(audio_folder)
    if not audio_files:
        print("No audio files found in the folder.")
        return
    
    print(f"\nFound {len(audio_files)} audio file(s).")
    print("\nLyrics Options:")
    print("  [1] Embed lyrics file into audio metadata")
    print("  [2] Rename lyrics file to match song filename")
    print("  [3] Do both (embed + rename)")
    print("  [b] Back to setup menu")
    
    while True:
        choice = input("\nYour choice: ").strip().lower()
        if choice in ('1', '2', '3', 'b'):
            break
    
    if choice == 'b':
        return
    
    # Get lyrics directory
    while True:
        lyrics_dir = input("\nEnter lyrics directory path (or 'b' to go back): ").strip()
        if lyrics_dir.lower() == 'b':
            return
        
        lyrics_files = find_lyrics_files(lyrics_dir)
        if lyrics_files:
            break
        print("No lyrics files found in directory. Try again.")
    
    # Display available lyrics files
    display_lyrics_files(lyrics_files)
    
    # Search for lyrics file
    selected_lyrics_path = None
    while True:
        search_term = input("\nEnter song title to search (or 'b' to go back): ").strip()
        if search_term.lower() == 'b':
            return
        
        if not search_term:
            print("Please enter a search term.")
            continue
        
        matches = search_lyrics_files(lyrics_files, search_term)
        
        if not matches:
            print(f"No lyrics files found matching '{search_term}'. Try again.")
            continue
        
        print(f"\nFound {len(matches)} matching file(s):")
        for idx, filepath in enumerate(matches, start=1):
            print(f"  [{idx}] {os.path.basename(filepath)}")
        print("  [0] Search again")
        
        while True:
            try:
                file_choice = input("\nSelect lyrics file number: ").strip()
                if file_choice == '0':
                    break
                file_idx = int(file_choice) - 1
                if 0 <= file_idx < len(matches):
                    selected_lyrics_path = matches[file_idx]
                    break
                else:
                    print("Invalid selection. Try again.")
            except ValueError:
                print("Invalid input. Enter a number.")
        
        if selected_lyrics_path:
            break
    
    # Read lyrics content
    try:
        with open(selected_lyrics_path, 'r', encoding='utf-8') as f:
            lyrics_content = f.read()
    except Exception as e:
        print(f"Error reading lyrics file: {e}")
        return
    
    print(f"\nLyrics file loaded: {os.path.basename(selected_lyrics_path)}")
    print(f"Size: {len(lyrics_content)} characters")
    
    # Option 1 or 3: Embed lyrics
    if choice in ('1', '3'):
        embedded_count = 0
        for filepath in audio_files:
            audio = load_audio_file(filepath)
            if audio is None:
                continue
            
            if set_tag_value(audio, 'lyrics', lyrics_content, filepath):
                audio.save()
                embedded_count += 1
        
        print(f"\nLyrics embedded into {embedded_count} file(s).")
    
    # Option 2 or 3: Rename lyrics file
    if choice in ('2', '3'):
        if len(audio_files) == 1:
            # Single file: rename to match
            audio_file = audio_files[0]
            audio_dir = os.path.dirname(audio_file)
            audio_name = os.path.splitext(os.path.basename(audio_file))[0]
            lyrics_ext = os.path.splitext(selected_lyrics_path)[1]
            new_lyrics_path = os.path.join(audio_dir, f"{audio_name}{lyrics_ext}")
            
            try:
                import shutil
                shutil.copy2(selected_lyrics_path, new_lyrics_path)
                print(f"\nLyrics file copied to: {new_lyrics_path}")
            except Exception as e:
                print(f"Error copying lyrics file: {e}")
        else:
            # Multiple files: ask which one to match
            print("\nMultiple audio files found. Select which song to match:")
            for idx, filepath in enumerate(audio_files, start=1):
                print(f"  [{idx}] {os.path.basename(filepath)}")
            print("  [0] Skip renaming")
            
            while True:
                try:
                    file_choice = input("\nSelect file number: ").strip()
                    if file_choice == '0':
                        break
                    file_idx = int(file_choice) - 1
                    if 0 <= file_idx < len(audio_files):
                        audio_file = audio_files[file_idx]
                        audio_dir = os.path.dirname(audio_file)
                        audio_name = os.path.splitext(os.path.basename(audio_file))[0]
                        lyrics_ext = os.path.splitext(selected_lyrics_path)[1]
                        new_lyrics_path = os.path.join(audio_dir, f"{audio_name}{lyrics_ext}")
                        
                        try:
                            import shutil
                            shutil.copy2(selected_lyrics_path, new_lyrics_path)
                            print(f"\nLyrics file copied to: {new_lyrics_path}")
                        except Exception as e:
                            print(f"Error copying lyrics file: {e}")
                        break
                    else:
                        print("Invalid selection. Try again.")
                except ValueError:
                    print("Invalid input. Enter a number.")
    
    print("\nLyrics processing complete.")


# ===================== SETUP MENU =====================
def setup_menu(audio_files: List[str]) -> Tuple[List[str], Dict[str,str], List[str]]:
    print("\n" + "=" * 60)
    print("Setup Menu - Select Metadata Fields to Edit")
    print("=" * 60)
    print("\nAvailable Tags:")
    print("  [1] Cover          [7] Genre")
    print("  [2] Lyrics         [8] Date")
    print("  [3] Title          [9] Track Number")
    print("  [4] Artist         [10] Disc Number")
    print("  [5] Album          [11] Comment")
    print("  [6] Album Artist")
    print("\nInstructions: Enter numbers separated by spaces (e.g., 1 2 4)")
    print("              Type 'b' to go back to main menu")
    
    while True:
        selection = input("\nYour selection: ").strip()
        if selection.lower() == 'b':
            return None, None, None
        
        choices = selection.split()
        selected_tags = [AVAILABLE_TAGS[c] for c in choices if c in AVAILABLE_TAGS]
        if selected_tags:
            break
        print("Error: No valid tags selected. Try again.")
    
    global_values = {}
    per_file_tags = []
    metadata_map = analyze_metadata(audio_files, selected_tags)
    
    for tag in selected_tags:
        if tag == 'cover':
            continue
        if tag == 'lyrics':
            continue
        
        display_metadata_analysis(metadata_map, tag, audio_files)
        
        if tag in GLOBAL_TAGS:
            print(f"\nOptions for {tag.title()}:")
            print("  [g] Set global value for all files")
            print("  [i] Edit individually per file")
            print("  [s] Skip this tag")
            print("  [b] Back to setup menu")
            
            while True:
                choice = input("\nYour choice: ").strip().lower()
                if choice in ('g','i','s','b'):
                    break
            
            if choice == 'b':
                return None, None, None
            elif choice == 'g':
                new_val = input(f"Enter new {tag.title()} value: ").strip()
                if new_val:
                    global_values[tag] = new_val
            elif choice == 'i':
                per_file_tags.append(tag)
        else:
            per_file_tags.append(tag)
    
    return selected_tags, global_values, per_file_tags

# ===================== EDIT AUDIO FILES =====================
def edit_audio_files(audio_files: List[str], selected_tags: List[str], 
                    global_values: Dict[str,str], per_file_tags: List[str]) -> None:
    if not audio_files:
        print("\nNo audio files found.\n")
        return
    
    if global_values:
        for filepath in audio_files:
            audio = load_audio_file(filepath)
            if audio is None:
                continue
            for tag, val in global_values.items():
                set_tag_value(audio, tag, val, filepath)
            audio.save()
    
    if not per_file_tags:
        print("\nNo per-file edits required. Done.")
        return
    
    stats = {"processed":0,"skipped":0,"failed":0}
    
    for idx, path in enumerate(audio_files, start=1):
        audio = load_audio_file(path)
        if audio is None:
            stats["failed"] += 1
            continue
        
        filename = os.path.basename(path)
        print(f"\n[{idx}/{len(audio_files)}] File: {filename}")
        for tag in per_file_tags:
            current = get_tag_value(audio, tag, path)
            display_current = current if current else "[Not Set]"
            print(f"  {tag.title()}: {display_current}")
        
        print("\nOptions:")
        print("  [Enter] Edit this file")
        print("  [s] Skip this file")
        print("  [q] Quit and finish")
        
        action = input("\nYour choice: ").strip().lower()
        
        if action == 'q':
            break
        elif action == 's':
            stats["skipped"] += 1
            continue
        
        modified = False
        for tag in per_file_tags:
            current = get_tag_value(audio, tag, path)
            display_current = f"[{current}]" if current else "[Not Set]"
            new_val = input(f"  {tag.title()} {display_current}: ").strip()
            if new_val:
                set_tag_value(audio, tag, new_val, path)
                modified = True
        
        if modified:
            audio.save()
            stats["processed"] += 1
        else:
            stats["skipped"] += 1
    
    print("\n" + "=" * 60)
    print("Batch Operation Summary")
    print("=" * 60)
    if global_values:
        print(f"  Global edits applied to {len(audio_files)} file(s)")
    print(f"  Per-file processed: {stats['processed']}")
    print(f"  Per-file skipped:   {stats['skipped']}")
    print(f"  Failed:             {stats['failed']}")

# ===================== MAIN LOOP =====================
def main_loop() -> None:
    print("=" * 60)
    print("Audio Metadata Editor - Complete Version")
    print("=" * 60)
    
    while True:
        print("\n" + "=" * 60)
        print("Main Menu")
        print("=" * 60)
        print("Enter directory path to begin")
        print("Type 'e' to exit")
        
        directory = input("\nDirectory: ").strip()
        
        if directory.lower() == 'e':
            print("Exiting...")
            break
        
        if not directory:
            continue
        
        audio_files = find_audio_files(directory)
        if not audio_files:
            print("No audio files found in folder.")
            continue
        
        print(f"Found {len(audio_files)} audio file(s).")
        
        result = setup_menu(audio_files)
        if result == (None, None, None):
            continue
        
        selected_tags, global_values, per_file_tags = result
        
        if "cover" in selected_tags:
            process_album_cover(directory)
        
        if "lyrics" in selected_tags:
            process_lyrics(directory)
        
        edit_audio_files(audio_files, selected_tags, global_values, per_file_tags)

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
