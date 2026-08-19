"""
Shared constants, enums and the wire protocol used by both the server
and the client.

We deliberately avoid `pickle` for network traffic (unsafe to deserialize
data from an untrusted peer) and instead use a small length-prefixed JSON
protocol, implemented by `send_json` / `recv_json` below.
"""
import json
import socket
import struct

# ----------------------------------------------------------------------
# ROLES / PHASES
# ----------------------------------------------------------------------
ROLE_UNASSIGNED = "unassigned"
ROLE_HIDER = "hider"
ROLE_HUNTER = "hunter"
ROLE_SPECTATOR = "spectator"

PHASE_LOBBY = "lobby"
PHASE_ROLE_ASSIGN = "role_assign"
PHASE_COUNTDOWN = "countdown"
PHASE_HIDING = "hiding"
PHASE_HUNTING = "hunting"
PHASE_RESULTS = "results"

# ----------------------------------------------------------------------
# CLIENT -> SERVER MESSAGE TYPES
# ----------------------------------------------------------------------
MSG_JOIN = "join"                    # {name}
MSG_SET_READY = "set_ready"          # {ready: bool}
MSG_SET_MAP = "set_map"              # {map: str}  (host only)
MSG_SET_MODE = "set_mode"            # {mode: str} (host only)
MSG_START_GAME = "start_game"        # {} (host only)
MSG_INPUT = "input"                  # {move: [x,z], look_y, sprint, jump}
MSG_TRANSFORM = "transform"          # {object_type: str}
MSG_UNTRANSFORM = "untransform"      # {}
MSG_SCANNER = "scanner_ping"         # {}
MSG_ATTACK = "attack"                # {}
MSG_INTERACT = "interact"            # {}
MSG_CHAT = "chat"                    # {text}
MSG_LEAVE = "leave"                  # {}

# ----------------------------------------------------------------------
# SERVER -> CLIENT MESSAGE TYPES
# ----------------------------------------------------------------------
MSG_WELCOME = "welcome"              # {player_id, is_host}
MSG_LOBBY_STATE = "lobby_state"      # {players:[...], map, mode}
MSG_PHASE_CHANGE = "phase_change"    # {phase, time_left}
MSG_ROLE_ASSIGNED = "role_assigned"  # {role}
MSG_SNAPSHOT = "snapshot"            # full world snapshot
MSG_SCANNER_RESULT = "scanner_result"  # {clues: [...]}
MSG_OBJECTIVE_UPDATE = "objective_update"  # {objectives:[...]}
MSG_ELIMINATED = "eliminated"        # {player_id}
MSG_ROUND_RESULT = "round_result"    # final results payload
MSG_CHAT_BROADCAST = "chat_broadcast"  # {name, text}
MSG_ERROR = "error"                  # {message}
MSG_PLAYER_LEFT = "player_left"      # {player_id}


def send_json(sock: socket.socket, payload: dict) -> None:
    """Send a length-prefixed JSON message. Raises on socket errors."""
    data = json.dumps(payload).encode("utf-8")
    header = struct.pack("!I", len(data))
    sock.sendall(header + data)


def _recv_exact(sock: socket.socket, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("socket closed")
        buf += chunk
    return buf


def recv_json(sock: socket.socket) -> dict:
    """Blocking receive of one length-prefixed JSON message."""
    header = _recv_exact(sock, 4)
    (length,) = struct.unpack("!I", header)
    if length <= 0 or length > 10_000_000:
        raise ValueError("invalid message length")
    data = _recv_exact(sock, length)
    return json.loads(data.decode("utf-8"))
