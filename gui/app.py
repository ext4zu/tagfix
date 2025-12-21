import tkinter as tk
from tkinter import ttk
import os
from gui.tabs.browser import BrowserTab
from gui.tabs.editor import EditorTab
from gui.table import TrackTable
from core.audio import AudioHandler

class TagFixApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TagFix")
        self.root.geometry("1200x800")
        
        style = ttk.Style()
        style.theme_use('clam')
        
        # === MODERN PROFESSIONAL DARK PALETTE ===
        
        # 1. Background Layers (Creating Depth)
        ROOT_BG = '#1E1E1E'       # Deep matte charcoal
        SURFACE_BG = '#252526'    # Slightly lighter for sidebars/containers
        INPUT_BG = '#3C3C3C'      # Distinctly lighter for inputs
        
        # 2. Foreground & Text (Readability)
        TEXT_PRIMARY = '#D4D4D4'  # Off-white, soft
        TEXT_SECONDARY = '#858585' # Muted grey
        
        # 3. Borders & Accents (Structure)
        BORDER_SUBTLE = '#3E3E42' # CRITICAL: Fixes white outlines
        SELECTION_BG = '#094771'  # Professional muted blue
        SELECTION_FG = '#FFFFFF'
        
        # Store palette for access by other modules if needed
        self.colors = {
            'ROOT_BG': ROOT_BG,
            'SURFACE_BG': SURFACE_BG,
            'INPUT_BG': INPUT_BG,
            'TEXT_PRIMARY': TEXT_PRIMARY,
            'TEXT_SECONDARY': TEXT_SECONDARY,
            'BORDER_SUBTLE': BORDER_SUBTLE,
            'SELECTION_BG': SELECTION_BG,
            'SELECTION_FG': SELECTION_FG
        }
        
        # --- Global Widget Styles ---
        
        # Configure the global theme base
        style.configure(".",
                        background=ROOT_BG,
                        foreground=TEXT_PRIMARY,
                        bordercolor=BORDER_SUBTLE, # Ensure global borders are dark
                        darkcolor=BORDER_SUBTLE,   # Fixes 3D-effect shades
                        lightcolor=BORDER_SUBTLE)  # Fixes 3D-effect highlights
        
        # --- Containers & Labels ---
        style.configure("TFrame", background=ROOT_BG)
        style.configure("Surface.TFrame", background=SURFACE_BG)
        style.configure("TLabel", background=ROOT_BG, foreground=TEXT_PRIMARY)
        
        # --- Label Frames ---
        style.configure("TLabelframe",
                        background=ROOT_BG,
                        bordercolor=BORDER_SUBTLE,
                        borderwidth=1)
        style.configure("TLabelframe.Label",
                        background=ROOT_BG,
                        foreground=TEXT_PRIMARY)
        
        # --- Buttons ---
        style.configure("TButton",
                        background=SURFACE_BG,
                        foreground=TEXT_PRIMARY,
                        bordercolor=BORDER_SUBTLE,
                        borderwidth=1,
                        focusthickness=0,
                        relief="flat")
        style.map("TButton",
                  background=[('active', INPUT_BG), ('pressed', BORDER_SUBTLE)],
                  foreground=[('disabled', TEXT_SECONDARY)])
        
        # --- Inputs (TEntry) ---
        style.configure("TEntry",
                        fieldbackground=INPUT_BG,
                        foreground=TEXT_PRIMARY,
                        insertcolor=TEXT_PRIMARY,
                        bordercolor=BORDER_SUBTLE,
                        borderwidth=1,
                        relief="flat")
        
        # --- The Main Tables (Treeview) ---
        style.configure("Treeview",
                        background=ROOT_BG,
                        fieldbackground=ROOT_BG,
                        foreground=TEXT_PRIMARY,
                        bordercolor=BORDER_SUBTLE,
                        borderwidth=0)
                        
        style.configure("Treeview.Heading",
                        background=SURFACE_BG,
                        foreground=TEXT_PRIMARY,
                        bordercolor=BORDER_SUBTLE,
                        relief="flat")
                        
        style.map("Treeview",
                  background=[('selected', SELECTION_BG)],
                  foreground=[('selected', SELECTION_FG)])
        style.map("Treeview.Heading",
                  background=[('active', INPUT_BG)])
        
        self.paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)
        
        self.audio_handler = AudioHandler()
        self.tracks_cache = {}
        
        self.current_path = os.path.expanduser("~")
        
        self.editor = EditorTab(self.paned, self.on_save_tags, self.audio_handler)
        self.paned.add(self.editor, weight=1)
        
        self.table = TrackTable(self.paned, refresh_callback=self.refresh_current_folder, on_track_updated=self.on_track_updated)
        self.paned.add(self.table, weight=3)
        
        self.browser = BrowserTab(self.paned, self.on_folder_selected)
        self.paned.add(self.browser, weight=1)
        
        self.table.tree.bind("<<TreeviewSelect>>", self.on_track_selected)
        
        # We need to pass browser.log to table, but table is created before browser.
        # Let's create browser first?
        # Or pass a lambda that resolves later.
        
        # Re-ordering creation:
        # 1. Browser (Right/Sidebar) - wait, layout is: Editor | Table | Browser?
        # Original code: Editor(1), Table(3), Browser(1).
        # If I move Browser creation up, I need to add it to paned window later to keep order?
        # PanedWindow adds in order.
        
        # Alternative: Set the callback on table AFTER creating browser.
        self.table.set_log_callback(self.browser.log)
        
        self.browser.set_root(self.current_path)

    def refresh_current_folder(self):
        if self.current_path:
            self.on_folder_selected(self.current_path)

    def on_folder_selected(self, path):
        self.current_path = path
        self.table.clear()
        self.tracks_cache = {}
        try:
            supported_exts = ('.mp3', '.flac', '.m4a', '.ogg', '.wav')
            for root, dirs, files in os.walk(path):
                for f in files:
                    if f.lower().endswith(supported_exts):
                        fullpath = os.path.join(root, f)
                        tags = self.audio_handler.get_tags(fullpath)
                        item_id = self.table.add_track(tags)
                        self.tracks_cache[item_id] = tags
        except OSError:
            pass

    def on_track_selected(self, event):
        selection = self.table.tree.selection()
        if selection:
            item_id = selection[0]
            track_data = self.tracks_cache.get(item_id)
            if track_data:
                self.editor.load_track(track_data)

    def on_track_updated(self, filepath):
        # Re-read tags
        tags = self.audio_handler.get_tags(filepath)
        if not tags: return

        # Update cache
        # We need to find the item_id for this filepath
        for item_id, data in self.tracks_cache.items():
            if data["path"] == filepath:
                self.tracks_cache[item_id] = tags
                break
        
        # If the updated file is currently loaded in the editor, reload it
        if self.editor.current_track and self.editor.current_track["path"] == filepath:
            self.editor.load_track(tags)

    def on_save_tags(self, filepath, tags):
        if tags is None:
            # Refresh only (e.g. cover update)
            self.table.refresh_row(filepath)
            return True
            
        if self.audio_handler.save_tags(filepath, tags):
            # Update Table and Cache via refresh_row
            # This ensures item_status is updated in the table, 
            # and on_track_updated is called to update app cache and editor.
            self.table.refresh_row(filepath)
            return True
        return False
