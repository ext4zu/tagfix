import requests
import urllib.parse
import tempfile
import os

from core.config import ConfigManager

class MetadataHandler:
    def __init__(self):
        self.mb_url = "https://musicbrainz.org/ws/2"
        self.cover_url = "https://coverartarchive.org"
        self.lrc_url = "https://lrclib.net/api"
        self.headers = {'User-Agent': 'TagFix/1.0 (https://github.com/tagfix)'}
        self.config = ConfigManager()

    def fetch_cover(self, artist, album):
        source = self.config.get("covers", "source", "iTunes")
        
        if source == "iTunes":
            # iTunes First
            url = self.fetch_from_itunes(artist, album)
            if url:
                if self._download_to_temp(url): return self._download_to_temp(url)
            
            print("iTunes failed or no result, falling back to MusicBrainz...")
            return self._fetch_from_musicbrainz(artist, album)
        else:
            # MusicBrainz First
            path = self._fetch_from_musicbrainz(artist, album)
            if path: return path
            
            print("MusicBrainz failed, falling back to iTunes...")
            url = self.fetch_from_itunes(artist, album)
            if url:
                return self._download_to_temp(url)
        return None

    def _download_to_temp(self, url):
        try:
            resp = requests.get(url, headers=self.headers)
            if resp.status_code == 200:
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                tmp.write(resp.content)
                tmp.close()
                return tmp.name
        except Exception as e:
            print(f"Download error: {e}")
        return None

    def fetch_from_itunes(self, artist, album):
        try:
            term = f"{artist} {album}"
            encoded = urllib.parse.quote(term)
            url = f"https://itunes.apple.com/search?term={encoded}&entity=album&limit=1"
            
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('resultCount', 0) > 0:
                    artwork = data['results'][0].get('artworkUrl100')
                    if artwork:
                        force_500 = self.config.get("covers", "force_500px", True)
                        if force_500:
                            return artwork.replace('100x100bb', '500x500bb')
                        else:
                            return artwork.replace('100x100bb', '1000x1000bb')
        except Exception as e:
            print(f"iTunes search error: {e}")
        return None

    def _fetch_from_musicbrainz(self, artist, album):
        try:
            query = f'artist:"{artist}" AND release:"{album}"'
            encoded = urllib.parse.quote(query)
            url = f"{self.mb_url}/release?query={encoded}&fmt=json&limit=1"
            
            resp = requests.get(url, headers=self.headers)
            if resp.status_code == 200:
                data = resp.json()
                releases = data.get('releases', [])
                if releases:
                    mbid = releases[0]['id']
                    return self._download_mb_cover(mbid)
        except Exception as e:
            print(f"Cover fetch error: {e}")
        return None

    def _download_mb_cover(self, mbid):
        force_500 = self.config.get("covers", "force_500px", True)
        suffix = "front-500" if force_500 else "front"
        cover_url = f"{self.cover_url}/release/{mbid}/{suffix}"
        
        try:
            img_resp = requests.get(cover_url, headers=self.headers)
            if img_resp.status_code == 200:
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                tmp.write(img_resp.content)
                tmp.close()
                return tmp.name
            elif force_500 and img_resp.status_code == 404:
                # Fallback to original if 500px not found
                cover_url = f"{self.cover_url}/release/{mbid}/front"
                img_resp = requests.get(cover_url, headers=self.headers)
                if img_resp.status_code == 200:
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                    tmp.write(img_resp.content)
                    tmp.close()
                    return tmp.name
        except:
            pass
        return None

    # ... existing fetch_lyrics ...

    # ... existing search_releases ...

    def search_releases(self, artist, album):
        try:
            query = f'artist:"{artist}" AND release:"{album}"'
            encoded = urllib.parse.quote(query)
            url = f"{self.mb_url}/release?query={encoded}&fmt=json&limit=10"
            
            resp = requests.get(url, headers=self.headers)
            if resp.status_code == 200:
                data = resp.json()
                return data.get('releases', [])
        except Exception as e:
            print(f"Search releases error: {e}")
        return []

    def get_cover_bytes(self, mbid):
        force_500 = self.config.get("covers", "force_500px", True)
        suffix = "front-500" if force_500 else "front"
        cover_url = f"{self.cover_url}/release/{mbid}/{suffix}"
        
        try:
            resp = requests.get(cover_url, headers=self.headers)
            if resp.status_code == 200:
                return resp.content
            elif force_500 and resp.status_code == 404:
                # Fallback
                cover_url = f"{self.cover_url}/release/{mbid}/front"
                resp = requests.get(cover_url, headers=self.headers)
                if resp.status_code == 200:
                    return resp.content
        except Exception as e:
            print(f"Get cover bytes error: {e}")
        return None

    def search_lyrics(self, artist, title, album):
        try:
            params = {
                'q': f"{artist} {title} {album}".strip()
            }
            url = f"{self.lrc_url}/search"
            resp = requests.get(url, params=params, headers=self.headers)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            print(f"Search lyrics error: {e}")
        return []
