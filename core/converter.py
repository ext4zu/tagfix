import os
import subprocess
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

class Converter:
    def convert_to_wav(self, files):
        return self._convert(files, 'wav')

    def convert_to_flac(self, files):
        return self._convert(files, 'flac')

    def _convert(self, files, fmt):
        count = 0
        for f in files:
            try:
                dirname = os.path.dirname(f)
                filename = os.path.basename(f)
                name, _ = os.path.splitext(filename)
                
                out_dir = os.path.join(dirname, f"converted_{fmt}")
                os.makedirs(out_dir, exist_ok=True)
                
                out_path = os.path.join(out_dir, f"{name}.{fmt}")
                
                if PYDUB_AVAILABLE:
                    audio = AudioSegment.from_file(f)
                    audio.export(out_path, format=fmt)
                    count += 1
                else:
                    cmd = ['ffmpeg', '-i', f, '-y', out_path]
                    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                    count += 1
            except Exception as e:
                print(f"Error converting {f}: {e}")
        return count
