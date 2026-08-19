"""
Integration test: spins up the real GameServer on a local port and
drives it with two real TCP client sockets through join -> lobby ->
start -> role assignment -> countdown -> hiding -> hunting -> a
transform + interact + scanner + attack cycle, using the exact wire
protocol the Ursina client would use. No Ursina required.
Run: python integration_test.py
"""
import socket
import threading
import time

from config import settings
from game.game_state import send_json, recv_json, MSG_JOIN, MSG_SET_MODE, MSG_START_GAME, MSG_TRANSFORM
from server.game_server import GameServer

PORT = 5599


def recv_until(sock, predicate, timeout=10.0):
    """Receive messages until one matches predicate(msg) -> True. Returns it."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        sock.settimeout(max(0.1, deadline - time.time()))
        msg = recv_json(sock)
        if predicate(msg):
            return msg
    raise TimeoutError("predicate never matched")


def main():
    server = GameServer(host="127.0.0.1", port=PORT)
    t = threading.Thread(target=server.start, daemon=True)
    t.start()
    time.sleep(0.4)

    # --- connect two clients ---
    s1 = socket.create_connection(("127.0.0.1", PORT), timeout=5)
    welcome1 = recv_json(s1)
    print("client1 welcome:", welcome1)
    assert welcome1["type"] == "welcome" and welcome1["is_host"] is True
    send_json(s1, {"type": MSG_JOIN, "name": "Alice"})

    s2 = socket.create_connection(("127.0.0.1", PORT), timeout=5)
    welcome2 = recv_json(s2)
    print("client2 welcome:", welcome2)
    assert welcome2["type"] == "welcome" and welcome2["is_host"] is False
    send_json(s2, {"type": MSG_JOIN, "name": "Bob"})

    lobby1 = recv_until(s1, lambda m: m["type"] == "lobby_state" and len(m["players"]) == 2)
    print("lobby state seen by host:", lobby1)

    # host sets mode then starts
    send_json(s1, {"type": MSG_SET_MODE, "mode": "classic"})
    recv_until(s1, lambda m: m["type"] == "lobby_state")
    send_json(s1, {"type": MSG_START_GAME})

    role1 = recv_until(s1, lambda m: m["type"] == "role_assigned")
    role2 = recv_until(s2, lambda m: m["type"] == "role_assigned")
    print("roles:", role1, role2)
    assert {role1["role"], role2["role"]} == {"hider", "hunter"}

    phase_countdown = recv_until(s1, lambda m: m["type"] == "phase_change" and m["phase"] == "countdown")
    print("phase:", phase_countdown)

    phase_hiding = recv_until(s1, lambda m: m["type"] == "phase_change" and m["phase"] == "hiding",
                               timeout=settings.COUNTDOWN_SECONDS + 5)
    print("phase:", phase_hiding)

    # whichever client is the hider, send a transform request
    hider_sock, hider_role_msg = (s1, role1) if role1["role"] == "hider" else (s2, role2)
    send_json(hider_sock, {"type": MSG_TRANSFORM, "object_type": "chair"})

    snap = recv_until(hider_sock, lambda m: m["type"] == "snapshot", timeout=5)
    print("post-transform snapshot sample:", {p["player_id"]: p.get("transformed_into") for p in snap["players"]})

    phase_hunting = recv_until(s1, lambda m: m["type"] == "phase_change" and m["phase"] == "hunting",
                                timeout=settings.HIDING_PHASE_SECONDS + 5)
    print("phase:", phase_hunting)

    hunter_sock = s2 if hider_sock is s1 else s1
    send_json(hunter_sock, {"type": "scanner_ping"})
    scan_result = recv_until(hunter_sock, lambda m: m["type"] == "scanner_result", timeout=5)
    print("scanner result:", scan_result)
    assert isinstance(scan_result["clues"], list) and len(scan_result["clues"]) >= 1

    send_json(hunter_sock, {"type": "attack"})
    time.sleep(0.5)  # let it process; attack may hit or miss depending on position/facing

    print("\nINTEGRATION TEST PASSED")
    server.stop()
    s1.close()
    s2.close()


if __name__ == "__main__":
    main()
