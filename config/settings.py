import tkinter as tk
from tkinter import filedialog
'''path = os.path.join(os.path.expanduser("~"), "Downloads")'''

root = tk.Tk()
root.attributes('-topmost', True)
root.withdraw()
path = filedialog.askdirectory(parent=root)
root.destroy()

