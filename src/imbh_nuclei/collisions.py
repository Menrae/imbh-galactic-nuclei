"""Direct BH-star collisions (Newton et al. 2026, Section 4.2).

See docs/equations.md#section-42--direct-collisions-with-stars for full derivations,
citations (S. C. Rose et al. 2020 for f1/f2; Bondi & Hoyle 1944 for accretion; Volonteri
et al. 2013 / Bardeen 1970 for spin change), and the flagged ambiguities (Eq. 19/20 rate
notation, Eq. 21 exponent).
"""

from __future__ import annotations

import numpy as np
from scipy.special import hyp2f1

from imbh_nuclei.constants import C_KMS, G_ASTRO, PC_TO_KM, R_SUN_PC, YR_TO_S
from imbh_nuclei.gw_capture import r_isco

#: Sound speed used for Bondi-Hoyle accretion (Eq. 19), J. Christensen-Dalsgaard et al. 1996.
SOUND_SPEED_KMS = 600.0

#: Accretion efficiency at the ISCO (S. C. Rose et al. 2022).
ACCRETION_EFFICIENCY = 0.1


def f1_eccentricity(e: np.ndarray, alpha: float) -> np.ndarray:
    """f1(e) eccentricity factor in the collision timescale (Eq. 18), from S. C. Rose
    et al. 2020, ApJ, 904, 113, Eq. 20.

    f1(e) = (1-e)^(1/2-alpha)/2 * 2F1(1/2, alpha-1/2; 1; 2e/(e-1))
          + (1+e)^(1/2-alpha)/2 * 2F1(1/2, alpha-1/2; 1; 2e/(e+1))

    At e=0, 2F1(a,b;c;0)=1 identically, so f1(0)=1 (recovers the non-eccentric Eq. 18 form).
    """
    e = np.asarray(e, dtype=float)
    term1 = (1 - e) ** (0.5 - alpha) / 2 * hyp2f1(0.5, alpha - 0.5, 1, 2 * e / (e - 1))
    term2 = (1 + e) ** (0.5 - alpha) / 2 * hyp2f1(0.5, alpha - 0.5, 1, 2 * e / (e + 1))
    return term1 + term2


def f2_eccentricity(e: np.ndarray, alpha: float) -> np.ndarray:
    """f2(e) eccentricity factor in the collision timescale (Eq. 18), from S. C. Rose
    et al. 2020, ApJ, 904, 113, Eq. 21.

    f2(e) = (1-e)^(3/2-alpha)/2 * 2F1(1/2, alpha-3/2; 1; 2e/(e-1))
          + (1+e)^(3/2-alpha)/2 * 2F1(1/2, alpha-3/2; 1; 2e/(e+1))

    At e=0, f2(0)=1 (same identity as f1).
    """
    e = np.asarray(e, dtype=float)
    term1 = (1 - e) ** (1.5 - alpha) / 2 * hyp2f1(0.5, alpha - 1.5, 1, 2 * e / (e - 1))
    term2 = (1 + e) ** (1.5 - alpha) / 2 * hyp2f1(0.5, alpha - 1.5, 1, 2 * e / (e + 1))
    return term1 + term2


def bh_schwarzschild_radius(m_bh: np.ndarray) -> np.ndarray:
    """Schwarzschild radius of a BH [pc], used as its effective radius in r_c.

    NOT explicitly given in Newton et al. 2026 (they only say "rc is the sum of the radii
    of the interacting objects" without defining the BH's radius) -- the Schwarzschild
    radius is the natural choice for a compact object's physical size in a collision cross
    section. Numerically negligible next to R_sun (~1e4x smaller for stellar-mass BHs), so
    this choice does not materially affect results either way. See paper/limitations.md.
    """
    m_bh = np.asarray(m_bh, dtype=float)
    return 2 * G_ASTRO * m_bh / C_KMS**2


def collision_timescale(
    m_bh: np.ndarray,
    n_star: np.ndarray,
    sigma: np.ndarray,
    e_bh: np.ndarray,
    alpha_star: float,
) -> np.ndarray:
    """Direct BH-star collision timescale (Eq. 18).

    t_coll^-1 = pi*n*sigma*[f1(e)*rc^2 + f2(e)*rc*2G(m_BH+Msun)/sigma^2]

    Parameters
    ----------
    m_bh : array_like
        BH mass [Msun].
    n_star : array_like
        Stellar number density [pc^-3] (= rho_star/Msun, Eq. 3), at the BH's semimajor axis.
    sigma : array_like
        Velocity dispersion [km/s] (Eq. 1, alpha=alpha_star), at the same radius.
    e_bh : array_like
        BH's orbital eccentricity about the SMBH.
    alpha_star : float
        Stellar density slope, passed through to f1/f2.

    Returns
    -------
    ndarray
        t_coll [yr].
    """
    m_bh = np.asarray(m_bh, dtype=float)
    n_star = np.asarray(n_star, dtype=float)
    sigma = np.asarray(sigma, dtype=float)
    e_bh = np.asarray(e_bh, dtype=float)

    r_c = bh_schwarzschild_radius(m_bh) + R_SUN_PC  # pc
    f1 = f1_eccentricity(e_bh, alpha_star)
    f2 = f2_eccentricity(e_bh, alpha_star)
    m_tot = m_bh + 1.0  # BH + 1 Msun star

    bracket = f1 * r_c**2 + f2 * r_c * 2 * G_ASTRO * m_tot / sigma**2  # pc^2
    rate_per_pc_per_kms = np.pi * n_star * sigma * bracket  # pc^-3 * km/s * pc^2 = km/(s*pc)
    t_seconds = (1.0 / rate_per_pc_per_kms) * PC_TO_KM
    return t_seconds / YR_TO_S


