def start_watching():
    path = "C:/Users/umesh/Downloads"
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    import time
    import os
    last_modified = {}
    class NexusObserver(FileSystemEventHandler):
        print("Watching for changes....")
        def on_created(self, event):
            print(f"Event {event.src_path} created")
        def on_deleted(self, event):
            print(f"Event {event.src_path} deleted")
        def on_modified(self, event):
            current_time = time.time()
            file_path = event.src_path
            if file_path in last_modified:
                time_diff = current_time - last_modified[file_path]
                if time_diff < 0.5:
                    return
            if event.is_directory and event.src_path == path:
                return
            last_modified[file_path] = current_time
            print(f"Event {event.src_path} modified")

        def on_moved(self, event):
            current_dir = os.path.dirname(event.src_path)
            changed_dir = os.path.dirname(event.dest_path)
            if current_dir == changed_dir:
                return
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
        observer.join()