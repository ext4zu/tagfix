import tkinter as tk
from tkinter import ttk
from core.config import ConfigManager

class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, on_save=None):
        super().__init__(parent)
        self.title("Settings")
        self.geometry("400x500")
        self.configure(bg='#1e1e1e')
        self.on_save = on_save
        self.config = ConfigManager()
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Style Configuration
        style = ttk.Style()
        style.theme_use('clam') # Use clam as base for better customization
        
        # Notebook Style
        style.configure("Settings.TNotebook", background="#1e1e1e", borderwidth=0)
        style.configure("Settings.TNotebook.Tab", 
                        background="#2d2d2d", 
                        foreground="#888888", 
                        padding=[10, 5], 
                        borderwidth=0)
        style.map("Settings.TNotebook.Tab",
                  background=[("selected", "#1e1e1e"), ("active", "#3c3c3c")],
                  foreground=[("selected", "#ffffff"), ("active", "#ffffff")])
        
        # Main Container: Notebook
        self.notebook = ttk.Notebook(self, style="Settings.TNotebook")
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # --- Tab 1: Interface ---
        self.tab_interface = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_interface, text="Interface")
        self._build_interface_tab()
        
        # --- Tab 2: Cover Art ---
        self.tab_covers = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_covers, text="Cover Art")
        self._build_covers_tab()
        
        # --- Tab 3: Lyrics ---
        self.tab_lyrics = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_lyrics, text="Lyrics")
        self._build_lyrics_tab()
        
        # Footer Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Save", command=self.save).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=5)
        
    def _build_interface_tab(self):
        frame = ttk.LabelFrame(self.tab_interface, text="File List Columns")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.col_vars = {}
        columns = ["title", "artist", "album", "albumartist", "year", "genre"]
        current_cols = self.config.get("columns", "title") # Just to get the dict
        # Actually get returns the value, so we need to access the dict
        current_cols = self.config.config.get("columns", {})
        
        for col in columns:
            var = tk.BooleanVar(value=current_cols.get(col, True))
            self.col_vars[col] = var
            ttk.Checkbutton(frame, text=col.title(), variable=var).pack(anchor="w", padx=10, pady=5)
            
    def _build_covers_tab(self):
        frame = ttk.LabelFrame(self.tab_covers, text="Download Settings")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Force 500px
        self.force_500_var = tk.BooleanVar(value=self.config.get("covers", "force_500px", True))
        cb = ttk.Checkbutton(frame, text="Restrict downloads to 500x500px", variable=self.force_500_var)
        cb.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Tooltip-ish label
        ttk.Label(frame, text="Significantly speeds up previews and batch fetching.\nRecommended.", 
                  foreground="#888888", font=("", 9)).pack(anchor="w", padx=28, pady=(0, 15))
        
        # Source
        ttk.Label(frame, text="Preferred Source:").pack(anchor="w", padx=10)
        self.source_var = tk.StringVar(value=self.config.get("covers", "source", "iTunes"))
        
        # Style Fix
        style = ttk.Style()
        
        # Configure the dropdown listbox colors and shape
        # Use priority 100 to ensure these override defaults
        self.option_add('*TCombobox*Listbox.background', '#2d2d2d', 100)
        self.option_add('*TCombobox*Listbox.foreground', '#d4d4d4', 100)
        self.option_add('*TCombobox*Listbox.selectBackground', '#094771', 100)
        self.option_add('*TCombobox*Listbox.selectForeground', '#ffffff', 100)
        self.option_add('*TCombobox*Listbox.font', 'TkDefaultFont', 100)
        self.option_add('*TCombobox*Listbox.relief', 'flat', 100)
        self.option_add('*TCombobox*Listbox.borderwidth', '0', 100)
        self.option_add('*TCombobox*Listbox.highlightThickness', '0', 100)
        self.option_add('*TCombobox*Listbox.selectBorderWidth', '0', 100)
        
        try:
            style.layout('Square.TCombobox', style.layout('TCombobox'))
            style.configure('Square.TCombobox', 
                            arrowsize=12, 
                            relief='flat', 
                            borderwidth=1, 
                            # padding=5, # Removed padding to prevent layout issues
                            background='#252526', # Button background
                            fieldbackground='#3c3c3c', # Input area background
                            foreground='#d4d4d4',
                            bordercolor='#3e3e42',
                            lightcolor='#3e3e42',
                            darkcolor='#3e3e42')
            style.map('Square.TCombobox',
                      fieldbackground=[('readonly', '#3c3c3c')],
                      selectbackground=[('readonly', '#3c3c3c')],
                      selectforeground=[('readonly', '#d4d4d4')])
        except: pass
        
        combo = ttk.Combobox(frame, textvariable=self.source_var, state="readonly", style="Square.TCombobox")
        combo['values'] = ("iTunes", "MusicBrainz")
        combo.pack(fill=tk.X, padx=10, pady=5)
        
    def _build_lyrics_tab(self):
        frame = ttk.LabelFrame(self.tab_lyrics, text="Batch Behavior")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.strict_var = tk.BooleanVar(value=self.config.get("lyrics", "strict_mode", True))
        ttk.Checkbutton(frame, text="Strict Mode (Exact Match Only)", variable=self.strict_var).pack(anchor="w", padx=10, pady=5)
        
        self.save_lrc_var = tk.BooleanVar(value=self.config.get("lyrics", "save_lrc", False))
        ttk.Checkbutton(frame, text="Save .lrc files alongside audio", variable=self.save_lrc_var).pack(anchor="w", padx=10, pady=5)
        
    def save(self):
        # Save Interface
        for col, var in self.col_vars.items():
            self.config.config["columns"][col] = var.get()
            
        # Save Covers
        self.config.set("covers", "force_500px", self.force_500_var.get())
        self.config.set("covers", "source", self.source_var.get())
        
        # Save Lyrics
        self.config.set("lyrics", "strict_mode", self.strict_var.get())
        self.config.set("lyrics", "save_lrc", self.save_lrc_var.get())
        
        self.config.save()
        
        if self.on_save:
            self.on_save()
            
        self.destroy()
