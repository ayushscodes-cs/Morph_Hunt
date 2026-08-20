"""
Entry point for Morph Hunt.
Boots the Panda3D-based ClientApp (replaces the old Ursina Ursina() call).
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from client.client import ClientApp


def main():
    app = ClientApp()
    app.run()


if __name__ == "__main__":
    main()