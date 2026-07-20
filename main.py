
from core.watcher import start_watching
from core.scanner import start_scan
from core.analyzer import analyzer
import time
def main():
    while True:
        start_organize = input("Hii, want Nexus to begin scan and organize the files?(yes/no):")
        if start_organize == "yes":
            start_scan()
            start_watching()
        else:
            print("Ok ✌️")
        analyzer()
        time.sleep(1)
        break
if __name__ == '__main__':
    main()