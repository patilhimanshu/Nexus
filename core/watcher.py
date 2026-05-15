def start_watching():
    path = "C:/Users/umesh/Downloads"
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    import time
    import os

    class NexusObserver(FileSystemEventHandler):
        def on_created(self, event):
            print(f"Event {event.src_path} created")
        def on_deleted(self, event):
            print(f"Event {event.src_path} deleted")
        def on_modified(self, event):
            if event.is_directory:
                if event.src_path == path:
                    return
            print(f"Event {event.src_path} modified")

        def on_moved(self, event):
            print(f"Event moved from {event.src_path} to {event.dest_path} ")

    observer = Observer()
    nexus_observer = NexusObserver()
    observer.schedule(nexus_observer, path=path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()