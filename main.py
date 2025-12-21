import tkinter as tk
from gui.app import TagFixApp

if __name__ == "__main__":
    root = tk.Tk()
    root.configure(bg='#1E1E1E')
    app = TagFixApp(root)
    root.mainloop()
