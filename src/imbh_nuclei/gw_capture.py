"""GW capture between single black holes (Newton et al. 2026, Section 4.1).

See docs/equations.md#section-41--gw-capture-between-single-black-holes for full
derivations, citations (O'Leary, Kocsis & Loeb 2009; Barausse & Rezzolla 2009; Barausse,
Morozova & Rezzolla 2012; Bardeen, Press & Teukolsky 1972; Li & Bambi 2014), and unit
conventions.

Length/mass/velocity follow the package convention (pc, Msun, km/s); ISCO/spin quantities
(r_isco, Z1, Z2, E_ISCO) are dimensionless, computed in natural units (c=G=1) as in the
source papers.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

from imbh_nuclei.constants import C_KMS, G_ASTRO, PC_TO_KM, YR_TO_S

#: Remnant-mass fitting constants (Eq. 8), from C. Reisswig et al. 2009 as tabulated in
#: E. Barausse, V. Morozova, & L. Rezzolla 2012 (see docs/equations.md).
P0 = 0.04827
P1 = 0.01707

#: Aligned-spin final-spin fitting constants, E. Barausse & L. Rezzolla 2009, ApJL, 704,
#: L40, Eqs. 1-3 (arXiv:0904.2577). Needed to compute "L" (their script-ell) in Newton et
#: al. 2026 Eq. 10 -- see docs/equations.md#section-41 ambiguity note: N26 uses this "L"
#: without giving its formula, tracing back to this source resolves it.
S4 = -0.1229
S5 = 0.4537
T0 = -2.8904
T2 = -3.5171
T3 = 2.5763


def symmetric_mass_ratio(m1: ArrayLike, m2: ArrayLike) -> np.ndarray:
    """eta = m1*m2 / (m1+m2)^2. See docs/equations.md#section-41."""
    m1 = np.asarray(m1, dtype=float)
    m2 = np.asarray(m2, dtype=float)
    return m1 * m2 / (m1 + m2) ** 2


def b_max(m1: ArrayLike, m2: ArrayLike, v_rel: ArrayLike) -> np.ndarray:
    """Maximum impact parameter for GW capture (Eq. 4).

    b_max = (340*pi*eta/3)^(1/7) * (G*M_tot/c^2) * (v_rel/c)^(-9/7)

    Parameters
    ----------
    m1, m2 : array_like
        BH masses [Msun].
    v_rel : array_like
        Relative velocity at infinity [km/s] -- taken to be sigma(r) (Eq. 1) evaluated
        with alpha=alpha_bh, per docs/equations.md.

    Returns
    -------
    ndarray
        b_max [pc].
    """
    m1 = np.asarray(m1, dtype=float)
    m2 = np.asarray(m2, dtype=float)
    v_rel = np.asarray(v_rel, dtype=float)
    eta = symmetric_mass_ratio(m1, m2)
    m_tot = m1 + m2
    gm_over_c2 = G_ASTRO * m_tot / C_KMS**2  # pc
    return (340 * np.pi * eta / 3) ** (1 / 7) * gm_over_c2 * (v_rel / C_KMS) ** (-9 / 7)


def b_min(m1: ArrayLike, m2: ArrayLike, v_rel: ArrayLike) -> np.ndarray:
    """Minimum impact parameter; b < b_min is a direct collision (Eq. 5).

    b_min = 4*G*M_tot/c^2 * (v_rel/c)^(-1)
    """
    m1 = np.asarray(m1, dtype=float)
    m2 = np.asarray(m2, dtype=float)
    v_rel = np.asarray(v_rel, dtype=float)
    m_tot = m1 + m2
    gm_over_c2 = G_ASTRO * m_tot / C_KMS**2  # pc
    return 4 * gm_over_c2 * (v_rel / C_KMS) ** (-1)


def capture_cross_section(m1: ArrayLike, m2: ArrayLike, v_rel: ArrayLike) -> np.ndarray:
    """GW capture cross section (Eq. 6): A_cap = pi*(b_max^2 - b_min^2). Units: pc^2.

    NOTE (not addressed in N26): b_max ~ v_rel^(-9/7) falls off faster than
    b_min ~ v_rel^(-1), so at sufficiently high v_rel (deep in the cusp, close to the
    SMBH) b_max can drop below b_min -- i.e. every encounter close enough to matter is
    already a direct collision, not a "capture," and the GW-capture channel is
    physically closed. N26 only remarks that "the cross section as set by bmin is so
    small that including or excluding these interactions does not change our results,"
    which is true in the outer cusp but does not address this inner-region sign flip.
    Clamped at 0 here (capture_timescale then returns +inf for those cases) rather than
    silently returning the unphysical negative cross section from a literal reading of
    Eq. 6. Found via a full-loop smoke test at small semimajor axis, not from the paper
    text -- see paper/limitations.md.
    """
    bmax = b_max(m1, m2, v_rel)
    bmin = b_min(m1, m2, v_rel)
    return np.maximum(0.0, np.pi * (bmax**2 - bmin**2))


