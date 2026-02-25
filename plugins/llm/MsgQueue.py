from queue import Queue
import copy
import threading
import sys
from pathlib import Path

try:
    from .sys_prompt import *
except ImportError:
    CURRENT_DIR = Path(__file__).resolve().parent
    if str(CURRENT_DIR) not in sys.path:
        sys.path.insert(0, str(CURRENT_DIR))
    from sys_prompt import *


class MsgQueue:
    def __init__(self, memory_len):
        self.queue = Queue()
        self.lock = threading.Lock()
        self.memory_len = memory_len

    def put(self, x):
        with self.lock:
            self.queue.put(x)

    def content(self, type='None'):
        with self.lock:
            messages = list(self.queue.queue)
            if type == 'None':
                return copy.deepcopy(messages)
            return insert_prompt(messages, type=type)

    def size(self):
        with self.lock:
            return self.queue.qsize()

    def pop(self):
        with self.lock:
            self.queue.get()

    def check_len(self):
        with self.lock:
            while self.queue.qsize() > self.memory_len:
                try:
                    self.queue.get_nowait()
                except Exception:
                    break
                if self.queue.qsize() > self.memory_len:
                    try:
                        self.queue.get_nowait()
                    except Exception:
                        break

    def clear(self):
        with self.lock:
            self.queue.queue.clear()

    def copy(self):
        with self.lock:
            return copy.deepcopy(self.queue)

def insert_prompt(messages, type):
    messages = copy.deepcopy(messages)
    messages.insert(0, {
        'role': 'system',
        'content': sys_prompts[type],
    })
    return messages


