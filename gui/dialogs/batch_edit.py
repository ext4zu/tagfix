import tkinter as tk
from tkinter import ttk
import threading
import os
from core.audio import AudioHandler
from core.metadata import MetadataHandler
import io
from PIL import Image

class BatchEditDialog(tk.Toplevel):
    def __init__(self, parent, file_paths, status_map=None, on_update=None):
        super().__init__(parent)
        self.title("Batch Editor")
        self.geometry("600x700")
        self.configure(bg='#1e1e1e')
        self.file_paths = file_paths
        self.status_map = status_map or {}
        self.on_update = on_update
        self.audio_handler = AudioHandler()
        self.metadata_handler = MetadataHandler()
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Main Layout
        self.main_frame = ttk.Frame(self, padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # --- Top Section: Control Panel ---
        control_frame = ttk.LabelFrame(self.main_frame, text="Batch Metadata (Leave empty to keep original)")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.entries = {}
        fields = ["Artist", "Album", "AlbumArtist", "Year", "Genre"]
        
        for i, field in enumerate(fields):
            lbl = ttk.Label(control_frame, text=field)
            lbl.grid(row=i, column=0, sticky="w", padx=5, pady=2)
            
            ent = ttk.Entry(control_frame)
            ent.grid(row=i, column=1, sticky="ew", padx=5, pady=2)
            self.entries[field.lower()] = ent
            
        control_frame.columnconfigure(1, weight=1)
        
        # Bulk Actions
        action_frame = ttk.Frame(control_frame)
        action_frame.grid(row=len(fields), column=0, columnspan=2, sticky="ew", pady=10)
        
        ttk.Button(action_frame, text="Fetch All Covers (iTunes)", command=self.fetch_all_covers).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(action_frame, text="Resize All Covers (500x500)", command=self.resize_all_covers).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # --- Middle Section: File List ---
        list_frame = ttk.LabelFrame(self.main_frame, text=f"Files to Edit ({len(file_paths)})")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        columns = ("filename", "title")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        self.tree.heading("filename", text="Filename")
        self.tree.heading("title", text="Current Title")
        self.tree.column("filename", width=250)
        self.tree.column("title", width=250)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate List
        self._populate_list()
        
        # --- Bottom Section: Footer ---
        footer_frame = ttk.Frame(self.main_frame)
        footer_frame.pack(fill=tk.X)
        
        self.status_label = ttk.Label(footer_frame, text="Ready")
        self.status_label.pack(side=tk.LEFT)
        
        ttk.Button(footer_frame, text="Apply Changes", command=self.apply_changes).pack(side=tk.RIGHT, padx=5)
        ttk.Button(footer_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=5)
        
    def _populate_list(self):
        for path in self.file_paths:
            tags = self.audio_handler.get_tags(path)
            self.tree.insert("", "end", values=(os.path.basename(path), tags.get("title", "")))
            
    def apply_changes(self):
        # Get values to update
        updates = {k: e.get().strip() for k, e in self.entries.items() if e.get().strip()}
        
        if not updates:
            self.status_label.configure(text="No changes to apply.")
            return
            
        self.status_label.configure(text="Applying changes...")
        
        def worker():
            count = 0
            modified_paths = []
            for path in self.file_paths:
                tags = self.audio_handler.get_tags(path)
                # Apply updates
                for k, v in updates.items():
                    tags[k] = v
                
                if self.audio_handler.save_tags(path, tags):
                    count += 1
                    modified_paths.append(path)
                    
            self.after(0, lambda: self._on_complete(f"Updated {count} files.", modified_paths))
            
        t = threading.Thread(target=worker)
        t.daemon = True
        t.start()
        
    def fetch_all_covers(self):
        self.status_label.configure(text="Fetching covers...")
        
        def worker():
            count = 0
            modified_paths = []
            for path in self.file_paths:
                # Optimization: Check cached status first
                status = self.status_map.get(path)
                if status:
                    c_stat = status[0]
                    # Green (2) or Yellow (1) -> Skip (User requirement: "If Status is Green... SKIP", "If Status is Yellow... SKIP")
                    # Only process if Red (0)
                    if c_stat != 0:
                        continue
                else:
                    # Fallback to disk check if no cache
                    tags = self.audio_handler.get_tags(path)
                    if tags.get('cover_status', 0) != 0:
                        continue

                tags = self.audio_handler.get_tags(path)
                artist = tags.get("artist")
                album = tags.get("album")
                
                if artist and album:
                    # Use the new fetch_cover logic (iTunes priority)
                    cover_path = self.metadata_handler.fetch_cover(artist, album)
                    if cover_path:
                        with open(cover_path, 'rb') as f:
                            data = f.read()
                        if self.audio_handler.set_cover(path, data):
                            count += 1
                            modified_paths.append(path)
                            # Update status map for subsequent ops
                            self.status_map[path] = (2, self.status_map.get(path, (0,0))[1])
                        os.unlink(cover_path)
                        
            self.after(0, lambda: self._on_complete(f"Fetched {count} covers.", modified_paths))
            
        t = threading.Thread(target=worker)
        t.daemon = True
        t.start()
        
    def resize_all_covers(self):
        self.status_label.configure(text="Resizing covers...")
        
        def worker():
            count = 0
            modified_paths = []
            for path in self.file_paths:
                # Optimization: Check cached status first
                status = self.status_map.get(path)
                if status:
                    c_stat = status[0]
                    # Green (2) -> Skip
                    # Red (0) -> Skip
                    # Yellow (1) -> Process
                    if c_stat != 1:
                        continue
                else:
                    # Fallback
                    tags = self.audio_handler.get_tags(path)
                    c_stat = tags.get('cover_status', 0)
                    if c_stat == 2: continue # Already 500x500
                    
                data = self.audio_handler.get_cover(path)
                if data:
                    try:
                        img = Image.open(io.BytesIO(data))
                        # Resize to 500x500
                        img = img.resize((500, 500), Image.Resampling.LANCZOS)
                        
                        out = io.BytesIO()
                        img.save(out, format="JPEG", quality=90)
                        new_data = out.getvalue()
                        
                        if self.audio_handler.set_cover(path, new_data):
                            count += 1
                            modified_paths.append(path)
                            # Update status map
                            self.status_map[path] = (2, self.status_map.get(path, (0,0))[1])
                    except Exception:
                        pass
                        
            self.after(0, lambda: self._on_complete(f"Resized {count} covers.", modified_paths))
            
        t = threading.Thread(target=worker)
        t.daemon = True
        t.start()
        
    def _on_complete(self, message, modified_paths=None):
        self.status_label.configure(text=message)
        if self.on_update:
            self.on_update(modified_paths) # Trigger refresh in parent
        
        # Close after a brief delay to let user see "Updated X files"
        self.after(1000, self.destroy)
