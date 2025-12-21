import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import io

class EditorTab(ttk.Frame):
    def __init__(self, parent, on_save=None, audio_handler=None):
        super().__init__(parent)
        self.on_save = on_save
        self.audio_handler = audio_handler
        self.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.cover_frame = ttk.LabelFrame(self, text="Cover Art")
        self.cover_frame.pack(fill=tk.X, pady=5)
        
        self.cover_label = ttk.Label(self.cover_frame, text="[No Cover]")
        self.cover_label.pack(pady=5)
        
        self.resolution_label = ttk.Label(self.cover_frame, text="", font=("", 9))
        self.resolution_label.pack(pady=(0, 5))
        
        btn_frame = ttk.Frame(self.cover_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Search Online", command=self.search_cover).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        ttk.Button(btn_frame, text="Auto Fetch", command=self.fetch_auto_cover).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        ttk.Button(btn_frame, text="Select File", command=self.select_cover).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        ttk.Button(btn_frame, text="Resize", command=self.resize_cover).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        self.edit_frame = ttk.LabelFrame(self, text="Metadata")
        self.edit_frame.pack(fill=tk.X, pady=5)
        
        self.entries = {}
        
        fields = ["Title", "Artist", "Album", "AlbumArtist", "Year", "Genre"]
        for i, field in enumerate(fields):
            lbl = ttk.Label(self.edit_frame, text=field)
            lbl.grid(row=i, column=0, sticky="w", padx=5, pady=2)
            
            ent = ttk.Entry(self.edit_frame)
            ent.grid(row=i, column=1, sticky="ew", padx=5, pady=2)
            self.entries[field.lower()] = ent
            
        self.edit_frame.columnconfigure(1, weight=1)
        
        self.save_btn = ttk.Button(self, text="Apply Changes", command=self.save_tags)
        self.save_btn.pack(pady=10, fill=tk.X)
        
        lyrics_frame = ttk.LabelFrame(self, text="Lyrics")
        lyrics_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        btn_frame = ttk.Frame(lyrics_frame)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Fetch Lyrics", command=self.fetch_lyrics).pack(side=tk.RIGHT)
        
        # Modern Professional Palette
        INPUT_BG = '#3C3C3C'
        TEXT_PRIMARY = '#D4D4D4'
        SELECTION_BG = '#094771'
        BORDER_SUBTLE = '#3E3E42'
        
        self.lyrics_text = tk.Text(lyrics_frame, height=10, 
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
        self.lyrics_text.pack(fill=tk.BOTH, expand=True)
        
        self.current_track = None

    def load_track(self, track_data):
        self.current_track = track_data
        
        # Update Cover
        if self.audio_handler:
            data = self.audio_handler.get_cover(track_data["path"])
            if data:
                try:
                    img = Image.open(io.BytesIO(data))
                    self.resolution_label.configure(text=f"{img.width}x{img.height}")
                    img.thumbnail((200, 200))
                    photo = ImageTk.PhotoImage(img)
                    self.cover_label.configure(image=photo, text="")
                    self.cover_label.image = photo
                except Exception:
                    self.cover_label.configure(image="", text="[Error]")
                    self.resolution_label.configure(text="")
            else:
                self.cover_label.configure(image="", text="[No Cover]")
                self.resolution_label.configure(text="")
            
        # Update Entries
        for key, entry in self.entries.items():
            entry.delete(0, tk.END)
            entry.insert(0, track_data.get(key, ""))
            
        # Update Lyrics
        self.lyrics_text.delete("1.0", tk.END)
        self.lyrics_text.insert("1.0", track_data.get("lyrics", ""))

    def save_tags(self):
        if not self.current_track: return
        
        new_tags = {k: e.get() for k, e in self.entries.items()}
        new_tags["lyrics"] = self.lyrics_text.get("1.0", tk.END).strip()
        
        self.save_btn.configure(state="disabled", text="Saving...")
        self.show_toast("Saving Tags...")
        
        import threading
        def worker():
            success = False
            if self.on_save:
                success = self.on_save(self.current_track["path"], new_tags)
            self.after(0, lambda: self._on_save_complete(success))
            
        t = threading.Thread(target=worker)
        t.daemon = True
        t.start()

    def _on_save_complete(self, success):
        self.save_btn.configure(state="normal", text="Apply Changes")
        if success:
            self.show_toast("Tags Saved Successfully")
        else:
            self.show_toast("Save Failed")
            
    def fetch_lyrics(self):
        if not self.current_track: return
        artist = self.entries["artist"].get()
        title = self.entries["title"].get()
        album = self.entries["album"].get()
        
        from gui.dialogs.lyrics_search import LyricsSearchDialog
        LyricsSearchDialog(self.winfo_toplevel(), artist, title, album, self._update_lyrics)

    def _update_lyrics(self, text):
        self.lyrics_text.delete("1.0", tk.END)
        self.lyrics_text.insert("1.0", text)
        self.show_toast("Lyrics Fetched")

    def show_toast(self, message):
        toast = tk.Label(self, text=message, bg="#333", fg="white", padx=10, pady=5)
        toast.place(relx=0.5, rely=0.9, anchor="center")
        self.after(2000, toast.destroy)

    def search_cover(self):
        if not self.current_track: return
        
        artist = self.entries["artist"].get()
        album = self.entries["album"].get()
        
        from gui.dialogs.cover_search import CoverSearchDialog
        CoverSearchDialog(self.winfo_toplevel(), artist, album, self._on_cover_selected)

    def _on_cover_selected(self, data):
        if self.audio_handler.set_cover(self.current_track["path"], data):
            try:
                img = Image.open(io.BytesIO(data))
                self.resolution_label.configure(text=f"{img.width}x{img.height}")
                img.thumbnail((200, 200))
                photo = ImageTk.PhotoImage(img)
                self.cover_label.configure(image=photo, text="")
                self.cover_label.image = photo
                self.show_toast("Cover Updated")
                
                # Notify parent to refresh the specific row
                if self.on_save:
                    self.on_save(self.current_track["path"], None)
            except Exception:
                pass

    def fetch_auto_cover(self):
        if not self.current_track: return
        
        artist = self.entries["artist"].get()
        album = self.entries["album"].get()
        
        self.show_toast("Fetching Cover...")
        
        # Run in thread
        import threading
        def worker():
            from core.metadata import MetadataHandler
            handler = MetadataHandler()
            path = handler.fetch_cover(artist, album)
            if path:
                with open(path, 'rb') as f:
                    data = f.read()
                self.after(0, lambda: self._on_cover_selected(data))
                import os
                os.unlink(path) # Cleanup temp file
            else:
                self.after(0, lambda: self.show_toast("Cover Not Found"))
                
        t = threading.Thread(target=worker)
        t.daemon = True
        t.start()

    def select_cover(self):
        if not self.current_track: return
        from tkinter import filedialog
        path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.jpeg *.png")])
        if path:
            with open(path, 'rb') as f:
                data = f.read()
            if self.audio_handler.set_cover(self.current_track["path"], data):
                self.update_cover_display(path)

    def resize_cover(self):
        if not self.current_track: return
        
        self.show_toast("Resizing Cover...")
        
        import threading
        def worker():
            # Get current cover data from audio handler
            data = self.audio_handler.get_cover(self.current_track["path"])
            if data:
                try:
                    img = Image.open(io.BytesIO(data))
                    img = img.resize((500, 500), Image.Resampling.LANCZOS)
                    
                    # Save to bytes
                    out = io.BytesIO()
                    img.save(out, format="JPEG", quality=90)
                    new_data = out.getvalue()
                    
                    if self.audio_handler.set_cover(self.current_track["path"], new_data):
                        self.after(0, lambda: self._on_resize_complete(img))
                except Exception as e:
                    print(f"Resize error: {e}")
                    self.after(0, lambda: self.show_toast("Resize Failed"))
            else:
                self.after(0, lambda: self.show_toast("No Cover to Resize"))
                        
        t = threading.Thread(target=worker)
        t.daemon = True
        t.start()

    def _on_resize_complete(self, img):
        # Update display
        self.resolution_label.configure(text=f"{img.width}x{img.height}")
        img.thumbnail((200, 200))
        photo = ImageTk.PhotoImage(img)
        self.cover_label.configure(image=photo, text="")
        self.cover_label.image = photo
        self.show_toast("Cover Resized")

    def update_cover_display(self, path):
        try:
            img = Image.open(path)
            self.resolution_label.configure(text=f"{img.width}x{img.height}")
            img.thumbnail((200, 200))
            photo = ImageTk.PhotoImage(img)
            self.cover_label.configure(image=photo, text="")
            self.cover_label.image = photo
        except Exception:
            pass