def bondi_hoyle_rate(m_i: np.ndarray, sigma: np.ndarray, c_s: float = SOUND_SPEED_KMS) -> np.ndarray:
    """Bondi-Hoyle accretion rate onto the BH (Eq. 19) [Msun / (km/s / pc)... see note].

    mdot_BH = 4*pi*G^2*m_i^2*rho_star / (c_s^2 + sigma^2)^(3/2)

    rho_star = 3*Msun / (4*pi*R_sun^3) -- the star's own internal density, NOT the cluster
    stellar density profile (same symbol rho_star is overloaded in the paper for two
    different quantities; disambiguated here by context).

    Returns the rate in Msun / yr (unit conversion applied internally).
    """
    m_i = np.asarray(m_i, dtype=float)
    sigma = np.asarray(sigma, dtype=float)
    rho_star_internal = 3.0 / (4 * np.pi * R_SUN_PC**3)  # Msun/pc^3, the STAR's own density
    mdot = 4 * np.pi * G_ASTRO**2 * m_i**2 * rho_star_internal / (c_s**2 + sigma**2) ** 1.5
    # mdot has units Msun^2 * [pc Msun^-1 (km/s)^2]^2 * pc^-3 / (km/s)^3 = Msun * (km/s) / pc
    # convert (km/s)/pc -> 1/yr via PC_TO_KM, YR_TO_S
    return mdot * (YR_TO_S / PC_TO_KM)


def captured_mass(mdot_bh: np.ndarray, r_star_pc: float, sigma: np.ndarray) -> np.ndarray:
    """Captured mass from a single collision (Eq. 20).

    m_cap = min(mdot_BH * t_star_cross, 1 Msun), t_star_cross ~ R_star / sigma

    NOTE (see paper/limitations.md#mdot-vs-delta-m-notation): the paper's Eq. 20 multiplies
    "Delta m_BH" (no dot) by the crossing time; we use the Eq. 19 rate mdot_BH here since
    only rate*time is dimensionally a mass.

    Parameters
    ----------
    mdot_bh : array_like
        Accretion rate [Msun/yr] from bondi_hoyle_rate.
    r_star_pc : float
        Stellar radius [pc] (use R_SUN_PC for a 1 Msun star).
    sigma : array_like
        Velocity dispersion [km/s].

    Returns
    -------
    ndarray
        Captured mass [Msun].
    """
    mdot_bh = np.asarray(mdot_bh, dtype=float)
    sigma = np.asarray(sigma, dtype=float)
    t_cross_s = (r_star_pc * PC_TO_KM) / sigma  # pc / (km/s) -> s
    t_cross_yr = t_cross_s / YR_TO_S
    return np.minimum(mdot_bh * t_cross_yr, 1.0)


def accreted_mass(
    m_cap: np.ndarray, m_bh: np.ndarray, eta: float = ACCRETION_EFFICIENCY
) -> np.ndarray:
    """Net mass accreted after radiative feedback losses.

    Delta m_BH = m_cap * v_esc / (c * eta), v_esc = sqrt(2*G*m_BH/R_sun), eta=0.1
    """
    m_cap = np.asarray(m_cap, dtype=float)
    m_bh = np.asarray(m_bh, dtype=float)
    v_esc = np.sqrt(2 * G_ASTRO * m_bh / R_SUN_PC)  # km/s
    return m_cap * v_esc / (C_KMS * eta)


def spin_change(chi_i: np.ndarray, m_i: np.ndarray, m_f: np.ndarray, prograde: np.ndarray) -> np.ndarray:
    """Final BH spin after a collision (Eq. 21), following M. Volonteri et al. 2013 /
    J. M. Bardeen 1970.

    chi_f = (r_ISCO^(1/2)/3) * (m_i/m_f) * [4 - sqrt(3*(m_i/m_f)^2*r_ISCO - 2)]
            if m_f/m_i <= sqrt(r_ISCO), else 1

    NOTE (see paper/limitations.md#eq21-exponent-discrepancy): Newton et al. 2026's
    published Eq. 21 prints exponent 1/3 on r_ISCO; the cited source (Volonteri et al. 2013,
    Eq. 14) has 1/2. We implement 1/2, following the source, and flag this discrepancy.

    Parameters
    ----------
    chi_i : array_like
        BH spin before the collision (used to evaluate r_ISCO).
    m_i, m_f : array_like
        BH mass before and after the collision [Msun].
    prograde : array_like of bool
        Whether the accretion disk is prograde (True) or retrograde (False) w.r.t. chi_i.

    Returns
    -------
    ndarray
        Final spin magnitude.
    """
    chi_i = np.asarray(chi_i, dtype=float)
    m_i = np.asarray(m_i, dtype=float)
    m_f = np.asarray(m_f, dtype=float)
    prograde = np.asarray(prograde, dtype=bool)

    r_isco_val = np.where(
        prograde, r_isco(chi_i, prograde=True), r_isco(chi_i, prograde=False)
    )
    mass_ratio = m_f / m_i
    saturated = mass_ratio >= np.sqrt(r_isco_val)

    prefactor = np.sqrt(r_isco_val) / 3 * (m_i / m_f)
    inner = 3 * (m_i / m_f) ** 2 * r_isco_val - 2
    unsaturated_value = prefactor * (4 - np.sqrt(np.clip(inner, 0, None)))

    return np.where(saturated, 1.0, unsaturated_value)
