"""Physical constants in the unit system used throughout this package.

Unit convention (chosen for the galactic-nucleus scales in Newton et al. 2026):
    length     : pc
    mass       : Msun
    velocity   : km/s
    time       : yr  (except where noted, e.g. relaxation timescales in Gyr)

See docs/equations.md#units-and-conventions.
"""

#: Gravitational constant in pc, Msun, km/s units: G = 4.30091e-3 pc Msun^-1 (km/s)^2.
#: Standard value used throughout galactic dynamics (e.g. Bovy 2015 galpy documentation).
G_ASTRO = 4.30091e-3  # pc Msun^-1 (km/s)^2

#: Speed of light in km/s.
C_KMS = 299792.458

#: pc -> km
PC_TO_KM = 3.0856775814913673e13

#: yr -> s
YR_TO_S = 3.15576e7

#: Newton's constant in SI (m^3 kg^-1 s^-2), for cross-checks / equations quoted in SI.
G_SI = 6.674e-11

#: Solar radius in pc (6.957e5 km / PC_TO_KM).
R_SUN_PC = 6.957e5 / PC_TO_KM
