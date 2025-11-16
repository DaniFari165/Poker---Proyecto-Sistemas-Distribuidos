import socket, threading, json, time
from queue import Queue, Empty

class NetClient:
    def __init__(self):
        self.sock = None
        self.incoming = Queue()
        self.running = False

    def connect(self, host, port, nick):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        self.running = True

        # enviamos nick
        self.send({"type": "hello", "nick": nick})

        t = threading.Thread(target=self._recv_loop, daemon=True)
        t.start()

    def _recv_loop(self):
        f = self.sock.makefile("r", encoding="utf-8", newline="\n")
        for line in f:
            if not self.running:
                break
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            self.incoming.put(msg)
        self.running = False

    def send(self, obj):
        if not self.sock:
            return
        data = json.dumps(obj) + "\n"
        self.sock.sendall(data.encode("utf-8"))

    def get_nowait(self):
        try:
            return self.incoming.get_nowait()
        except Empty:
            return None

    def close(self):
        self.running = False
        try:
            if self.sock:
                self.sock.close()
        except:
            pass
        self.sock = None