import os
from watcher import path
files = os.listdir(path)
filenames = []
for file in files:
    filenames.append(file)