def capture_timescale(
    m1: ArrayLike, m2: ArrayLike, v_rel: ArrayLike, n_bh: ArrayLike
) -> np.ndarray:
    """GW capture timescale (Eq. 7): t_GW = (A_cap * n_BH * sigma)^-1.

    v_rel doubles as sigma here, per N26 (relative velocity at infinity = velocity
    dispersion, Eq. 1).

    Parameters
    ----------
    m1, m2 : array_like
        BH masses [Msun].
    v_rel : array_like
        Velocity dispersion / relative velocity [km/s].
    n_bh : array_like
        BH number density [pc^-3] (Eq. 2), evaluated at the same radius as v_rel.

    Returns
    -------
    ndarray
        t_GW [yr]. +inf where capture_cross_section is 0 (capture channel physically
        closed at that velocity -- see capture_cross_section's docstring).
    """
    a_cap = capture_cross_section(m1, m2, v_rel)  # pc^2
    n_bh = np.asarray(n_bh, dtype=float)
    v_rel = np.asarray(v_rel, dtype=float)
    rate_per_pc_per_kms = a_cap * n_bh * v_rel  # pc^-1 * km/s -- see unit note below
    with np.errstate(divide="ignore"):
        t_pc_per_kms = 1.0 / rate_per_pc_per_kms  # pc / (km/s); +inf where rate is 0
    t_seconds = t_pc_per_kms * PC_TO_KM  # (pc/(km/s)) * (km/pc) = s
    return t_seconds / YR_TO_S


def r_isco(chi: ArrayLike, prograde: bool = True) -> np.ndarray:
    """ISCO radius in natural units (c=G=1) as a function of spin (Eq. 11).

    r_ISCO = 3 + Z2 -+ sqrt((3-Z1)(3+Z1+2*Z2))  (- for prograde, + for retrograde)

    See docs/equations.md#section-41 (Bardeen, Press & Teukolsky 1972).
    At chi=0: Z1=3, Z2=3, giving r_ISCO=6 (the Schwarzschild value) for both signs.
    """
    chi = np.asarray(chi, dtype=float)
    z1_ = z1(chi)
    z2_ = z2(chi)
    sign = -1.0 if prograde else 1.0
    return 3 + z2_ + sign * np.sqrt((3 - z1_) * (3 + z1_ + 2 * z2_))


def z1(chi: ArrayLike) -> np.ndarray:
    """Z1(chi), Eq. 12."""
    chi = np.asarray(chi, dtype=float)
    return 1 + (1 - chi**2) ** (1 / 3) * ((1 + chi) ** (1 / 3) + (1 - chi) ** (1 / 3))


def z2(chi: ArrayLike) -> np.ndarray:
    """Z2(chi), Eq. 12."""
    chi = np.asarray(chi, dtype=float)
    return np.sqrt(3 * chi**2 + z1(chi) ** 2)


def isco_energy(r_isco_value: ArrayLike) -> np.ndarray:
    """E_ISCO = sqrt(1 - 2/(3*r_ISCO)), used in Eq. 8."""
    r_isco_value = np.asarray(r_isco_value, dtype=float)
    return np.sqrt(1 - 2 / (3 * r_isco_value))


def chi_parallel(
    m1: ArrayLike, chi1_parallel: ArrayLike, m2: ArrayLike, chi2_parallel: ArrayLike
) -> np.ndarray:
    """Parallel spin component (Eq. 9): (m1^2*chi1 + m2^2*chi2)/(m1+m2)^2, projected on L.

    chi1_parallel, chi2_parallel are the L-projected components (chi_i . L_hat) already
    computed by the caller; this function combines them with the mass weighting.
    """
    m1 = np.asarray(m1, dtype=float)
    m2 = np.asarray(m2, dtype=float)
    chi1_parallel = np.asarray(chi1_parallel, dtype=float)
    chi2_parallel = np.asarray(chi2_parallel, dtype=float)
    return (m1**2 * chi1_parallel + m2**2 * chi2_parallel) / (m1 + m2) ** 2


