import os

# Bug fix: this used to be hardcoded to "C:/Users/umesh/Downloads",
# which only exists on Himanshu's machine. os.path.expanduser("~")
# resolves to the current user's home folder on ANY machine
# (Windows, Mac, or Linux), so this works for Aahil, Himanshu, or
# anyone else who runs Nexus without editing this file.
path = os.path.join(os.path.expanduser("~"), "Downloads")
