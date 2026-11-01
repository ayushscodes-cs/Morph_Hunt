import os
import json
import uuid

_profile_id = None
_profile_name = None

def _get_path():
    return os.path.join(os.path.expanduser("~"), ".morph_hunt_profile.json")

def _load_profile():
    global _profile_id, _profile_name
    if _profile_id is not None:
        return
    path = _get_path()
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                data = json.load(f)
                _profile_id = data.get("profile_id")
                _profile_name = data.get("name")
        except Exception:
            pass
    if not _profile_id:
        _profile_id = str(uuid.uuid4())
        _save_profile()

def _save_profile():
    path = _get_path()
    with open(path, "w") as f:
        json.dump({"profile_id": _profile_id, "name": _profile_name}, f)

def get_profile_id():
    _load_profile()
    return _profile_id

def get_profile_name():
    _load_profile()
    return _profile_name

def set_profile_name(name):
    global _profile_name
    _load_profile()
    _profile_name = name
    _save_profile()