def remnant_mass(
    m1: ArrayLike, m2: ArrayLike, chi_par: ArrayLike, prograde: bool = True
) -> np.ndarray:
    """Final merger remnant mass (Eq. 8).

    m_f/M_tot = 1 - eta(1-4eta)(1-E_ISCO) - 16*eta^2*(p0 + 4*p1*chi_par*(chi_par+1))

    Parameters
    ----------
    m1, m2 : array_like
        Progenitor BH masses [Msun].
    chi_par : array_like
        Parallel spin component (Eq. 9).
    prograde : bool
        Orbital sense for the r_ISCO(chi_par) evaluation feeding E_ISCO.

    Returns
    -------
    ndarray
        Remnant mass [Msun].
    """
    m1 = np.asarray(m1, dtype=float)
    m2 = np.asarray(m2, dtype=float)
    chi_par = np.asarray(chi_par, dtype=float)
    eta = symmetric_mass_ratio(m1, m2)
    m_tot = m1 + m2
    e_isco = isco_energy(r_isco(chi_par, prograde=prograde))
    frac = 1 - eta * (1 - 4 * eta) * (1 - e_isco) - 16 * eta**2 * (
        P0 + 4 * P1 * chi_par * (chi_par + 1)
    )
    return frac * m_tot


def final_spin(
    q: ArrayLike,
    chi1_costheta1: ArrayLike,
    chi2_costheta2: ArrayLike,
    orbital_l: ArrayLike,
) -> np.ndarray:
    """Final spin magnitude (Eq. 10).

    chi_f = min(1, |[q^2*chi2*cos(theta2) + chi1*cos(theta1)]/(1+q)^2 + q*L/(1+q)^2|)

    Parameters
    ----------
    q : array_like
        Mass ratio of the BHs.
    chi1_costheta1, chi2_costheta2 : array_like
        chi_i * cos(theta_i) products for BH 1 and 2 (cos(theta_i) = chi_i_hat . L_hat).
    orbital_l : array_like
        Orbital angular momentum magnitude L (dimensionless, in the same normalization
        as chi) -- Newton et al. 2026 does not give a formula for this; use
        orbital_ell() below (Barausse & Rezzolla 2009) to compute it.

    Returns
    -------
    ndarray
        Final spin magnitude, capped at 1.
    """
    q = np.asarray(q, dtype=float)
    chi1_costheta1 = np.asarray(chi1_costheta1, dtype=float)
    chi2_costheta2 = np.asarray(chi2_costheta2, dtype=float)
    orbital_l = np.asarray(orbital_l, dtype=float)
    value = (q**2 * chi2_costheta2 + chi1_costheta1) / (1 + q) ** 2 + q * orbital_l / (
        1 + q
    ) ** 2
    return np.minimum(1.0, np.abs(value))


def orbital_ell(q: ArrayLike, chi1_costheta1: ArrayLike, chi2_costheta2: ArrayLike) -> np.ndarray:
    """"L" (script-ell) in Eq. 10 -- NOT given a formula by Newton et al. 2026 itself.

    Traced to E. Barausse & L. Rezzolla 2009, ApJL, 704, L40 (arXiv:0904.2577), whose
    Eq. 1 gives the aligned-spin final-spin fit and Eq. 5 gives the aligned-spin
    reduction a_fin = [a1 + a2*q^2 + ell*q]/(1+q)^2 -- solving the latter for ell using
    the former as a_fin_aligned:

        a_tilde = (a1 + a2*q^2) / (1 + q^2)                        [note: (1+q^2), not (1+q)^2]
        a_fin_aligned = a_tilde + a_tilde*eta*(S4*a_tilde + S5*eta + T0)
                        + eta*(2*sqrt(3) + T2*eta + T3*eta^2)
        ell = [(1+q)^2 * a_fin_aligned - a1 - a2*q^2] / q

    where a1 = chi1*cos(theta1), a2 = chi2*cos(theta2) (the L-aligned spin components,
    matching Newton et al.'s own chi1_costheta1/chi2_costheta2 notation), and
    eta = q/(1+q)^2 is the symmetric mass ratio expressed via q.

    Self-consistency check: for fully-aligned spins (costheta1=costheta2=1), plugging
    this ell back into final_spin() exactly recovers a_fin_aligned by construction --
    verified in tests/test_gw_capture.py.

    Parameters
    ----------
    q : array_like
        Mass ratio.
    chi1_costheta1, chi2_costheta2 : array_like
        L-aligned spin components of BH 1 and 2.

    Returns
    -------
    ndarray
        ell, ready to pass as `orbital_l` to final_spin().
    """
    q = np.asarray(q, dtype=float)
    a1 = np.asarray(chi1_costheta1, dtype=float)
    a2 = np.asarray(chi2_costheta2, dtype=float)
    eta = q / (1 + q) ** 2

    a_tilde = (a1 + a2 * q**2) / (1 + q**2)
    a_fin_aligned = (
        a_tilde
        + a_tilde * eta * (S4 * a_tilde + S5 * eta + T0)
        + eta * (2 * np.sqrt(3) + T2 * eta + T3 * eta**2)
    )
    return ((1 + q) ** 2 * a_fin_aligned - a1 - a2 * q**2) / q
