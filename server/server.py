"""
Dedicated headless server entry point.

Run with:  python server/server.py [port]
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import settings
from server.game_server import GameServer


def main():
    port = settings.DEFAULT_PORT
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port '{sys.argv[1]}', using default {settings.DEFAULT_PORT}")
    server = GameServer(host=settings.DEFAULT_HOST, port=port)
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n[server] shutting down")
        server.stop()


if __name__ == "__main__":
    main()
