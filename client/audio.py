import os

class SoundManager:
    _sounds = {}

    @staticmethod
    def _play(rel_path):
        from direct.showbase.ShowBaseGlobal import base
        if not hasattr(base, 'loader'):
            return
            
        if rel_path not in SoundManager._sounds:
            _base_dir = os.path.dirname(os.path.dirname(__file__))
            full_path = os.path.join(_base_dir, "new_assets", "audio", rel_path)
            try:
                from panda3d.core import Filename
                model_path = Filename.fromOsSpecific(full_path).getFullpath()
                snd = base.loader.loadSfx(model_path)
                SoundManager._sounds[rel_path] = snd
            except Exception as e:
                print(f"Audio load error: {e}")
                SoundManager._sounds[rel_path] = None
                
        snd = SoundManager._sounds[rel_path]
        if snd:
            snd.play()

    @staticmethod
    def gun_fire(weapon_idx=1):
        if weapon_idx == 1:
            SoundManager._play("assault.wav")
        elif weapon_idx == 2:
            SoundManager._play("pistol.wav")
        elif weapon_idx == 3:
            SoundManager._play("shotgun.wav")
        elif weapon_idx == 4:
            SoundManager._play("smg.wav")
        else:
            SoundManager._play("assault.wav")

    @staticmethod
    def laser(): pass
    @staticmethod
    def hit(): pass
    @staticmethod
    def morph(): pass
    @staticmethod
    def footstep(): pass
    @staticmethod
    def scanner(): pass
    @staticmethod
    def taunt(): pass
    @staticmethod
    def countdown(): pass
    @staticmethod
    def eliminated(): pass
