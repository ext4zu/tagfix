import tkinter as tk
from tkinter import ttk
import os # Added for os.path.basename

class TrackTable(ttk.Frame):
    def __init__(self, parent, refresh_callback=None, on_track_updated=None, log_callback=None):
        super().__init__(parent)
        self.refresh_callback = refresh_callback
        self.on_track_updated = on_track_updated
        self.log_callback = log_callback
        self.pack(fill=tk.BOTH, expand=True)

        # Create a frame to hold the Treeview and its scrollbar
        self.frame = ttk.Frame(self)
        self.frame.grid(column=0, row=1, sticky='nsew') # Row 1 now
        
        # Toolbar
        self.toolbar = ttk.Frame(self)
        self.toolbar.grid(column=0, row=0, sticky='ew', padx=5, pady=2)
        
        ttk.Button(self.toolbar, text="⚙ Columns", command=self.show_settings).pack(side=tk.RIGHT)
        ttk.Button(self.toolbar, text="Batch Edit", command=self.open_batch_editor).pack(side=tk.RIGHT, padx=5)
        ttk.Button(self.toolbar, text="Fetch All Lyrics", command=self.mass_lyrics_fetch).pack(side=tk.RIGHT, padx=5)

        self.columns = ("filename", "title", "artist", "album", "albumartist", "year", "genre")
        self.tree = ttk.Treeview(self.frame, columns=self.columns, show="headings", selectmode="browse")
        
        # Dark Mode Tags
        DARK_BG = '#181818'
        DARK_ALT_BG = '#252525'
        TEXT_FG = '#E0E0E0'
        
        self.tree.tag_configure('odd', background=DARK_BG, foreground=TEXT_FG)
        self.tree.tag_configure('even', background=DARK_ALT_BG, foreground=TEXT_FG)

        # Configure #0 (Hidden in show="headings", but we want icons...)
        # Wait, show="tree headings" shows #0. show="headings" hides #0.
        # If we want a dedicated column for icons, we can use #0 as that column.
        # So we must use show="tree headings".
        self.tree.configure(show="tree headings")

        # Column #0: Cover/Lyrics (Status Icons)
        self.tree.heading("#0", text="Cover/Lyrics", anchor="center")
        self.tree.column("#0", width=100, minwidth=100, stretch=False, anchor="center")

        # Column 1: Filename
        self.tree.heading("filename", text="Filename")
        self.tree.column("filename", width=200, anchor="w")

        self.tree.heading("title", text="Title")
        self.tree.column("title", width=150)

        self.tree.heading("artist", text="Artist")
        self.tree.column("artist", width=150)

        self.tree.heading("album", text="Album")
        self.tree.column("album", width=150)
        
        self.tree.heading("albumartist", text="Album Artist")
        self.tree.column("albumartist", width=150)

        self.tree.heading("year", text="Year")
        self.tree.column("year", width=60)

        self.tree.heading("genre", text="Genre")
        self.tree.column("genre", width=100)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Vertical scrollbar
        scrollbar = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Horizontal scrollbar
        hsb = ttk.Scrollbar(self.frame, orient="horizontal", command=self.tree.xview)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.configure(xscrollcommand=hsb.set)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) # Make row 1 (for the table) expandable

        self.icon_cache = [] # Keep references to PhotoImage objects to prevent garbage collection
        self.item_paths = {} # Store full paths for items
        self.item_status = {} # Store (cover_status, lyrics_status)

        # Settings Button
        settings_button = ttk.Button(self, text="Settings", command=self.show_settings)
        settings_button.grid(row=0, column=0, sticky='ne', padx=5, pady=5) # Placed in row 0, top-right

        # Pro Dark Palette
        DARK_BG = '#1e1e1e'
        TEXT_FG = '#d4d4d4'
        BUTTON_ACTIVE_BG = '#4a4a4a'
        
        self.menu = tk.Menu(self, tearoff=0,
                          bg=DARK_BG, fg=TEXT_FG,
                          activebackground=BUTTON_ACTIVE_BG, activeforeground=TEXT_FG) # Context menu for rows (original)
        # Converter removed as requested
        
        self.tree.bind("<Button-3>", self.show_menu)
        
        # Apply initial settings
        self.apply_settings()

    def set_log_callback(self, callback):
        self.log_callback = callback

    def show_settings(self):
        from gui.dialogs.settings import SettingsDialog
        SettingsDialog(self.winfo_toplevel(), on_save=self.apply_settings)

    def apply_settings(self):
        from core.config import ConfigManager
        config = ConfigManager()
        cols = config.get_section("columns")
        
        for col, visible in cols.items():
            self.toggle_column(col, visible)

    def toggle_column(self, col, visible):
        if visible:
            # Restore a default width or a previously saved width
            # For simplicity, let's use a default width if it was 0
            if col == "title": self.tree.column(col, width=150, stretch=True)
            elif col == "artist": self.tree.column(col, width=150, stretch=True)
            elif col == "album": self.tree.column(col, width=150, stretch=True)
            elif col == "albumartist": self.tree.column(col, width=150, stretch=True)
            elif col == "year": self.tree.column(col, width=60, stretch=True)
            elif col == "genre": self.tree.column(col, width=100, stretch=True)
            else: self.tree.column(col, width=100, stretch=True) # Fallback default
        else:
            self.tree.column(col, width=0, stretch=False)

    def show_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            if item not in self.tree.selection():
                self.tree.selection_set(item)
            self.menu.post(event.x_root, event.y_root)

    def open_batch_editor(self):
        items = self.tree.get_children()
        if not items:
            print("No files to edit")
            return
            
        file_paths = []
        status_map = {}
        for item in items:
            path = self.item_paths.get(item)
            status = self.item_status.get(item)
            if path:
                file_paths.append(path)
                if status:
                    status_map[path] = status
                
        if not file_paths: return
        
        from gui.dialogs.batch_edit import BatchEditDialog
        BatchEditDialog(self.winfo_toplevel(), file_paths, status_map=status_map, on_update=self.on_batch_update)

    def on_batch_update(self, modified_paths=None):
        if modified_paths:
            print(f"Batch update: Refreshing {len(modified_paths)} rows...")
            for path in modified_paths:
                self.refresh_row(path)
        else:
            # Fallback to full refresh
            if self.refresh_callback:
                self.refresh_callback()

    def mass_lyrics_fetch(self):
        items = self.tree.get_children()
        if not items:
            print("No files to process")
            return

        from gui.dialogs.lyrics_download import LyricsDownloadDialog
        LyricsDownloadDialog(self.winfo_toplevel(), self._start_mass_fetch)

    def _start_mass_fetch(self, options):
        items = self.tree.get_children()
        
        # Find button first
        self.fetch_btn = None
        for child in self.toolbar.winfo_children():
            if child.cget("text") == "Fetch All Lyrics":
                self.fetch_btn = child
                break
        
        # Collect file paths with optimization
        file_paths = []
        skipped_count = 0
        
        for item in items:
            path = self.item_paths.get(item)
            status = self.item_status.get(item)
            
            if not path: continue
            
            if not status:
                # Fallback if no status, process it
                file_paths.append(path)
                continue
                
            l_stat = status[1] # 0=Red, 1=Yellow, 2=Green
            
            should_process = False
            if l_stat == 0: # Red (Missing)
                should_process = True
            elif l_stat == 1: # Yellow (Unsynced)
                if options['strict_mode']:
                    should_process = True # Try to upgrade to synced
                elif not options['skip_existing']:
                    should_process = True # Force re-fetch
            elif l_stat == 2: # Green (Synced)
                if not options['skip_existing']:
                    should_process = True # Force re-fetch
            
            if should_process:
                file_paths.append(path)
            else:
                skipped_count += 1
        
        if not file_paths:
            msg = f"All {skipped_count} files skipped based on current status."
            print(msg)
            if self.log_callback:
                self.log_callback(msg)
                
            self.batch_stats = {
                'total': len(items),
                'saved': 0,
                'skipped': skipped_count,
                'failed': 0
            }
            self.batch_failures = []
            self._on_batch_complete(0)
            return

        import threading
        # If we pass skip_existing=True to processor, it will read disk and check again.
        # To be safe and strictly follow "Trust this state", we can rely on our filtering.
        # But the processor needs to know if it should skip if it finds something on disk that wasn't in cache (rare).
        # Let's just pass the options as is. The overhead of reading disk for the *processed* files is necessary anyway to get Artist/Title.
        
        # Initialize stats
        # We need to account for the skipped files in the total
        self.batch_stats = {
            'total': len(items), # Total items selected/in list
            'saved': 0,
            'skipped': skipped_count,
            'failed': 0
        }
        self.batch_failures = []
        
        t = threading.Thread(target=self._mass_fetch_worker, args=(file_paths, items, options))
        t.daemon = True
        t.start()
        if self.log_callback:
            self.log_callback(f"Started mass fetch for {len(file_paths)} files")
        print(f"Started mass fetch for {len(file_paths)} files")

    def _mass_fetch_worker(self, file_paths, items, options):
        # Set loading icons in main thread
        self.after(0, lambda: self._set_loading_icons(items))
        
        from core.batch_lyrics import BatchLyricsProcessor
        proc = BatchLyricsProcessor()
        
        def progress(processed, total, filepath, status):
            self.after(0, lambda: self._on_batch_progress(processed, total, filepath, status))
            
        proc.process_library(file_paths, progress, **options)
        
        self.after(0, lambda: self._on_batch_complete(len(file_paths)))
        if self.log_callback:
            self.after(0, lambda: self.log_callback("Mass fetch complete"))
        print("Mass fetch complete")

    def _on_batch_complete(self, count):
        if self.fetch_btn:
            self.fetch_btn.configure(text="Fetch All Lyrics")
        
        from gui.dialogs.batch_results import BatchResultsDialog
        BatchResultsDialog(self.winfo_toplevel(), self.batch_stats, self.batch_failures)

    def _on_batch_progress(self, processed, total, filepath, status):
        # Update button text
        if self.fetch_btn:
            self.fetch_btn.configure(text=f"Fetching: {processed}/{total}")
            
        msg = f"[{processed}/{total}] {status}: {os.path.basename(filepath)}"
        print(msg)
        if self.log_callback:
            self.log_callback(msg)
        
        # Update stats
        if status == "Success":
            self.batch_stats['saved'] += 1
            self.after(0, lambda: self.refresh_row(filepath))
        elif status == "Skipped (Synced)":
            self.batch_stats['skipped'] += 1
            self.after(0, lambda: self.refresh_row(filepath))
        else:
            self.batch_stats['failed'] += 1
            # Map status to user-friendly reason
            reason = status
            if status == "Not Found":
                reason = "No lyrics found"
            elif status == "No Synced Lyrics":
                reason = "Only unsynced lyrics found"
            
            self.batch_failures.append({
                'filename': os.path.basename(filepath),
                'reason': reason
            })

    def _set_loading_icons(self, items):
        from core.icons import create_status_icon
        for item in items:
            status = self.item_status.get(item)
            if status:
                cover_stat, lyrics_stat = status
                # Only set loading if not already synced
                if lyrics_stat != 2:
                    icon = create_status_icon(cover_stat, lyrics_stat, is_loading=True)
                    self.tree.item(item, image=icon)
                    self.icon_cache.append(icon)


    def refresh_row(self, filepath):
        # Find item
        target_item = None
        for item, path in self.item_paths.items():
            if path == filepath:
                target_item = item
                break
        
        if target_item and self.tree.exists(target_item):
            # Re-read tags to get fresh status
            from core.audio import AudioHandler
            from core.icons import create_status_icon
            handler = AudioHandler()
            tags = handler.get_tags(filepath)
            if tags:
                c_stat = tags.get('cover_status', 0)
                l_stat = tags.get('lyrics_status', 0)
                icon = create_status_icon(c_stat, l_stat)
                
                # Update Values
                values = (
                    os.path.basename(filepath), # Filename
                    tags.get("title", ""),
                    tags.get("artist", ""),
                    tags.get("album", ""),
                    tags.get("albumartist", ""),
                    tags.get("year", ""),
                    tags.get("genre", "")
                )
                
                # Update #0 text to empty (icon only)
                self.tree.item(target_item, text="", image=icon, values=values)
                
                # Update cache and status
                self.icon_cache.append(icon)
                self.item_status[target_item] = (c_stat, l_stat)
                
                # Notify app of update (to refresh editor if needed)
                if self.on_track_updated:
                    self.on_track_updated(filepath)

    def convert_selected(self, fmt):
        selection = self.tree.selection()
        if not selection: return
        
        files = []
        for item in selection:
            # Retrieve the full path from the stored item_paths dictionary
            path = self.item_paths.get(item)
            if path:
                files.append(path)
        
        if not files: return
        
        from core.converter import Converter
        conv = Converter()
        if fmt == 'wav':
            conv.convert_to_wav(files)
        elif fmt == 'flac':
            conv.convert_to_flac(files)
        
        print(f"Converted {len(files)} files to {fmt}")

    def add_track(self, tags):
        from core.icons import create_status_icon
        c_stat = tags.get('cover_status', 0)
        l_stat = tags.get('lyrics_status', 0)
        icon = create_status_icon(c_stat, l_stat)
        self.icon_cache.append(icon)
        
        values = (
            os.path.basename(tags["path"]), # Filename
            tags.get("title", ""),
            tags.get("artist", ""),
            tags.get("album", ""),
            tags.get("albumartist", ""),
            tags.get("year", ""),
            tags.get("genre", "")
        )
        # Zebra Striping
        idx = len(self.tree.get_children())
        tag = 'even' if idx % 2 == 0 else 'odd'
        
        # Use text="" for column #0 (icon only)
        item = self.tree.insert("", "end", text="", image=icon, values=values, tags=(tag,))
        self.item_paths[item] = tags["path"] # Store path
        self.item_status[item] = (c_stat, l_stat) # Store status
        return item

    def clear(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.item_paths.clear()
        self.item_status.clear()
