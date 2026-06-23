import os
import tkinter as tk
from tkinter import filedialog

def choose_folder():
    answer = input("Would you like Nexus to understand your project? (yes/no): ")
    if answer == "yes":
        root = tk.Tk()
        root.attributes('-topmost', True)
        root.withdraw()
        file_path = filedialog.askdirectory(parent=root)
        root.destroy()
        return file_path
    else:
        print("Ok ✌️")
choose_folder()