"""Orbital mechanics for a BH's orbit about the SMBH: applying velocity kicks (from GW
recoil, Eq. 13, or the relaxation random walk) and recovering new orbital elements.

See docs/equations.md#orbital-random-walk-from-relaxation. The Kepler-solver and
energy/angular-momentum-to-orbital-elements machinery here is standard two-body mechanics
(not paper-specific); only the *use* of an isotropic random kick orientation for the
relaxation random walk is a flagged simplification -- see the docs anchor above.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

from imbh_nuclei.constants import G_ASTRO, PC_TO_KM, YR_TO_S


def orbital_period(a: ArrayLike, m_smbh: ArrayLike) -> np.ndarray:
    """Kepler orbital period [yr] for semimajor axis a [pc] about mass m_smbh [Msun]."""
    a = np.asarray(a, dtype=float)
    m_smbh = np.asarray(m_smbh, dtype=float)
    # P = 2*pi*sqrt(a^3/(G*M)); a^3/(G*M) has units pc^3/(pc Msun^-1 (km/s)^2 * Msun)
    #   = pc^2/(km/s)^2 -- take sqrt -> pc/(km/s), then convert to yr.
    period_pc_per_kms = 2 * np.pi * np.sqrt(a**3 / (G_ASTRO * m_smbh))
    return period_pc_per_kms * PC_TO_KM / YR_TO_S


def solve_kepler_equation(mean_anomaly: ArrayLike, e: ArrayLike, tol: float = 1e-10) -> np.ndarray:
    """Solve M = E - e*sin(E) for the eccentric anomaly E via Newton's method."""
    mean_anomaly = np.asarray(mean_anomaly, dtype=float)
    e = np.asarray(e, dtype=float)
    ecc_anomaly = np.where(e < 0.8, mean_anomaly, np.pi * np.ones_like(mean_anomaly))
    for _ in range(100):
        f = ecc_anomaly - e * np.sin(ecc_anomaly) - mean_anomaly
        fprime = 1 - e * np.cos(ecc_anomaly)
        delta = f / fprime
        ecc_anomaly = ecc_anomaly - delta
        if np.all(np.abs(delta) < tol):
            break
    return ecc_anomaly


def kepler_state(
    a: ArrayLike, e: ArrayLike, m_smbh: ArrayLike, mean_anomaly: ArrayLike
) -> tuple[np.ndarray, np.ndarray]:
    """Position and velocity vectors in the orbital plane for given orbital elements.

    Parameters
    ----------
    a : array_like
        Semimajor axis [pc].
    e : array_like
        Eccentricity.
    m_smbh : array_like
        Central mass [Msun].
    mean_anomaly : array_like
        Mean anomaly [rad] -- uniform in [0, 2*pi) samples a point weighted by time spent,
        since mean anomaly is uniform in time by definition of a Kepler orbit.

    Returns
    -------
    r_vec : ndarray, shape (..., 2)
        Position [pc] in the (x, y) orbital plane, focus (SMBH) at the origin.
    v_vec : ndarray, shape (..., 2)
        Velocity [km/s] in the same plane.
    r : ndarray
        Radial distance [pc] (== norm(r_vec), returned for convenience).
    """
    a = np.asarray(a, dtype=float)
    e = np.asarray(e, dtype=float)
    m_smbh = np.asarray(m_smbh, dtype=float)
    mean_anomaly = np.asarray(mean_anomaly, dtype=float)

    ecc_anomaly = solve_kepler_equation(mean_anomaly, e)
    cos_ea = np.cos(ecc_anomaly)
    sin_ea = np.sin(ecc_anomaly)

    x = a * (cos_ea - e)
    y = a * np.sqrt(1 - e**2) * sin_ea
    r_vec = np.stack([x, y], axis=-1)

    n = 2 * np.pi / orbital_period(a, m_smbh)  # mean motion [rad/yr]
    r = a * (1 - e * cos_ea)
    factor = (a * n) / (1 - e * cos_ea)  # yr^-1 * pc = pc/yr
    vx = -factor * sin_ea
    vy = factor * np.sqrt(1 - e**2) * cos_ea
    v_vec_pc_per_yr = np.stack([vx, vy], axis=-1)

    # convert pc/yr -> km/s: 1 pc/yr = PC_TO_KM km / YR_TO_S s
    v_vec = v_vec_pc_per_yr * (PC_TO_KM / YR_TO_S)
    return r_vec, v_vec, r


