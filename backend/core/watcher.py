import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from backend.core.index_manager import IndexManager


class DebouncedFileHandler(FileSystemEventHandler):
    def __init__(self, index_manager: IndexManager):
        self.index_manager = index_manager
        self.last_modified = {}

    def on_modified(self, event):
        if (
            event.is_directory
            or ".codequery" in event.src_path
            or ".git" in event.src_path
        ):
            return
        now = time.time()
        if (
            event.src_path in self.last_modified
            and now - self.last_modified[event.src_path] < 0.3
        ):
            return
        self.last_modified[event.src_path] = now
        try:
            self.index_manager.index_file(event.src_path)
        except (OSError, ValueError, RuntimeError) as e:
            print(f"Error indexing modified file {event.src_path}: {e}")

    def on_created(self, event):
        if (
            event.is_directory
            or ".codequery" in event.src_path
            or ".git" in event.src_path
        ):
            return
        try:
            self.index_manager.index_file(event.src_path)
        except (OSError, ValueError, RuntimeError) as e:
            print(f"Error indexing created file {event.src_path}: {e}")

    def on_deleted(self, event):
        if (
            event.is_directory
            or ".codequery" in event.src_path
            or ".git" in event.src_path
        ):
            return
        try:
            self.index_manager.remove_file(event.src_path)
        except (OSError, ValueError, RuntimeError) as e:
            print(f"Error removing deleted file {event.src_path}: {e}")


def start_watcher(index_manager: IndexManager) -> Observer:
    observer = Observer()
    handler = DebouncedFileHandler(index_manager)
    observer.schedule(handler, index_manager.workspace_path, recursive=True)
    observer.start()
    return observer
