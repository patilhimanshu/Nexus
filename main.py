
from core.watcher import start_watching
import time
def main():
    start_watching()
    while True:
        time.sleep(1)
if __name__ == '__main__':
    main()