def orbital_elements_from_state(
    r_vec: ArrayLike, v_vec: ArrayLike, m_smbh: ArrayLike
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Recover (a, e, bound) from a 2D position/velocity state about mass m_smbh.

    Parameters
    ----------
    r_vec : array_like, shape (..., 2)
        Position [pc].
    v_vec : array_like, shape (..., 2)
        Velocity [km/s].
    m_smbh : array_like
        Central mass [Msun].

    Returns
    -------
    a : ndarray
        Semimajor axis [pc] (only meaningful where bound is True).
    e : ndarray
        Eccentricity (only meaningful where bound is True).
    bound : ndarray of bool
        Whether the specific orbital energy is negative (still bound to the SMBH).
    """
    r_vec = np.asarray(r_vec, dtype=float)
    v_vec = np.asarray(v_vec, dtype=float)
    m_smbh = np.asarray(m_smbh, dtype=float)

    r = np.linalg.norm(r_vec, axis=-1)
    v2 = np.sum(v_vec**2, axis=-1)  # (km/s)^2
    gm = G_ASTRO * m_smbh  # pc (km/s)^2

    specific_energy = v2 / 2 - gm / r  # (km/s)^2
    bound = specific_energy < 0

    a = np.where(bound, -gm / (2 * specific_energy), np.inf)

    # specific angular momentum (2D cross product, z-component) [pc * km/s]
    l_spec = r_vec[..., 0] * v_vec[..., 1] - r_vec[..., 1] * v_vec[..., 0]
    e_squared = 1 + (2 * specific_energy * l_spec**2) / gm**2
    e = np.sqrt(np.clip(e_squared, 0, None))

    return a, e, bound


def apply_velocity_kick(
    a: ArrayLike,
    e: ArrayLike,
    m_smbh: ArrayLike,
    kick_speed: ArrayLike,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Apply a velocity kick of given magnitude, at a random orbital phase and random
    orientation, and return the resulting orbit.

    Used for both the relaxation random walk (kick magnitude from
    relaxation_kick_sigma) and GW recoil kicks (kick magnitude |v_kick| from Eq. 13) --
    see docs/equations.md#orbital-random-walk-from-relaxation for the isotropic-
    orientation simplification this entails for the relaxation case.

    Parameters
    ----------
    a, e : array_like
        Current orbital elements [pc, dimensionless].
    m_smbh : array_like
        SMBH mass [Msun].
    kick_speed : array_like
        Kick magnitude [km/s].
    rng : numpy.random.Generator

    Returns
    -------
    a_new, e_new : ndarray
        New orbital elements (a_new = inf where unbound).
    bound : ndarray of bool
        Whether the BH remains bound to the SMBH after the kick.
    """
    a = np.asarray(a, dtype=float)
    e = np.asarray(e, dtype=float)
    m_smbh = np.asarray(m_smbh, dtype=float)
    kick_speed = np.asarray(kick_speed, dtype=float)
    shape = np.broadcast(a, e, m_smbh, kick_speed).shape

    mean_anomaly = rng.uniform(0, 2 * np.pi, size=shape)
    r_vec, v_vec, _ = kepler_state(a, e, m_smbh, mean_anomaly)

    # isotropic random 3D kick direction, then discard the out-of-plane component
    # (equivalent to a random orientation relative to the 2D orbital frame)
    phi = rng.uniform(0, 2 * np.pi, size=shape)
    kick_vec = kick_speed[..., None] * np.stack([np.cos(phi), np.sin(phi)], axis=-1)

    v_new = v_vec + kick_vec
    a_new, e_new, bound = orbital_elements_from_state(r_vec, v_new, m_smbh)
    return a_new, e_new, bound


def relaxation_kick_sigma(a: ArrayLike, m_smbh: ArrayLike, t_relax_yr: ArrayLike) -> np.ndarray:
    """Per-component standard deviation of the relaxation velocity kick (S. C. Rose
    et al. 2022): sigma = Delta_v_rlx / sqrt(3), Delta_v_rlx = v_bullet * sqrt(P_bullet/t_relax).

    v_bullet is taken as the circular orbital speed sqrt(G*M_smbh/a) at the current
    semimajor axis.
    """
    a = np.asarray(a, dtype=float)
    m_smbh = np.asarray(m_smbh, dtype=float)
    t_relax_yr = np.asarray(t_relax_yr, dtype=float)

    v_bullet = np.sqrt(G_ASTRO * m_smbh / a)  # km/s
    period = orbital_period(a, m_smbh)  # yr
    delta_v_rlx = v_bullet * np.sqrt(period / t_relax_yr)
    return delta_v_rlx / np.sqrt(3)
