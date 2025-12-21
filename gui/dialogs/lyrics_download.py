import tkinter as tk
from tkinter import ttk

class LyricsDownloadDialog(tk.Toplevel):
    def __init__(self, parent, on_start):
        super().__init__(parent)
        self.on_start = on_start
        self.title("Download Lyrics")
        self.geometry("350x250")
        self.configure(bg='#1e1e1e')
        self.resizable(False, False)
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Center window
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')
        
        # Content
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Configure Lyrics Download", font=("", 12, "bold")).pack(pady=(0, 15))
        
        # Options
        self.var_skip = tk.BooleanVar(value=True)
        self.var_strict = tk.BooleanVar(value=True)
        self.var_sidecar = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(frame, text="Skip existing synced lyrics", variable=self.var_skip).pack(anchor="w", pady=5)
        ttk.Checkbutton(frame, text="Strict Mode: Synced only", variable=self.var_strict).pack(anchor="w", pady=5)
        ttk.Checkbutton(frame, text="Auto-save sidecar (.lrc)", variable=self.var_sidecar).pack(anchor="w", pady=5)
        
        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(btn_frame, text="Fetch", command=self.start_fetch).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=5)
        
    def start_fetch(self):
        options = {
            "skip_existing": self.var_skip.get(),
            "strict_mode": self.var_strict.get(),
            "save_sidecar": self.var_sidecar.get()
        }
        self.on_start(options)
        self.destroy()
