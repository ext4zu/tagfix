import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import io
import threading

class CoverSearchDialog(tk.Toplevel):
    def __init__(self, parent, artist, album, on_apply):
        super().__init__(parent)
        self.title("Search Cover Art")
        self.geometry("900x600") # Wider for split view
        self.configure(bg='#1e1e1e')
        self.on_apply = on_apply
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # --- 1. Top: Inputs ---
        input_frame = ttk.Frame(self)
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(input_frame, text="Artist:").grid(row=0, column=0, padx=5)
        self.artist_entry = ttk.Entry(input_frame)
        self.artist_entry.insert(0, artist)
        self.artist_entry.grid(row=0, column=1, sticky='ew', padx=5)
        
        ttk.Label(input_frame, text="Album:").grid(row=0, column=2, padx=5)
        self.album_entry = ttk.Entry(input_frame)
        self.album_entry.insert(0, album)
        self.album_entry.grid(row=0, column=3, sticky='ew', padx=5)
        
        ttk.Button(input_frame, text="Search", command=self.search).grid(row=0, column=4, padx=5)
        input_frame.columnconfigure(1, weight=1)
        input_frame.columnconfigure(3, weight=1)
        
        # --- 2. Main: Split View (PanedWindow) ---
        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Left Pane: Results (60%)
        left_frame = ttk.Frame(self.paned)
        self.paned.add(left_frame, weight=3)
        
        self.tree = ttk.Treeview(left_frame, columns=("artist", "album"), show="headings")
        self.tree.heading("artist", text="Artist")
        self.tree.heading("album", text="Album")
        self.tree.column("artist", width=150)
        self.tree.column("album", width=200)
        
        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        
        # Right Pane: Preview (40%)
        right_frame = ttk.Frame(self.paned)
        self.paned.add(right_frame, weight=2)
        
        # Preview Container (Dark background)
        self.preview_container = tk.Frame(right_frame, bg="#2d2d2d")
        self.preview_container.pack(fill=tk.BOTH, expand=True)
        
        self.preview_label = tk.Label(self.preview_container, text="No Selection", bg="#2d2d2d", fg="#888888")
        self.preview_label.place(relx=0.5, rely=0.5, anchor="center")
        
        self.info_label = tk.Label(right_frame, text="", font=("", 9))
        self.info_label.pack(fill=tk.X, pady=5)
        
        # --- 3. Bottom: Buttons ---
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=5)
        self.apply_btn = ttk.Button(btn_frame, text="Apply", command=self.apply, state="disabled")
        self.apply_btn.pack(side=tk.RIGHT, padx=5)
        
        self.selected_data = None
        self.current_selection_id = None # For race condition check
        
        # Auto-search
        if artist and album:
            self.search()

    def search(self):
        artist = self.artist_entry.get()
        album = self.album_entry.get()
        
        self.tree.delete(*self.tree.get_children())
        self.preview_label.configure(image="", text="Searching...")
        self.info_label.configure(text="")
        
        t = threading.Thread(target=self._search_worker, args=(artist, album))
        t.daemon = True
        t.start()
        
    def _search_worker(self, artist, album):
        from core.metadata import MetadataHandler
        handler = MetadataHandler()
        results = handler.search_releases(artist, album)
        self.after(0, lambda: self._update_list(results))
        
    def _update_list(self, results):
        if not results:
            from tkinter import messagebox
            messagebox.showinfo("No Results", "No cover art found.\nTry changing the search terms (e.g., remove 'feat.' or album edition).")
            self.preview_label.configure(text="No Results")
            return

        self.preview_label.configure(text="Select an item")
        for r in results:
            # MusicBrainz structure
            title = r.get('title', 'Unknown')
            artist_credit = r.get('artist-credit', [{'name': 'Unknown'}])[0]['name']
            item = self.tree.insert("", "end", values=(artist_credit, title))
            
            if not hasattr(self, 'data_map'): self.data_map = {}
            self.data_map[item] = r['id']

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel: return
        
        item = sel[0]
        mbid = self.data_map.get(item)
        
        if mbid:
            # 1. Immediate UI Update
            self.preview_label.configure(image="", text="Loading...", fg="white")
            self.info_label.configure(text="")
            self.apply_btn.configure(state="disabled")
            self.selected_data = None
            
            # Capture selection ID (using mbid as ID for simplicity, or item ID)
            self.current_selection_id = item
            
            # 2. Background Thread
            t = threading.Thread(target=self._preview_worker, args=(mbid, item))
            t.daemon = True
            t.start()
            
    def _preview_worker(self, mbid, request_id):
        from core.metadata import MetadataHandler
        handler = MetadataHandler()
        data = handler.get_cover_bytes(mbid)
        self.after(0, lambda: self._update_preview(data, request_id))
        
    def _update_preview(self, data, request_id):
        # 3. Validation
        current_sel = self.tree.selection()
        if not current_sel or current_sel[0] != request_id:
            return # User clicked something else, discard this result
            
        if data:
            try:
                img = Image.open(io.BytesIO(data))
                w, h = img.size
                
                # Resize for preview (max 300x300)
                img.thumbnail((300, 300))
                photo = ImageTk.PhotoImage(img)
                
                self.preview_label.configure(image=photo, text="")
                self.preview_label.image = photo # Keep reference
                self.info_label.configure(text=f"Resolution: {w}x{h}")
                
                self.selected_data = data
                self.apply_btn.configure(state="normal")
            except:
                self.preview_label.configure(image="", text="Error Loading Image", fg="red")
        else:
            self.preview_label.configure(image="", text="No Cover Available", fg="#888888")

    def apply(self):
        if self.selected_data:
            self.on_apply(self.selected_data)
            self.destroy()
