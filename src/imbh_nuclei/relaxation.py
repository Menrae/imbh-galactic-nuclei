"""Relaxation and dynamical friction (Newton et al. 2026, Section 4.3).

See docs/equations.md#section-43--relaxation-and-dynamical-friction. The Coulomb
logarithm ln(Lambda) and the "average object mass" <M_avg> are both left as explicit,
required arguments rather than given silent defaults -- neither is pinned to a numeric
prescription in the paper text (see paper/limitations.md#average-object-mass and the
coulomb-logarithm note below).
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

from imbh_nuclei.constants import G_ASTRO, PC_TO_KM, YR_TO_S


def average_object_mass(
    n_star: ArrayLike, n_bh: ArrayLike, mean_bh_mass: float, star_mass: float = 1.0
) -> np.ndarray:
    """Number-density-weighted local mean object mass, <M_avg> in Eq. 22.

    <M_avg>(r) = [n_star(r)*star_mass + n_BH(r)*mean_bh_mass] / [n_star(r) + n_BH(r)]

    NOT given explicitly in Newton et al. 2026 (just "the average object mass") -- see
    paper/limitations.md#average-object-mass for the reasoning behind this resolution.
    """
    n_star = np.asarray(n_star, dtype=float)
    n_bh = np.asarray(n_bh, dtype=float)
    return (n_star * star_mass + n_bh * mean_bh_mass) / (n_star + n_bh)


def relaxation_timescale(
    sigma: ArrayLike, rho: ArrayLike, mean_object_mass: ArrayLike, coulomb_log: float
) -> np.ndarray:
    """Two-body relaxation timescale (Eq. 22).

    t_relax = 0.34 * sigma^3 / (G^2 * rho * <M_avg> * ln(Lambda))

    NOTE on ln(Lambda): Newton et al. 2026 does not give a numeric prescription for the
    Coulomb logarithm, citing Binney & Tremaine 2008 generically. A common choice in this
    exact subfield (a single-mass-dominated cusp around an SMBH) is ln(Lambda) ~
    ln(M_SMBH / <m>); callers must supply a value explicitly -- no default is assumed here.

    Parameters
    ----------
    sigma : array_like
        Velocity dispersion [km/s].
    rho : array_like
        Local mass density [Msun/pc^3].
    mean_object_mass : array_like
        <M_avg> [Msun] -- see average_object_mass.
    coulomb_log : float
        ln(Lambda).

    Returns
    -------
    ndarray
        t_relax [yr].
    """
    sigma = np.asarray(sigma, dtype=float)
    rho = np.asarray(rho, dtype=float)
    mean_object_mass = np.asarray(mean_object_mass, dtype=float)

    t_pc_per_kms = 0.34 * sigma**3 / (G_ASTRO**2 * rho * mean_object_mass * coulomb_log)
    t_seconds = t_pc_per_kms * PC_TO_KM
    return t_seconds / YR_TO_S


def segregation_timescale(
    m_bh: ArrayLike,
    sigma: ArrayLike,
    rho_star: ArrayLike,
    coulomb_log: float,
    star_mass: float = 1.0,
) -> np.ndarray:
    """Mass-segregation timescale (Eq. 23).

    t_seg ~= (M_star / m_BH) * t_relax(<M_avg>=M_star, rho=rho_star)

    i.e. the relaxation timescale evaluated with the *stellar* population parameters
    (not the two-component <M_avg> used in Eq. 22), scaled down by M_star/m_BH.

    Parameters
    ----------
    m_bh : array_like
        Mass of the sinking BH [Msun].
    sigma : array_like
        Velocity dispersion [km/s] at the relevant radius.
    rho_star : array_like
        Stellar density [Msun/pc^3] (Eq. 3) at the relevant radius.
    coulomb_log : float
        ln(Lambda).
    star_mass : float
        Field star mass [Msun], default 1.0 (paper's uniform stellar population).

    Returns
    -------
    ndarray
        t_seg [yr].
    """
    m_bh = np.asarray(m_bh, dtype=float)
    t_relax_star = relaxation_timescale(sigma, rho_star, star_mass, coulomb_log)
    return (star_mass / m_bh) * t_relax_star
