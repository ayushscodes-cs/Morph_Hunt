"""
Client-side networking: connects to the server, spins up a background
thread that continuously receives messages and pushes them onto a
thread-safe queue for the main (Ursina) thread to drain each frame.
"""
import queue
import socket
import threading

from config import settings
from game.game_state import send_json, recv_json, MSG_JOIN


class NetworkClient:
    def __init__(self):
        self.sock = None
        self.connected = False
        self.player_id = None
        self.is_host = False
        self.incoming: "queue.Queue[dict]" = queue.Queue()
        self._recv_thread = None

    def connect(self, host: str, port: int, name: str, char_idx: int = 1) -> (bool, str):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(settings.CONNECT_TIMEOUT)
            self.sock.connect((host, port))
            self.sock.settimeout(None)
        except OSError as e:
            return False, f"Could not connect: {e}"

        try:
            welcome = recv_json(self.sock)
        except (ConnectionError, ValueError, OSError) as e:
            return False, f"Handshake failed: {e}"

        if welcome.get("type") != "welcome":
            return False, "Unexpected server response."

        self.player_id = welcome.get("player_id")
        self.is_host = bool(welcome.get("is_host"))
        self.connected = True

        from client.profile import get_profile_id
        self.send({"type": MSG_JOIN, "profile_id": get_profile_id(), "name": name, "char_idx": char_idx})

        self._recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
        self._recv_thread.start()
        return True, "ok"

    def _recv_loop(self):
        while self.connected:
            try:
                msg = recv_json(self.sock)
            except (ConnectionError, ValueError, OSError):
                self.connected = False
                self.incoming.put({"type": "_disconnected"})
                break
            self.incoming.put(msg)

    def send(self, payload: dict):
        if not self.connected or not self.sock:
            return
        try:
            send_json(self.sock, payload)
        except OSError:
            self.connected = False

    def poll(self):
        """Drain and return all queued incoming messages (non-blocking)."""
        msgs = []
        while True:
            try:
                msgs.append(self.incoming.get_nowait())
            except queue.Empty:
                break
        return msgs

    def disconnect(self):
        self.connected = False
        if self.sock:
            try:
                self.sock.close()
            except OSError:
                pass
