import tkinter as tk
from tkinter import ttk
import threading

class LyricsSearchDialog(tk.Toplevel):
    def __init__(self, parent, artist, title, album, on_apply):
        super().__init__(parent)
        self.title("Search Lyrics")
        self.geometry("800x600")
        self.configure(bg='#1e1e1e')
        self.on_apply = on_apply
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Inputs
        input_frame = ttk.Frame(self)
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(input_frame, text="Artist:").grid(row=0, column=0, padx=5)
        self.artist_entry = ttk.Entry(input_frame)
        self.artist_entry.insert(0, artist)
        self.artist_entry.grid(row=0, column=1, sticky='ew', padx=5)
        
        ttk.Label(input_frame, text="Title:").grid(row=0, column=2, padx=5)
        self.title_entry = ttk.Entry(input_frame)
        self.title_entry.insert(0, title)
        self.title_entry.grid(row=0, column=3, sticky='ew', padx=5)
        
        ttk.Label(input_frame, text="Album:").grid(row=0, column=4, padx=5)
        self.album_entry = ttk.Entry(input_frame)
        self.album_entry.insert(0, album)
        self.album_entry.grid(row=0, column=5, sticky='ew', padx=5)
        
        ttk.Button(input_frame, text="Search", command=self.search).grid(row=0, column=6, padx=5)
        
        input_frame.columnconfigure(1, weight=1)
        input_frame.columnconfigure(3, weight=1)
        input_frame.columnconfigure(5, weight=1)
        
        # Content
        content_frame = ttk.Frame(self)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10)
        
        # List
        list_frame = ttk.Frame(content_frame)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.tree = ttk.Treeview(list_frame, columns=("title", "artist", "album", "synced"), show="headings")
        self.tree.heading("title", text="Title")
        self.tree.heading("artist", text="Artist")
        self.tree.heading("album", text="Album")
        self.tree.heading("synced", text="Synced")
        self.tree.column("synced", width=60, anchor="center")
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        
        # Preview
        preview_frame = ttk.Frame(content_frame)
        preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        ttk.Label(preview_frame, text="Preview:").pack(anchor="w")
        # Modern Professional Palette
        INPUT_BG = '#3C3C3C'
        TEXT_PRIMARY = '#D4D4D4'
        SELECTION_BG = '#094771'
        BORDER_SUBTLE = '#3E3E42'
        
        self.preview_text = tk.Text(preview_frame, width=40,
                                  bg=INPUT_BG, fg=TEXT_PRIMARY,
                                  insertbackground=TEXT_PRIMARY,
                                  selectbackground=SELECTION_BG,
                                  # --- THE BORDER FIXES ---
                                  bd=1,
                                  relief="flat",
                                  highlightthickness=1,
                                  highlightbackground=BORDER_SUBTLE,
                                  highlightcolor=SELECTION_BG,
                                  padx=5, pady=5)
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        
        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=5)
        self.apply_btn = ttk.Button(btn_frame, text="Apply", command=self.apply, state="disabled")
        self.apply_btn.pack(side=tk.RIGHT, padx=5)
        
        self.selected_lyrics = None
        
        if artist and title:
            self.search()

    def search(self):
        artist = self.artist_entry.get()
        title = self.title_entry.get()
        album = self.album_entry.get()
        
        self.tree.delete(*self.tree.get_children())
        self.preview_text.delete("1.0", tk.END)
        
        t = threading.Thread(target=self._search_worker, args=(artist, title, album))
        t.daemon = True
        t.start()
        
    def _search_worker(self, artist, title, album):
        from core.metadata import MetadataHandler
        handler = MetadataHandler()
        results = handler.search_lyrics(artist, title, album)
        self.after(0, lambda: self._update_list(results))
        
    def _update_list(self, results):
        if not hasattr(self, 'data_map'): self.data_map = {}
        self.data_map = {} # Clear old map
        
        for r in results:
            is_synced = "Yes" if r.get('syncedLyrics') else "No"
            item = self.tree.insert("", "end", values=(
                r.get('name', ''),
                r.get('artistName', ''),
                r.get('albumName', ''),
                is_synced
            ))
            self.data_map[item] = r

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel: return
        
        item = sel[0]
        data = self.data_map.get(item)
        if data:
            lyrics = data.get('syncedLyrics') or data.get('plainLyrics') or ""
            self.preview_text.delete("1.0", tk.END)
            self.preview_text.insert("1.0", lyrics if lyrics else "")
            self.selected_lyrics = lyrics
            self.apply_btn.configure(state="normal")

    def apply(self):
        if self.selected_lyrics:
            self.on_apply(self.selected_lyrics)
            self.destroy()
