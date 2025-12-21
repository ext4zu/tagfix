import os
import shutil
import re
import mutagen

class Organizer:
    def organize_folder(self, source_dir):
        dest_dir = os.path.join(source_dir, "Sorted")
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
            
        supported_exts = ('.flac', '.mp3', '.m4a', '.ogg', '.wav', '.opus', '.wma', '.alac', '.aiff')
        failures = []
        
        for root, dirs, files in os.walk(source_dir):
            if "Sorted" in root: continue
            
            for file in files:
                if file.lower().endswith(supported_exts):
                    src_path = os.path.join(root, file)
                    try:
                        artist, album = self.get_metadata(src_path)
                        safe_artist = self.sanitize_name(artist)
                        safe_album = self.sanitize_name(album)
                        
                        target_folder = os.path.join(dest_dir, safe_artist, safe_album)
                        os.makedirs(target_folder, exist_ok=True)
                        
                        target_path = os.path.join(target_folder, file)
                        if os.path.exists(target_path):
                            base, ext = os.path.splitext(file)
                            counter = 1
                            while os.path.exists(target_path):
                                target_path = os.path.join(target_folder, f"{base} ({counter}){ext}")
                                counter += 1
                        
                        shutil.copy2(src_path, target_path)
                        count += 1
                    except Exception as e:
                        failures.append(f"Failed to organize {file}: {e}")
                        
        return count, failures

    def get_metadata(self, file_path):
        try:
            audio = mutagen.File(file_path, easy=True)
            if not audio: return "Unknown Artist", "Unknown Album"
            artist = audio.get('albumartist', audio.get('artist', ['Unknown Artist']))[0]
            album = audio.get('album', ['Unknown Album'])[0]
            return artist, album
        except Exception:
            return "Unknown Artist", "Unknown Album"

    def sanitize_name(self, name):
        if not name: return "Unknown"
        return re.sub(r'[<>:"/\\|?*]', '_', name).strip()
