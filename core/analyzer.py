import os
import tkinter as tk
from tkinter import filedialog
from config.project_files import project_file

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
def find_project_files(file_path):
    filtered_files = []
    files = os.listdir(file_path)
    for file in files:
        for category, file_list in project_file.items():
            if file.lower() in [f.lower() for f in file_list]:
                full_path = os.path.join(file_path, file)
                filtered_files.append(full_path)
    return filtered_files

def read_files(files):
    combined_summary = []
    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            content_base = f.read()
            combined_summary.append(file + ":-" + content_base + "\n")
    return combined_summary

filepath = choose_folder()
files_main = find_project_files(filepath)
content = read_files(files_main)
combined = "\n".join(content)
print(combined)
print(files_main)
