import tkinter as tk
from tkinter import ttk

class BatchResultsDialog(tk.Toplevel):
    def __init__(self, parent, stats, failures):
        super().__init__(parent)
        self.title("Batch Complete")
        
        # Compact dimensions
        width = 450
        height = 350 if failures else 180
        
        # Center relative to parent
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (width // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (height // 2)
        self.geometry("500x400")
        self.configure(bg='#1e1e1e')
        self.resizable(False, False)
        
        # Modal behavior
        self.transient(parent)
        self.grab_set()
        
        # Main Container
        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # --- 1. Header ---
        # Simple text header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(header_frame, text="Batch Operation Complete", font=("", 10, "bold")).pack(anchor="w")
        
        # --- 2. Stats Grid (Single Row) ---
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Helper to create stat label
        def add_stat(label, value, color=None):
            f = ttk.Frame(stats_frame)
            f.pack(side=tk.LEFT, padx=(0, 15))
            ttk.Label(f, text=f"{label}: ", font=("", 9)).pack(side=tk.LEFT)
            lbl = ttk.Label(f, text=str(value), font=("", 9, "bold"))
            if color: lbl.configure(foreground=color)
            lbl.pack(side=tk.LEFT)

        add_stat("Total", stats['total'])
        add_stat("Saved", stats['saved'], "green")
        add_stat("Skipped", stats['skipped'], "gray")
        add_stat("Failed", stats['failed'], "red")
        
        # --- 4. Footer (Packed first to ensure visibility at bottom) ---
        btn = ttk.Button(main_frame, text="Close", command=self.destroy)
        btn.pack(side=tk.BOTTOM, anchor="e", pady=(10, 0))
        
        # Auto-focus and bind Enter
        btn.focus_set()
        self.bind("<Return>", lambda e: self.destroy())
        self.bind("<Escape>", lambda e: self.destroy())

        # --- 3. Details Area ---
        if failures:
            # Error List
            ttk.Label(main_frame, text="Failed Items:", font=("", 9)).pack(anchor="w", pady=(0, 5))
            
            list_frame = ttk.Frame(main_frame)
            list_frame.pack(fill=tk.BOTH, expand=True)
            
            # Scrollbar + Listbox
            columns = ("filename", "reason")
            tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="none", height=8)
            tree.heading("filename", text="Filename", anchor="w")
            tree.heading("reason", text="Reason", anchor="w")
            tree.column("filename", width=200)
            tree.column("reason", width=150)
            
            scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            for f in failures:
                tree.insert("", "end", values=(f['filename'], f['reason']))
                
        else:
            # Success Message
            msg_frame = ttk.Frame(main_frame)
            msg_frame.pack(fill=tk.BOTH, expand=True)
            ttk.Label(msg_frame, text="Process completed successfully.", foreground="green", font=("", 10)).pack(expand=True)
