from direct.showbase.ShowBase import ShowBase
from panda3d.core import get_model_path

class TestApp(ShowBase):
    def __init__(self):
        super().__init__(windowType='none')
        get_model_path().appendDirectory('/d/Ayush/Ayush workspaces/morph_hunt/')
        try:
            model = self.loader.loadModel('assets/models/furniture/Models/chair.obj')
            print("Successfully loaded OBJ model:", model)
        except Exception as e:
            print("Failed to load OBJ model:", e)
            
        try:
            model = self.loader.loadModel('assets/models/characters/Model/characterMedium.fbx')
            print("Successfully loaded FBX model:", model)
        except Exception as e:
            print("Failed to load FBX model:", e)
        
        self.userExit()

TestApp().run()
