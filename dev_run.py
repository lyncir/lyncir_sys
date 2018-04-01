import time
from multiprocessing import Process

from os import path
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

HOST = "0.0.0.0"
PORT = 8000
WORKERS = 1
# 监听的文件夹
PATH = "."


class Reloader:
    class Handler(FileSystemEventHandler):
        def __init__(self, reloader):
            self.reloader = reloader

        # def on_any_event(self, event):
        #     """监听任何事件"""
        #     self.reloader.reload()

        def on_modified(self, event):
            """只监听修改事件"""
            self.reloader.reload()

    def __init__(self, directory, callback):
        self.observer = None
        self.process = None
        self.handler = Reloader.Handler(self)
        self.directory = path.abspath(directory)
        self.callback = callback

    def watch(self, first=True):
        if first:
            self.reload()
        else:
            self.observer = Observer()
            self.observer.schedule(self.handler, self.directory, recursive=True)
            self.observer.start()

    def reload(self):
        if self.observer:
            self.observer.stop()
            self.process.terminate()
            self.process.join()
        try:
            self.process = Process(target=self.callback)
            self.process.start()
        finally:
            self.watch(first=False)


def run_server():
    from app import app
    app.run(host=HOST, port=PORT, workers=WORKERS)


if __name__ == '__main__':
    Reloader(PATH, run_server).watch()
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break
