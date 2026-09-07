import sys
sys.path.append('/home/hero/code/AATSR_product/')
from util.util_ls4t import *

'''2025.9.10'''
'''hom'''

class LS4T_HOM():
    def __init__(self):
        self.hom = Hom()

    def set_structure(self,leaf_area_index,hspot):
        self.hom.set_structure(leaf_area_index,hspot)

    def set_thermal(self,temperature_soil_sunlit,temperature_soil_shaded,temperature_leaf_sunlit,temperature_leaf_shaded,):
        self.hom.set_thermal(temperature_soil_sunlit,temperature_soil_shaded,temperature_leaf_sunlit,temperature_leaf_shaded)

    def set_optical(self,wavelength,emissivity_soil,emissivity_leaf):
        self.hom.set_optical(wavelength,emissivity_soil,emissivity_leaf)

    def set_angle(self,view_zenith_angle,solar_zenith_angle,relative_azimuth_angle):
        self.hom.set_angle(view_zenith_angle,solar_zenith_angle,relative_azimuth_angle)

    def sample_bt(self):
        bt = sample_hom_bt(self.hom.temperature_leaf_sunlit,
                           self.hom.temperature_leaf_shaded,
                           self.hom.temperature_soil_sunlit,
                           self.hom.temperature_soil_shaded,
                           self.hom.leaf_area_index,
                           self.hom.hspot,
                           self.hom.wavelength,
                           self.hom.emissivity_soil,
                           self.hom.emissivity_leaf,
                           self.hom.viewing_zenith_angle,
                           self.hom.solar_zenith_angle,
                           self.hom.relative_azimuth_angle)
        return bt

    def sample_emis(self):
        emis = sample_hom_Emis(self.hom.leaf_area_index,
                               self.hom.hspot,
                               self.hom.wavelength,
                               self.hom.emissivity_soil,
                               self.hom.emissivity_leaf,
                               self.hom.viewing_zenith_angle,
                               self.hom.solar_zenith_angle,
                               self.hom.relative_azimuth_angle)
        return emis

    def cal_effective_emis(self,component_number=2):
        w = cal_effective_emissivity_hom(self.hom.leaf_area_index,
                                         self.hom.hspot,
                                         self.hom.wavelength,
                                         self.hom.emissivity_soil,
                                         self.hom.emissivity_leaf,
                                         self.hom.viewing_zenith_angle,
                                         self