"""
Entry point for Morph Hunt.
Boots the Panda3D-based ClientApp (replaces the old Ursina Ursina() call).
"""
import os
import sys
from panda3d.core import loadPrcFileData

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# PyInstaller puts data files in sys._MEIPASS when bundled
if hasattr(sys, '_MEIPASS'):
    base_dir = sys._MEIPASS
    # Force Panda3D to load the OpenGL graphics pipe and OpenAL audio pipe when bundled
    loadPrcFileData("", "load-display pandagl")
    loadPrcFileData("", "audio-library-name p3openal_audio")
    loadPrcFileData("", "load-file-type p3assimp")
else:
    base_dir = os.path.abspath(os.path.dirname(__file__))

from panda3d.core import getModelPath
getModelPath().appendDirectory(base_dir)

# Ensure gltf loader is bundled by PyInstaller and explicitly register it
# because PyInstaller breaks entry_points which panda3d relies on for finding plugins
import gltf
from gltf._loader import GltfLoader
from panda3d.core import LoaderFileTypeRegistry
LoaderFileTypeRegistry.getGlobalPtr().registerType(GltfLoader)

from client.client import ClientApp


def main():
    app = ClientApp()
    app.run()


if __name__ == "__main__":
    main()