"""Initial BH population setup (Newton et al. 2026, Section 2/3).

See docs/equations.md#initial-orbital-properties. Initial mass/spin distributions
(K20, K20+M, H18, H18+M) are Phase 3 work -- this module takes mass/spin samplers as
injectable callables so Phase 2's loop mechanics can be built and tested independently
of those specific distributions.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from imbh_nuclei.inspiral import remaining_merger_time_circular

#: Outer bound for the log-uniform semimajor-axis sampling [pc], matching N26's stated
#: focus region (the inner 0.1 pc of the NSC). Confirmed from the paper text.
A_MAX_PC = 0.1

#: Inner bound for the log-uniform semimajor-axis sampling [pc]. NOT given by N26 or by
#: Rose et al. 2022 (whose own sampling range is stated only qualitatively as "the inner
#: few parsecs... including within 0.01 pc"). See paper/limitations.md#initial-orbital-properties
#: -- flagged to user. Chosen so that even a BH born exactly at a_min takes >100x the
#: 10 Gyr simulation time to inspiral via quiescent (non-kicked) GW decay alone
#: (remaining_merger_time_circular(20 Msun, 4e6 Msun, 1e-3 pc) ~ 1450 Gyr) -- an earlier
#: default of 1e-4 pc was revised after a full-loop smoke test showed an implausibly
#: high (66%) EMRI fraction traced to this exact cause: at 1e-4 pc quiescent inspiral
#: alone takes only ~0.15 Gyr, so most BHs sampled near that bound became prompt EMRIs
#: regardless of any dynamical processes. R_crit itself is far smaller still
#: (~1.5e-6 pc for a 4e6 Msun SMBH), so this is about the GW-inspiral timescale, not the
#: EMRI stopping-condition radius.
A_MIN_PC_DEFAULT = 1.0e-3

#: Representative BH mass [Msun] used to derive A_MIN_PC_DEFAULT's safety margin --
#: matches the value used in that constant's own derivation (see its docstring).
_A_MIN_REFERENCE_BH_MASS = 20.0

#: Target quiescent GW-inspiral time [yr] from a_min, matching A_MIN_PC_DEFAULT's own
#: derivation (remaining_merger_time_circular(20, 4e6, 1e-3 pc) ~ 1450 Gyr).
_A_MIN_TARGET_TAU_YR = 1450.0e9


def a_min_safety_bound(
    m_smbh: float,
    m1: float = _A_MIN_REFERENCE_BH_MASS,
    target_tau_yr: float = _A_MIN_TARGET_TAU_YR,
) -> float:
    """Generalizes A_MIN_PC_DEFAULT's safety margin to an arbitrary SMBH mass.

    A_MIN_PC_DEFAULT (1e-3 pc) was reverse-engineered so a BH born at that radius takes
    >>10 Gyr to inspiral via quiescent GW decay alone, at N26's fiducial m_smbh=4e6 --
    otherwise sampling near a_min manufactures prompt EMRIs that are a numerical
    artifact, not physics (see that constant's docstring for the earlier 1e-4 pc bug
    this was found from). Needed for Phase 5 (SMBH-mass scan): the quiescent GW merger
    time scales steeply with m_smbh (roughly tau ~ 1/m_smbh^2 for m_smbh >> m1, from
    inspiral.remaining_merger_time_circular's m1*m2*(m1+m2) denominator), so reusing
    A_MIN_PC_DEFAULT unchanged at other SMBH masses would reintroduce that exact
    artifact -- e.g. holding it fixed at m_smbh=4e7 (10x N26's fiducial value) drops the
    inspiral time from ~1450 Gyr to ~18 Gyr, no longer a safe margin above the 10 Gyr
    simulation span.

    Solves a_min(m_smbh) so that
    inspiral.remaining_merger_time_circular(m1, m_smbh, a_min) == target_tau_yr, using
    the closed form's exact tau ~ a^4 scaling (no root-finder needed). At
    m_smbh=4e6 this returns ~9.45e-4 pc, close to but not identical to
    A_MIN_PC_DEFAULT's manually-chosen 1e-3 -- callers reproducing Phase 3/4 exactly
    should keep using A_MIN_PC_DEFAULT verbatim at that one anchor point, not this
    function, to preserve bit-for-bit reproducibility.
    """
    a_probe = A_MIN_PC_DEFAULT
    tau_at_probe = remaining_merger_time_circular(m1, m_smbh, a_probe)
    return float(a_probe * (target_tau_yr / tau_at_probe) ** 0.25)


def sample_thermal_eccentricity(n: int, rng: np.random.Generator) -> np.ndarray:
    """Thermal eccentricity distribution, p(e) = 2e for e in [0, 1).

    Inverse-CDF sampling: CDF(e) = e^2, so e = sqrt(U) for U ~ Uniform(0, 1).
    See docs/equations.md#initial-orbital-properties (S. C. Rose et al. 2022).
    """
    u = rng.uniform(0, 1, size=n)
    return np.sqrt(u)


def sample_log_uniform_semimajor_axis(
    n: int, rng: np.random.Generator, a_min: float = A_MIN_PC_DEFAULT, a_max: float = A_MAX_PC
) -> np.ndarray:
    """Semimajor axis log-uniform in [a_min, a_max] pc: dN/d(log10 a) = const.

    See docs/equations.md#initial-orbital-properties (S. C. Rose et al. 2022).
    """
    log_a = rng.uniform(np.log10(a_min), np.log10(a_max), size=n)
    return 10.0**log_a


@dataclass
class PopulationState:
    """Per-BH state arrays for the N-BH sample, all length N and vectorized together."""

    mass: np.ndarray  # Msun
    chi: np.ndarray  # spin magnitude, [0, 1]
    a: np.ndarray  # semimajor axis about the SMBH, pc
    e: np.ndarray  # eccentricity
    generation: np.ndarray  # merger generation, starts at 1
    n_collisions: np.ndarray  # diagnostic counter
    status: np.ndarray  # 'active', 'excursion' (kicked beyond a_max, bound, sinking
    # back), 'emri' (terminal), 'ejected' (terminal, unbound)
    reactivation_time_yr: np.ndarray  # meaningful only for status == 'excursion': the
    # global simulation time at which this BH returns to 'active' at a = a_max

    def __len__(self) -> int:
        return len(self.mass)

    @property
    def active(self) -> np.ndarray:
        return self.status == "active"


def initialize_population(
    n_bh: int,
    mass_sampler,
    spin_sampler,
    rng: np.random.Generator,
    a_min: float = A_MIN_PC_DEFAULT,
    a_max: float = A_MAX_PC,
) -> PopulationState:
    """Build the initial N-BH population state.

    Parameters
    ----------
    n_bh : int
        Sample size (paper default 1000).
    mass_sampler : Callable[[int, np.random.Generator], np.ndarray]
        Draws n_bh initial masses [Msun]. Phase 3 will supply the K20/H18/etc. samplers;
        Phase 2 tests may use a simple placeholder (e.g. a fixed value or narrow range).
    spin_sampler : Callable[[int, np.random.Generator], np.ndarray]
        Draws n_bh initial spin magnitudes.
    rng : numpy.random.Generator
    a_min, a_max : float
        Semimajor-axis sampling bounds [pc] -- see A_MIN_PC_DEFAULT's docstring note on
        the unresolved inner-bound ambiguity.

    Returns
    -------
    PopulationState
    """
    mass = np.asarray(mass_sampler(n_bh, rng), dtype=float)
    chi = np.asarray(spin_sampler(n_bh, rng), dtype=float)
    a = sample_log_uniform_semimajor_axis(n_bh, rng, a_min=a_min, a_max=a_max)
    e = sample_thermal_eccentricity(n_bh, rng)

    return PopulationState(
        mass=mass,
        chi=chi,
        a=a,
        e=e,
        generation=np.ones(n_bh, dtype=int),
        n_collisions=np.zeros(n_bh, dtype=int),
        status=np.full(n_bh, "active", dtype=object),
        reactivation_time_yr=np.zeros(n_bh, dtype=float),
    )
