"""Nuclear star cluster structure (Newton et al. 2026, Section 2).

See docs/equations.md#section-2--cluster-structure for full derivations, citations, and
ambiguity notes. All three functions here have been verified directly against the
published PDF (Newton et al. 2026, Eqs. 1-3); see paper/limitations.md for the one
remaining interpretive choice (which alpha to pass to velocity_dispersion in each
dynamical-process context).
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

from imbh_nuclei.constants import G_ASTRO


def stellar_density(
    r: ArrayLike,
    rho0: float = 1.35e6,
    r0: float = 0.25,
    alpha: float = 1.25,
) -> np.ndarray:
    """Power-law stellar mass density profile.

    rho_star(r) = rho0 * (r / r0)^-alpha

    See docs/equations.md#stellar-density-profile (Newton et al. 2026, Eq. 3).

    Parameters
    ----------
    r : array_like
        Radius [pc]. Must be > 0.
    rho0 : float
        Density normalization at r0 [Msun/pc^3]. Paper default 1.35e6 (R. Genzel et al. 2010).
    r0 : float
        Normalization radius [pc]. Paper default 0.25.
    alpha : float
        Power-law cusp slope (paper default 1.25).

    Returns
    -------
    ndarray
        Stellar density [Msun/pc^3] at each r.
    """
    r = np.asarray(r, dtype=float)
    return rho0 * (r / r0) ** (-alpha)


def bh_number_density(
    r: ArrayLike,
    n0: float = 1.0e4,
    r_h: float = 1.0,
    alpha: float = 1.83,
) -> np.ndarray:
    """Power-law BH number density profile.

    n_BH(r) = n0 * (r / R_h)^-alpha

    See docs/equations.md#bh-number-density-profile (Newton et al. 2026, Eq. 2).
    Normalization confirmed directly from the PDF: n0 = 1e4 pc^-3, R_h = 1 pc (the
    SMBH's sphere of influence), alpha ~= 1.83, based on the Fokker-Planck BH density
    profile of D. Aharon & H. B. Perets (2016).

    Parameters
    ----------
    r : array_like
        Radius [pc]. Must be > 0.
    n0 : float
        Number density normalization at R_h [pc^-3]. Paper value: 1e4.
    r_h : float
        SMBH sphere-of-influence normalization radius [pc]. Paper value: 1.0.
    alpha : float
        Power-law cusp slope (paper default 1.83).

    Returns
    -------
    ndarray
        BH number density [pc^-3] at each r.
    """
    r = np.asarray(r, dtype=float)
    return n0 * (r / r_h) ** (-alpha)


def velocity_dispersion(r: ArrayLike, m_smbh: float, alpha: float) -> np.ndarray:
    """Isotropic velocity dispersion in the SMBH-dominated regime.

    sigma(r) = sqrt(G * M_SMBH / [(alpha + 1) * r])

    See docs/equations.md#velocity-dispersion-profile (Newton et al. 2026, Eq. 1),
    confirmed directly against the published PDF. alpha is "the slope of the density
    profile" -- the paper is used with two different density slopes (alpha_star for
    stars, alpha_bh for BHs), and does not explicitly restate which one governs sigma
    in every usage. Callers MUST pass the alpha appropriate to the context (see
    paper/limitations.md#velocity-dispersion-alpha-choice for the resolution adopted
    here: alpha_star when paired with the stellar density in the collision timescale,
    Eq. 18; alpha_bh when paired with the BH density in the GW capture timescale, Eq. 7).

    Parameters
    ----------
    r : array_like
        Radius [pc]. Must be > 0.
    m_smbh : float
        SMBH mass [Msun].
    alpha : float
        Slope of the *relevant* population's density profile (alpha_star or alpha_bh
        depending on context -- see docstring above).

    Returns
    -------
    ndarray
        Velocity dispersion [km/s] at each r.
    """
    r = np.asarray(r, dtype=float)
    return np.sqrt(G_ASTRO * m_smbh / ((alpha + 1.0) * r))
