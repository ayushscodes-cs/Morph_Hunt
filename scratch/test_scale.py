from direct.showbase.ShowBase import ShowBase
from panda3d.core import get_model_path

class TestApp(ShowBase):
    def __init__(self):
        super().__init__(windowType='none')
        get_model_path().appendDirectory('/d/Ayush/Ayush workspaces/morph_hunt/')
        model = self.loader.loadModel('assets/models/furniture/Models/loungeSofaLong.obj')
        min_pt, max_pt = model.getTightBounds()
        print("Sofa bounds:", min_pt, max_pt)
        print("Sofa dims:", max_pt - min_pt)
        self.userExit()

TestApp().run()
