import os
import mutagen
from mutagen.easyid3 import EasyID3

class AudioHandler:
    def get_tags(self, filepath):
        try:
            audio = mutagen.File(filepath, easy=True)
            if not audio:
                return {"filename": os.path.basename(filepath), "path": filepath}
                
            tags = {
                "filename": os.path.basename(filepath),
                "title": audio.get("title", [""])[0],
                "artist": audio.get("artist", [""])[0],
                "album": audio.get("album", [""])[0],
                "albumartist": audio.get("albumartist", [""])[0],
                "year": audio.get("date", [""])[0],
                "genre": audio.get("genre", [""])[0],
                "path": filepath,
                "cover_status": 0,
                "lyrics_status": 0
            }
            
            # Fallback for year/date if empty
            if not tags["year"] and "originaldate" in audio:
                tags["year"] = audio.get("originaldate", [""])[0]

            # --- Optimization: Single Open for Advanced Metadata (Cover, Lyrics, Duration) ---
            try:
                audio_full = mutagen.File(filepath)
                
                # 1. Duration
                if audio_full and audio_full.info:
                    tags['duration'] = audio_full.info.length
                else:
                    tags['duration'] = 0

                # 2. Cover Art
                if filepath.lower().endswith('.mp3'):
                    if hasattr(audio_full, 'tags'):
                        for k in audio_full.tags.keys():
                            if k.startswith('APIC'):
                                pic = audio_full.tags[k]
                                from PIL import Image
                                import io
                                try:
                                    img = Image.open(io.BytesIO(pic.data))
                                    if img.size == (500, 500):
                                        tags['cover_status'] = 2
                                    else:
                                        tags['cover_status'] = 1
                                except:
                                    pass # Corrupt image data
                                break
                elif filepath.lower().endswith('.flac'):
                    if audio_full.pictures:
                        from PIL import Image
                        import io
                        try:
                            img = Image.open(io.BytesIO(audio_full.pictures[0].data))
                            if img.size == (500, 500):
                                tags['cover_status'] = 2
                            else:
                                tags['cover_status'] = 1
                        except:
                            pass

                # 3. Lyrics
                lyrics_text = ""
                if filepath.lower().endswith('.mp3'):
                    for k in audio_full.tags.keys():
                        if k.startswith('USLT'):
                            lyrics_text = str(audio_full.tags[k])
                            break
                        elif k.startswith('SYLT'):
                            lyrics_text = "[Synced Lyrics Present]" 
                            tags['lyrics_status'] = 2
                            break
                elif filepath.lower().endswith('.flac'):
                    if 'lyrics' in audio_full:
                        lyrics_text = audio_full['lyrics'][0]
                
                if lyrics_text:
                    tags['lyrics'] = lyrics_text
                    # Check for timestamps if status not already set by SYLT
                    if tags['lyrics_status'] == 0:
                        import re
                        # Look for [mm:ss.xx] or [mm:ss]
                        if re.search(r'\[\d{2}:\d{2}(?:\.\d{2,3})?\]', lyrics_text):
                            tags['lyrics_status'] = 2 # Synced
                        else:
                            tags['lyrics_status'] = 1 # Unsynced

            except Exception as e:
                print(f"Error reading advanced metadata for {filepath}: {e}")
                tags['duration'] = 0
            
            return tags
        except Exception:
            return {"filename": os.path.basename(filepath), "path": filepath}

    def save_tags(self, filepath, tags):
        try:
            audio = mutagen.File(filepath, easy=True)
            if not audio:
                audio = mutagen.File(filepath)
                if not audio: return False
                audio.add_tags()
            
            audio["title"] = tags.get("title", "")
            audio["artist"] = tags.get("artist", "")
            audio["album"] = tags.get("album", "")
            audio["albumartist"] = tags.get("albumartist", "")
            audio["date"] = tags.get("year", "")
            audio["genre"] = tags.get("genre", "")
            
            audio.save()
            
            # Handle Lyrics (Not easy ID3)
            audio_full = mutagen.File(filepath)
            lyrics = tags.get("lyrics", "")
            
            if filepath.lower().endswith('.mp3'):
                from mutagen.id3 import USLT
                if not audio_full.tags: audio_full.add_tags()
                
                if lyrics:
                    # Remove existing USLT frames first to avoid duplicates
                    to_del = [k for k in audio_full.tags.keys() if k.startswith('USLT')]
                    for k in to_del: del audio_full.tags[k]
                    
                    audio_full.tags.add(USLT(encoding=3, lang='eng', desc='', text=lyrics))
                else:
                    to_del = [k for k in audio_full.tags.keys() if k.startswith('USLT')]
                    for k in to_del: del audio_full.tags[k]
                audio_full.save()
            elif filepath.lower().endswith('.flac'):
                audio_full['lyrics'] = lyrics
                audio_full.save()
                
            return True
        except Exception as e:
            print(f"Save Error: {e}")
            return False

    def get_cover(self, filepath):
        try:
            audio = mutagen.File(filepath)
            if not audio: return None
            
            if filepath.lower().endswith('.mp3'):
                if hasattr(audio, 'tags'):
                    for t in audio.tags.values():
                        if t.FrameID == 'APIC':
                            return t.data
            elif filepath.lower().endswith('.flac'):
                if audio.pictures:
                    return audio.pictures[0].data
            elif filepath.lower().endswith('.m4a'):
                if 'covr' in audio.tags:
                    return bytes(audio.tags['covr'][0])
            
            return None
        except Exception:
            return None

    def set_cover(self, filepath, image_data, mime_type='image/jpeg'):
        try:
            from PIL import Image
            import io
            
            # Verify it's a valid image but DO NOT RESIZE
            img = Image.open(io.BytesIO(image_data))
            img.verify() 
            
            # Reset pointer after verify
            # actually verify might consume it? 
            # Better just to use the original image_data if valid.
            
            # We need to ensure mime_type is correct or just trust caller?
            # The caller defaults to image/jpeg.
            # Let's just use the data provided.
            
            audio = mutagen.File(filepath)
            if not audio: return False
            
            if filepath.lower().endswith('.mp3'):
                from mutagen.id3 import APIC
                if not audio.tags: audio.add_tags()
                audio.tags.add(APIC(encoding=3, mime=mime_type, type=3, desc='Cover', data=image_data))
            elif filepath.lower().endswith('.flac'):
                from mutagen.flac import Picture
                pic = Picture()
                pic.type = 3
                pic.mime = mime_type
                pic.desc = 'Cover'
                pic.data = image_data
                audio.clear_pictures()
                audio.add_picture(pic)
            elif filepath.lower().endswith('.m4a'):
                from mutagen.mp4 import MP4Cover
                fmt = MP4Cover.FORMAT_JPEG if mime_type == 'image/jpeg' else MP4Cover.FORMAT_PNG
                audio.tags['covr'] = [MP4Cover(image_data, imageformat=fmt)]
            
            audio.save()
            return True
        except Exception:
            return False

    def get_lyrics(self, filepath):
        try:
            audio = mutagen.File(filepath)
            if not audio: return ""
            
            if filepath.lower().endswith('.mp3'):
                if hasattr(audio, 'tags'):
                    for key in audio.tags.keys():
                        if key.startswith('USLT'):
                            return audio.tags[key].text
            elif filepath.lower().endswith('.m4a'):
                if '\xa9lyr' in audio.tags:
                    return audio.tags['\xa9lyr'][0]
            elif filepath.lower().endswith('.flac'):
                if 'lyrics' in audio:
                    return audio['lyrics'][0]
            
            return ""
        except Exception:
            return ""

    def save_lyrics(self, filepath, lyrics):
        try:
            audio = mutagen.File(filepath)
            if not audio: return False
            
            if filepath.lower().endswith('.mp3'):
                from mutagen.id3 import USLT
                if not audio.tags: audio.add_tags()
                audio.tags.add(USLT(encoding=3, lang='eng', desc='', text=lyrics))
            elif filepath.lower().endswith('.m4a'):
                audio.tags['\xa9lyr'] = [lyrics]
            elif filepath.lower().endswith('.flac'):
                audio['lyrics'] = [lyrics]
            
            audio.save()
            return True
        except Exception:
            return False
