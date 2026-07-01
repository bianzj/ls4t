from util_base import *
from util_ls4t import *

'''2025.9.9'''
'''sample 类代码'''

class SampleLS4THom:
    def __init__(self,lai,hspot,wl,emisS,emisV,vza,sza,vaa,saa,component_number):
        self.lai = lai
        self.hspot = hspot
        self.wl = wl
        self.emisS = emisS
        self.emisV = emisV
        self.vza = vza
        self.sza = sza
        self.vaa = vaa
        self.saa = saa
        self.component_number = component_number

    def run(self):
        w, psoil = cal_effective_emissivity_hom(
            lai=self.lai,
            hspot=self.hspot,
            wl=self.wl,
            emisS=self.emisS,
            emisV=self.emisV,
            vza=self.vza,
            sza=self.sza,
            vaa=self.vaa,
            saa=self.saa,
            component_number=self.component_number
        )
        return w, psoil
    
if __name__ == "__main__":
    # 测试代码
    sample = SampleLS4THom(
        lai=3.0,
        hspot=0.1,
        wl=11.0,
        emisS=0.93,
        emisV=0.96,
        vza=30.0,
        sza=45.0,
        vaa=150.0,
        saa=180.0,
        component_number=2
    )
    sample.lai = 2.5  # 修改LAI值
    w, psoil = sample.run()
    print(f"计算结果 - 亮温: {w}, 土壤比例: {psoil}")