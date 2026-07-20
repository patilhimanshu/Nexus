import os
import tkinter as tk
from tkinter import filedialog
from core.intent_classifier import detect_intent
from core.intent_classifier import build_context
from dotenv import load_dotenv
import requests
import json
from config.models import RESPONSE_MODEL
from config.model_prompt import system_prompt
from core.memory import summarize_and_save, load_memory
from config.project_files import project_file
load_dotenv()


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
        for root,dirs,files in os.walk(file_path):

            for file in files:
                for category, file_list in project_file.items():
                    if file.lower() in [f.lower() for f in file_list]:
                        full_path = os.path.join(root, file)
                        filtered_files.append(full_path)
        return filtered_files

    def read_files(files):
        combined_summary = []
        for file in files:
            with open(file, "r", encoding="utf-8") as f:
                content_base = f.read()
                relative_path = os.path.relpath(file, filepath).replace("\\", "/")
                combined_summary.append(
                    f"\n===== {relative_path} =====\n{content_base}\n"
                )
        return combined_summary

    def query_project(data):
        conversation_history = []
        past_memory = load_memory()
        while True:
            question = input("What would you like to ask?(Type bye to quit):")
            summary = "It is a modular workspace"

            if question == "bye":
                if len(conversation_history) > 0:
                    summarize_and_save(conversation_history, filepath)
                break
            else:
                api_key = os.getenv("GROQ_API_KEY")
                intent = detect_intent(question)
                system_prompt_built = build_context(intent, data, summary)
                prompt = f"{system_prompt_built}\n\nPast Session Memory:\n{past_memory}\n\nUser Question:\n{question}"
                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": RESPONSE_MODEL,
                        "messages" : conversation_history + [{"role": "user", "content": prompt}],
                        "stream": True
                    },
                    stream=True
                )

                full_answer = ""
                print("\nNexus: ", end="", flush=True)
                for chunk in response.iter_lines():
                    if chunk:
                        chunk_str = chunk.decode("utf-8").replace("data: ", "")
                        if chunk_str == "[DONE]":
                            break
                        chunk_data = json.loads(chunk_str)
                        delta = chunk_data["choices"][0]["delta"].get("content", "")
                        print(delta, end="", flush=True)
                        full_answer += delta
                print("\n")
                conversation_history.append({"role":"user", "content": prompt})
                conversation_history.append({"role":"assistant", "content": full_answer})


    filepath = choose_folder()
    if filepath is None:
        print("No file selected")
        exit()

    files_main = find_project_files(filepath)
    content = read_files(files_main)
    combined = "\n".join(content)
    query_project(combined)


