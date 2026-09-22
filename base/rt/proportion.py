"""Canopy radiative-transfer helpers: component visible proportions."""


# ---------------------------------------------------------------------------
# SLSTR case dependencies, moved verbatim from the run project on 2026-09-16
# ---------------------------------------------------------------------------
from base.rt.gap import gap_probability_hom_analytical
from base.rt.hotspot import hotspot_analytical, hotspot_layer


def proportion_bidirectional_hom_one(lai,hspot,vza,sza,vsa):
    Psoil = gap_probability_hom_analytical(lai, vza)
    Pleaf = 1 - Psoil
    Psoil_sunlit = hotspot_layer(lai, hspot, vza, sza, vsa)
    Pleaf_sunlit = hotspot_analytical(lai, hspot, vza, sza, vsa)
    Psoil_shaded = Psoil - Psoil_sunlit
    Pleaf_shaded = Pleaf - Pleaf_sunlit
    return Psoil_sunlit,Psoil_shaded,Pleaf_sunlit,Pleaf_shaded

