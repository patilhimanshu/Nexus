
from core.watcher import start_watching
from core.scanner import start_scan
import time
def main():
    start_scan()
    start_watching()
    while True:
        time.sleep(1)
if __name__ == '__main__':
    main()