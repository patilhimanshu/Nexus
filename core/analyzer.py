import os
import tkinter as tk
from tkinter import filedialog
from core.intent_classifier import detect_intent
from core.intent_classifier import build_context
import requests

from config.project_files import project_file

def analyzer():
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

    def query_project(data):
        system_prompt = """You are Nexus, an intelligent project assistant and developer companion.
    You have been given the full context of the user's project including their code,
    dependencies, and documentation. Your job is to answer questions about this project
    accurately, concisely, and helpfully. Be professional but approachable.
    Never make up information — only answer based on what you know from the project files provided.
    If you don't know something, say so clearly."""
        while True:
            question = input("What would you like to ask?(Type bye to quit):")
            summary = "It is a modular workspace"

            if question == "bye":
                break
            else:
                intent = detect_intent(question)
                print(f"Detected intent: {intent}")
                system_prompt = build_context(intent, data, summary)
                prompt = f"{system_prompt}\n\nUser Question:\n{question}"
                model = "gemma3"
                response = requests.post("http://localhost:11434/api/generate", json={"model": model , "prompt": prompt, "stream" : False})
                answer = response.json()["response"]
                print(f"\nNexus: {answer}\n")


    filepath = choose_folder()
    if filepath is None:
        print("No file selected")
        exit()

    files_main = find_project_files(filepath)
    content = read_files(files_main)
    combined = "\n".join(content)
    query_project(combined)


