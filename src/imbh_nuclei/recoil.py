"""GW recoil kicks (Newton et al. 2026, Section 4.1.1).

See docs/equations.md#section-411--recoil-kicks. Fitting constants A, B, H, K are not
tabulated in Newton et al. 2026 -- pulled directly from K. Holley-Bockelmann, K. Gultekin,
D. Shoemaker, & N. Yunes 2008, ApJ, 686, 829 (arXiv:0707.1334, Eqs. 2-4), which itself
adopts the numerical-relativity fit of Campanelli et al. 2007 (ApJL, 659, L5).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike


@dataclass(frozen=True)
class HolleyBockelmann2008:
    """Recoil-kick fitting constants [km/s except B, dimensionless]."""

    A: float = 1.2e4
    B: float = -0.93
    H: float = 7.3e3
    K: float = 6.0e4


HOLLEY_BOCKELMANN_2008 = HolleyBockelmann2008()


def v_m(q: ArrayLike, constants: HolleyBockelmann2008 = HOLLEY_BOCKELMANN_2008) -> np.ndarray:
    """In-plane recoil speed from unequal masses (Eq. 14). q = m2/m1."""
    q = np.asarray(q, dtype=float)
    return constants.A * q**2 * (1 - q) / (1 + q) ** 5 * (1 + constants.B * q / (1 + q) ** 2)


def v_perp(
    q: ArrayLike,
    chi_par_2: ArrayLike,
    chi_par_1: ArrayLike,
    constants: HolleyBockelmann2008 = HOLLEY_BOCKELMANN_2008,
) -> np.ndarray:
    """In-plane recoil speed from unequal spins (Eq. 15)."""
    q = np.asarray(q, dtype=float)
    chi_par_2 = np.asarray(chi_par_2, dtype=float)
    chi_par_1 = np.asarray(chi_par_1, dtype=float)
    return constants.H * q**2 / (1 + q) ** 5 * (chi_par_2 - q * chi_par_1)


def v_parallel(
    q: ArrayLike,
    chi_perp_2: ArrayLike,
    chi_perp_1: ArrayLike,
    theta: ArrayLike,
    theta_0: ArrayLike,
    constants: HolleyBockelmann2008 = HOLLEY_BOCKELMANN_2008,
) -> np.ndarray:
    """Out-of-plane recoil speed (Eq. 16)."""
    q = np.asarray(q, dtype=float)
    chi_perp_2 = np.asarray(chi_perp_2, dtype=float)
    chi_perp_1 = np.asarray(chi_perp_1, dtype=float)
    theta = np.asarray(theta, dtype=float)
    theta_0 = np.asarray(theta_0, dtype=float)
    return (
        constants.K
        * np.cos(theta - theta_0)
        * q**2
        / (1 + q) ** 5
        * (chi_perp_2 - q * chi_perp_1)
    )


def kick_velocity(
    q: ArrayLike,
    chi_par_1: ArrayLike,
    chi_par_2: ArrayLike,
    chi_perp_1: ArrayLike,
    chi_perp_2: ArrayLike,
    theta: ArrayLike,
    theta_0: ArrayLike,
    xi: ArrayLike,
    eccentricity: ArrayLike = 0.0,
    constants: HolleyBockelmann2008 = HOLLEY_BOCKELMANN_2008,
) -> np.ndarray:
    """Full recoil velocity vector (Eq. 13), in the orbital (x, y, z) basis.

    v_kick = (1+e) * [x_hat*(v_m + v_perp*cos(xi)) + y_hat*v_perp*sin(xi) + z_hat*v_par]

    Parameters
    ----------
    q : array_like
        Mass ratio m2/m1.
    chi_par_1, chi_par_2 : array_like
        Spin components parallel to the orbital angular momentum.
    chi_perp_1, chi_perp_2 : array_like
        Spin components perpendicular to the orbital angular momentum.
    theta, theta_0, xi : array_like
        Merger-direction, initial-direction, and mass/spin-asymmetry angles [rad] --
        drawn uniformly per merger, per N26.
    eccentricity : array_like
        Orbital eccentricity at merger (default 0 for a circularized binary; N26's
        prompt GW-capture mergers are high-eccentricity, so pass the actual value when
        known).

    Returns
    -------
    ndarray, shape (..., 3)
        Kick velocity vector [km/s] in the (x, y, z) orbital basis.
    """
    q = np.asarray(q, dtype=float)
    xi = np.asarray(xi, dtype=float)
    eccentricity = np.asarray(eccentricity, dtype=float)

    vm = v_m(q, constants)
    vperp = v_perp(q, chi_par_2, chi_par_1, constants)
    vpar = v_parallel(q, chi_perp_2, chi_perp_1, theta, theta_0, constants)

    vx = vm + vperp * np.cos(xi)
    vy = vperp * np.sin(xi)
    vz = vpar
    stacked = np.stack([vx, vy, vz], axis=-1)
    return np.expand_dims(1 + eccentricity, axis=-1) * stacked
