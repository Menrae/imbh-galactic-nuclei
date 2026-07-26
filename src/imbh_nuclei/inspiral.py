"""GW inspiral into the SMBH / EMRI flagging (Newton et al. 2026, Section 4.4).

See docs/equations.md#section-44--gravitational-wave-inspiral-into-the-supermassive-black-hole.
Newton et al. 2026 cites P. C. Peters & J. Mathews 1963 and P. C. Peters 1964 for the
orbital decay without restating the equations; the standard, well-established closed
forms from those papers are implemented directly here (not an ambiguity).

Unit note: the raw da/dt, de/dt formulas below, evaluated with G_ASTRO/C_KMS (pc, Msun,
km/s units), come out in units of (km/s) and (km/s)/pc respectively -- both converted to
pc/yr and 1/yr via the same factor YR_TO_S/PC_TO_KM. This conversion was verified
numerically against an independent SI-unit computation (see tests/test_inspiral.py),
not just derived by hand, since unit-system conversions of this kind are easy to get
subtly wrong.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

from imbh_nuclei.constants import C_KMS, G_ASTRO, PC_TO_KM, YR_TO_S

#: Conversion factor from the "raw" pc/Msun/km-s unit system to yr-based rates,
#: verified numerically against an independent SI computation (see module docstring).
_RATE_CONVERSION = YR_TO_S / PC_TO_KM


def da_dt(m1: ArrayLike, m2: ArrayLike, a: ArrayLike, e: ArrayLike) -> np.ndarray:
    """Orbit-averaged semimajor-axis decay rate from GW emission (Peters 1964).

    da/dt = -64/5 * G^3*m1*m2*(m1+m2) / [c^5*a^3*(1-e^2)^(7/2)] * (1 + 73/24 e^2 + 37/96 e^4)

    Returns
    -------
    ndarray
        da/dt [pc/yr] (negative: the orbit shrinks).
    """
    m1 = np.asarray(m1, dtype=float)
    m2 = np.asarray(m2, dtype=float)
    a = np.asarray(a, dtype=float)
    e = np.asarray(e, dtype=float)

    prefactor = -64 / 5 * G_ASTRO**3 * m1 * m2 * (m1 + m2) / (C_KMS**5 * a**3)
    ecc_factor = (1 + 73 / 24 * e**2 + 37 / 96 * e**4) / (1 - e**2) ** 3.5
    return prefactor * ecc_factor * _RATE_CONVERSION


def de_dt(m1: ArrayLike, m2: ArrayLike, a: ArrayLike, e: ArrayLike) -> np.ndarray:
    """Orbit-averaged eccentricity decay rate from GW emission (Peters 1964).

    de/dt = -304/15 * e * G^3*m1*m2*(m1+m2) / [c^5*a^4*(1-e^2)^(5/2)] * (1 + 121/304 e^2)

    Returns
    -------
    ndarray
        de/dt [1/yr] (negative: the orbit circularizes).
    """
    m1 = np.asarray(m1, dtype=float)
    m2 = np.asarray(m2, dtype=float)
    a = np.asarray(a, dtype=float)
    e = np.asarray(e, dtype=float)

    prefactor = -304 / 15 * e * G_ASTRO**3 * m1 * m2 * (m1 + m2) / (C_KMS**5 * a**4)
    ecc_factor = (1 + 121 / 304 * e**2) / (1 - e**2) ** 2.5
    return prefactor * ecc_factor * _RATE_CONVERSION


def remaining_merger_time_circular(m1: ArrayLike, m2: ArrayLike, a: ArrayLike) -> np.ndarray:
    """Closed-form GW merger time for a circular orbit (e=0 limit of Peters 1964).

    tau = 5/256 * c^5*a^4 / (G^3*m1*m2*(m1+m2))

    A useful cross-check / fast estimate; the Phase 2 loop should integrate da/dt, de/dt
    numerically per-timestep for eccentric orbits rather than rely on this circular
    closed form alone.

    Returns
    -------
    ndarray
        tau [yr].
    """
    m1 = np.asarray(m1, dtype=float)
    m2 = np.asarray(m2, dtype=float)
    a = np.asarray(a, dtype=float)
    tau_raw = 5 / 256 * C_KMS**5 * a**4 / (G_ASTRO**3 * m1 * m2 * (m1 + m2))  # pc / (km/s)
    return tau_raw * PC_TO_KM / YR_TO_S


def r_crit(m_smbh: ArrayLike) -> np.ndarray:
    """Critical periapsis radius for the EMRI stopping condition: R_crit = 8*G*M_SMBH/c^2."""
    m_smbh = np.asarray(m_smbh, dtype=float)
    return 8 * G_ASTRO * m_smbh / C_KMS**2


def is_emri(
    periapsis: ArrayLike,
    m_smbh: ArrayLike,
    remaining_merger_time_yr: ArrayLike,
) -> np.ndarray:
    """EMRI stopping-condition flags (either condition triggers).

    1. periapsis < R_crit = 8*G*M_SMBH/c^2
    2. remaining GW merger time < 100 yr

    N26 notes these conditions may flag some plunging/eccentric-orbit BHs as EMRIs, but
    that this changes the EMRI rate by "no more than a factor of 2" and most flagged BHs
    have already circularized -- see paper/limitations.md.
    """
    periapsis = np.asarray(periapsis, dtype=float)
    m_smbh = np.asarray(m_smbh, dtype=float)
    remaining_merger_time_yr = np.asarray(remaining_merger_time_yr, dtype=float)

    condition_1 = periapsis < r_crit(m_smbh)
    condition_2 = remaining_merger_time_yr < 100.0
    return condition_1 | condition_2
