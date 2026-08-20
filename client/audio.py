"""
Procedural sound effects synthesizer for Morph Hunt.
Provides instant audio feedback for all game actions using native Windows audio APIs.
Thread-safe and non-blocking.
"""
import sys
import threading
import time


def _play_async(fn):
    threading.Thread(target=fn, daemon=True).start()


class SoundManager:
    @staticmethod
    def laser():
        """Blaster shot zap."""
        if sys.platform == "win32":
            import winsound
            def _s():
                winsound.Beep(1200, 35)
                winsound.Beep(750, 45)
            _play_async(_s)

    @staticmethod
    def hit():
        """Hitmarker chime when hitting an enemy."""
        if sys.platform == "win32":
            import winsound
            def _s():
                winsound.Beep(1800, 40)
                winsound.Beep(2400, 50)
            _play_async(_s)

    @staticmethod
    def morph():
        """Hider transform whoosh sound."""
        if sys.platform == "win32":
            import winsound
            def _s():
                winsound.Beep(500, 35)
                winsound.Beep(850, 45)
                winsound.Beep(1300, 60)
            _play_async(_s)

    @staticmethod
    def scanner():
        """Hunter sonar ping."""
        if sys.platform == "win32":
            import winsound
            def _s():
                winsound.Beep(1600, 80)
                time.sleep(0.04)
                winsound.Beep(2100, 100)
            _play_async(_s)

    @staticmethod
    def taunt():
        """Prop taunt whistle."""
        if sys.platform == "win32":
            import winsound
            def _s():
                for freq in (800, 1200, 1600, 2000):
                    winsound.Beep(freq, 40)
            _play_async(_s)

    @staticmethod
    def countdown():
        """Countdown tick."""
        if sys.platform == "win32":
            import winsound
            def _s():
                winsound.Beep(880, 80)
            _play_async(_s)

    @staticmethod
    def eliminated():
        """Player elimination thud."""
        if sys.platform == "win32":
            import winsound
            def _s():
                winsound.Beep(350, 120)
                winsound.Beep(200, 180)
            _play_async(_s)
