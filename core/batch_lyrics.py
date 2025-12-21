import os
import concurrent.futures
import requests
import time
from core.audio import AudioHandler

class BatchLyricsProcessor:
    def __init__(self):
        self.lrc_url = "https://lrclib.net/api"
        self.headers = {'User-Agent': 'TagFix/1.0 (https://github.com/tagfix)'}
        self.session = requests.Session()
        self.audio_handler = AudioHandler()

    def process_library(self, files, progress_callback=None, skip_existing=True, strict_mode=True, save_sidecar=True):
        # files is now a list of paths
        
        total = len(files)
        processed = 0
        
        # 2. Process concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_file = {executor.submit(self._process_file, f, skip_existing, strict_mode, save_sidecar): f for f in files}
            for future in concurrent.futures.as_completed(future_to_file):
                f = future_to_file[future]
                try:
                    res = future.result()
                    if progress_callback:
                        processed += 1
                        progress_callback(processed, total, f, res)
                except Exception as e:
                    print(f"Error processing {f}: {e}")

    def _process_file(self, filepath, skip_existing, strict_mode, save_sidecar):
        # A. Read Metadata
        try:
            tags = self.audio_handler.get_tags(filepath)
            if not tags: return "Read Error"
            
            # B. Check if needed (Skip if synced lyrics already exist)
            if skip_existing:
                has_embedded = tags.get('lyrics_status', 0) == 2 # 2 is Synced
                # We ONLY check for embedded lyrics here. 
                # Even if a sidecar exists, if embedded is missing, we want to fetch/embed.
                
                if has_embedded:
                    return "Skipped (Synced)"

            # C. Fetch
            # Optimization: Use duration from tags (added in AudioHandler optimization)
            duration = tags.get('duration', 0)

            lyrics_data = self._fetch_lyrics(tags.get('artist'), tags.get('title'), tags.get('album'), duration)
            
            if not lyrics_data:
                return "Not Found"
            
            synced_lyrics = lyrics_data.get('syncedLyrics')
            plain_lyrics = lyrics_data.get('plainLyrics')
            
            final_lyrics = None
            
            if synced_lyrics:
                final_lyrics = synced_lyrics
            elif not strict_mode and plain_lyrics:
                final_lyrics = plain_lyrics
            else:
                return "No Synced Lyrics"

            # D. Sidecar
            if save_sidecar and synced_lyrics: # Only save sidecar if we have synced lyrics (usually)
                lrc_path = os.path.splitext(filepath)[0] + ".lrc"
                with open(lrc_path, 'w', encoding='utf-8') as f:
                    f.write(synced_lyrics)
            
            # E. Embed
            tags['lyrics'] = final_lyrics
            self.audio_handler.save_tags(filepath, tags)
            
            return "Success"
            
        except Exception as e:
            return f"Error: {str(e)}"

    def _fetch_lyrics(self, artist, title, album, duration):
        try:
            params = {
                'artist_name': artist,
                'track_name': title,
                'album_name': album,
                'duration': duration
            }
            # Remove empty
            params = {k: v for k, v in params.items() if v}
            
            url = f"{self.lrc_url}/get"
            try:
                resp = self.session.get(url, params=params, headers=self.headers, timeout=10)
            except requests.exceptions.RequestException:
                return None

            if resp.status_code == 200:
                data = resp.json()
                if self._validate_duration(data.get('duration'), duration):
                    return data
            
            # Fallback search if strict match fails or duration mismatch
            # (User requirement: GET /api/get or /api/search)
            # If GET failed (404) or validation failed, try search
            if resp.status_code == 404 or (resp.status_code == 200 and not self._validate_duration(resp.json().get('duration'), duration)):
                 # Search logic could go here, but /get is usually best for "Mass" to avoid false positives.
                 # Let's stick to /get for high precision in mass mode, or maybe a very strict search.
                 pass
                 
            return None
            
        except Exception:
            return None

    def _validate_duration(self, api_duration, local_duration):
        if not api_duration or not local_duration: return True # Cannot validate
        return abs(float(api_duration) - float(local_duration)) < 2.0
