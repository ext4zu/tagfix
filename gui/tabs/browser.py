import tkinter as tk
from tkinter import ttk
import os

class BrowserTab(ttk.Frame):
    def __init__(self, parent, on_folder_selected):
        super().__init__(parent)
        self.on_folder_selected = on_folder_selected
        self.pack(fill=tk.BOTH, expand=True)
        
        # Split Container
        self.paned = ttk.PanedWindow(self, orient=tk.VERTICAL)
        self.paned.pack(fill=tk.BOTH, expand=True)
        
        # --- Top Section: Browser ---
        self.browser_frame = ttk.Frame(self.paned)
        self.paned.add(self.browser_frame, weight=5) # 80-85% approx
        
        ctrl_frame = ttk.Frame(self.browser_frame)
        ctrl_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(ctrl_frame, text="Refresh", command=self.refresh).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        ttk.Button(ctrl_frame, text="Change Root", command=self.change_root).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        self.tree = ttk.Treeview(self.browser_frame)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.heading("#0", text="Folders", anchor="w")
        
        # --- Bottom Section: Log Console ---
        self.log_frame = ttk.Frame(self.paned)
        self.paned.add(self.log_frame, weight=1) # 15-20% approx
        
        # Console
        from tkinter import scrolledtext
        # Modern Professional Palette
        INPUT_BG = '#3C3C3C'
        TEXT_PRIMARY = '#D4D4D4'
        SELECTION_BG = '#094771'
        BORDER_SUBTLE = '#3E3E42'
        
        self.console = scrolledtext.ScrolledText(self.log_frame, height=4, state='disabled',
                                               bg=INPUT_BG, fg=TEXT_PRIMARY,
                                               insertbackground=TEXT_PRIMARY,
                                               selectbackground=SELECTION_BG,
                                               # --- THE BORDER FIXES ---
                                               bd=1,
                                               relief="flat",
                                               highlightthickness=1,
                                               highlightbackground=BORDER_SUBTLE,
                                               highlightcolor=SELECTION_BG)
        self.console.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Styling - Standard Theme
        self.console.configure(font=("Consolas", 9))
        self.console.tag_config("timestamp", foreground="#888888")
        
        self.nodes = {}
        self.current_root = None
        self.populate_root()
        
        self.tree.bind("<<TreeviewOpen>>", self.on_open)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.bind("<Button-3>", self.show_menu)
        
        # Pro Dark Palette
        DARK_BG = '#1e1e1e'
        TEXT_FG = '#d4d4d4'
        BUTTON_ACTIVE_BG = '#4a4a4a'
        
        self.menu = tk.Menu(self, tearoff=0, 
                          bg=DARK_BG, fg=TEXT_FG, 
                          activebackground=BUTTON_ACTIVE_BG, activeforeground=TEXT_FG)
        self.menu.add_command(label="Refresh", command=self.refresh_selected)

    def log(self, message):
        import datetime
        timestamp = datetime.datetime.now().strftime("[%H:%M:%S] ")
        
        self.console.configure(state='normal')
        self.console.insert(tk.END, timestamp, "timestamp")
        self.console.insert(tk.END, message + "\n")
        self.console.see(tk.END)
        self.console.configure(state='disabled')
        

    def show_menu(self, event):
        node = self.tree.identify_row(event.y)
        if node:
            self.tree.selection_set(node)
            self.menu.post(event.x_root, event.y_root)

    def refresh_selected(self):
        node = self.tree.focus()
        path = self.nodes.get(node)
        if path:
            self.populate_node(node, path)

    def change_root(self):
        from tkinter import filedialog
        path = filedialog.askdirectory(title="Select Root Folder", initialdir=self.current_root)
        if path:
            self.set_root(path)
            if self.on_folder_selected:
                self.on_folder_selected(path)

    def refresh(self):
        if self.current_root:
            # Save current selection
            selected_path = None
            sel = self.tree.selection()
            if sel:
                selected_path = self.nodes.get(sel[0])
            
            self.set_root(self.current_root)
            
            # Restore selection
            if selected_path:
                self._expand_to_path(selected_path)
            
            if self.on_folder_selected and selected_path:
                self.on_folder_selected(selected_path)
            elif self.on_folder_selected:
                self.on_folder_selected(self.current_root)

    def _expand_to_path(self, target_path):
        # Break path into components relative to root
        try:
            rel = os.path.relpath(target_path, self.current_root)
            if rel == '.': return
            
            parts = rel.split(os.sep)
            current_node = None
            
            # Find root node
            for item in self.tree.get_children():
                if self.nodes.get(item) == self.current_root:
                    current_node = item
                    break
            
            if not current_node: return
            
            # Walk down
            for part in parts:
                # Ensure children are loaded
                self.populate_node(current_node, self.nodes[current_node])
                self.tree.item(current_node, open=True)
                
                # Find next node
                found = False
                for child in self.tree.get_children(current_node):
                    if self.tree.item(child, "text") == part:
                        current_node = child
                        found = True
                        break
                
                if not found: return
            
            # Select final node
            self.tree.selection_set(current_node)
            self.tree.see(current_node)
        except Exception as e:
            print(f"Error restoring selection: {e}")

    def set_root(self, path):
        self.current_root = path
        self.tree.delete(*self.tree.get_children())
        self.nodes = {}
        
        node = self.tree.insert("", "end", text=os.path.basename(path), open=True)
        self.nodes[node] = path
        self.populate_node(node, path)

    def populate_root(self):
        # Deprecated, use set_root
        pass

    def on_open(self, event):
        node = self.tree.focus()
        path = self.nodes.get(node)
        if path:
            self.populate_node(node, path)

    def populate_node(self, parent, path):
        self.tree.delete(*self.tree.get_children(parent)) # Keep this line to clear existing children
        try:
            for item in sorted(os.listdir(path)):
                if item.startswith('.'): continue
                
                fullpath = os.path.join(path, item)
                if os.path.isdir(fullpath):
                    node = self.tree.insert(parent, "end", text=item, open=False)
                    self.nodes[node] = fullpath
                    self.tree.insert(node, "end", text="Loading...")
        except OSError: # Changed from PermissionError to OSError as per instruction's snippet
            pass

    def on_select(self, event):
        if self.on_folder_selected:
            node = self.tree.focus()
            path = self.nodes.get(node)
            if path:
                self.on_folder_selected(path)
