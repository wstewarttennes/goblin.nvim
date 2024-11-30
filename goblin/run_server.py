# run_server.py
import os
import sys
from django.core.management import call_command
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import signal

class CodeChangeHandler(FileSystemEventHandler):
    def __init__(self, server_process):
        self.server_process = server_process

    def on_modified(self, event):
        # Only react to Python file changes
        if event.src_path.endswith('.py'):
            print(f"\nDetected change in {event.src_path}")
            print("Restarting Daphne server...")
            
            # Send SIGTERM to the current server process
            os.kill(self.server_process.pid, signal.SIGTERM)
            
            # Start a new server process
            new_process = start_server()
            self.server_process = new_process

def start_server():
    # Start Daphne with your configuration
    process = subprocess.Popen([
        'daphne',
        '-b', '0.0.0.0',
        '-p', '8008',
        'goblin.asgi:application'
    ])
    return process

if __name__ == "__main__":
    # Start the initial server
    server_process = start_server()

    # Set up file watching
    event_handler = CodeChangeHandler(server_process)
    observer = Observer()
    
    # Watch both your app directories and the Django project directory
    paths_to_watch = [
        './goblin',  # Your Django project directory
        './ears',    # Your app directory
        # Add other directories you want to watch
    ]

    for path in paths_to_watch:
        observer.schedule(event_handler, path, recursive=True)

    print("Starting file watcher for hot reload...")
    observer.start()

    try:
        # Keep the script running
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        os.kill(server_process.pid, signal.SIGTERM)
    
    observer.join()
