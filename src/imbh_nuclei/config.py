"""Config system: a full simulation run is fully specified by one SimulationConfig.

Reused across single validation runs (Phase 3) and the parameter scans in Phases 4-6, so
every field that later phases will need to vary (initial mass distribution, SMBH mass,
cusp slope alpha, N particles, integration time/timestep, random seed) lives here from
the start rather than being bolted on later.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

#: Valid initial BH mass/spin distributions from Newton et al. 2026, Table 1.
VALID_INITIAL_DISTRIBUTIONS = ("K20", "K20+M", "H18", "H18+M")


@dataclass
class ClusterConfig:
    """Nuclear star cluster structure parameters (Newton et al. 2026, Section 2)."""

    #: SMBH mass [Msun].
    m_smbh: float = 4.0e6
    #: Stellar density power-law slope alpha (Eq. 3). Paper default; observations suggest 1.1-1.4.
    alpha_star: float = 1.25
    #: BH number density power-law slope alpha (Eq. 2).
    alpha_bh: float = 1.83
    #: Stellar density normalization rho0 [Msun/pc^3] at r0 (Eq. 3).
    rho0: float = 1.35e6
    #: Stellar density normalization radius r0 [pc] (Eq. 3).
    r0: float = 0.25
    #: BH number density normalization n0 [pc^-3] at r_h (Eq. 2).
    n0_bh: float = 1.0e4
    #: SMBH sphere-of-influence radius R_h [pc], the BH density normalization radius (Eq. 2).
    r_h: float = 1.0
    #: Coulomb logarithm ln(Lambda) for the relaxation timescale (Eq. 22). Not specified
    #: numerically by Newton et al. 2026 (nor by S. C. Rose et al. 2022, whose Eq. 10 this
    #: formula is), but the specific regime -- relaxation of a single-mass (star) population
    #: dominated by a much heavier central point mass (Q = M_bullet/m_star >> 1) -- has a
    #: well-established standard prescription in the literature: ln(Lambda) ~ ln(Q), NOT the
    #: ln(0.4N) convention used for self-gravitating systems without a dominant central mass
    #: (see paper/limitations.md#coulomb-logarithm for the literature trace: Ben Bar-Or,
    #: G. Kupi, & T. Alexander 2013, ApJ, 764, 52; E. Vasiliev 2017, ApJ, 848, 10, who use
    #: this exact prescription for a Milky-Way-like M_bullet=4e6 Msun nucleus and get
    #: ln(Lambda)=15). Default here is ln(4e6/1) = 15.2018, evaluated at this dataclass's
    #: own m_smbh/star-mass defaults -- if m_smbh is changed (e.g. Phase 5's SMBH mass
    #: scan), this value should be recomputed as ln(m_smbh/1.0), not reused verbatim.
    coulomb_log: float = 15.201804919084164
    #: Outer bound for the tracked cluster region [pc] (Eq. 2 focus region, confirmed).
    a_max_pc: float = 0.1
    #: Inner bound for initial semimajor-axis sampling [pc] -- see
    #: paper/limitations.md#initial-orbital-properties, not given by N26. See
    #: population.A_MIN_PC_DEFAULT for why 1e-3 (not the earlier, too-aggressive 1e-4).
    a_min_pc: float = 1.0e-3


@dataclass
class PopulationConfig:
    """Initial BH population parameters (Newton et al. 2026, Section 3)."""

    #: One of VALID_INITIAL_DISTRIBUTIONS.
    initial_mass_distribution: str = "H18+M"
    #: Number of BHs in the sample.
    n_bh: int = 1000
    #: Primordial-binary-merger-product fraction (paper: 15%, "+M" variants only).
    primordial_binary_fraction: float = 0.15
    #: Mean BH mass [Msun] of the initial distribution in use, for the GW-capture eta
    #: calculation ("we take m2 in eta to be the average of the initial mass
    #: distribution", Section 4.1). MUST be set consistently with whichever
    #: mass_sampler is actually used -- this default (34.2) is the Monte Carlo-estimated
    #: mean specifically for H18+M (this dataclass's own default
    #: initial_mass_distribution), computed directly from
    #: initial_conditions.get_samplers("H18+M") at N=2e6, not a placeholder. Measured
    #: per-IC means (found to differ from an earlier, uncorrected 20.0 placeholder used
    #: through Phase 2 smoke-testing -- see paper/limitations.md#phase2-emri-rate-high):
    #: K20 9.72, K20+M 9.94, H18 33.40, H18+M 34.20.
    mean_bh_mass: float = 34.2

    def __post_init__(self) -> None:
        if self.initial_mass_distribution not in VALID_INITIAL_DISTRIBUTIONS:
            raise ValueError(
                f"initial_mass_distribution must be one of {VALID_INITIAL_DISTRIBUTIONS}, "
                f"got {self.initial_mass_distribution!r}"
            )


@dataclass
class IntegrationConfig:
    """Monte Carlo integration loop parameters (Newton et al. 2026, Section 4)."""

    #: Total integration time [Gyr].
    t_max_gyr: float = 10.0
    #: Initial timestep [yr]; adaptively shrunk below the shortest relevant timescale.
    dt0_yr: float = 1.0e6
    #: Fraction of min(t_coll, t_GW) the adaptive timestep is capped at, keeping the
    #: per-step event probability well below 1 (paper: "adjust the timestep ... to be
    #: always less than the collision timescale" -- the specific safety margin below
    #: that is our choice, not stated numerically in N26).
    timestep_safety_factor: float = 0.1
    #: Random seed for reproducibility.
    seed: int = 0
    #: Number of sub-steps the relaxation random walk (Sec 4.3) is broken into within
    #: each global timestep, so local dynamics (orbital period, t_relax, v_circ) get
    #: re-evaluated partway through the walk instead of only at its start -- see
    #: paper/limitations.md#phase2-emri-rate-high and
    #: docs/equations.md#orbital-random-walk-from-relaxation for why the one-shot
    #: aggregation (implicitly holding these fixed for the whole span) was wrong, and why
    #: this coarser-than-per-orbit substep count is our practical middle ground.
    relaxation_substeps: int = 20


@dataclass
class SimulationConfig:
    """Full specification of one simulation run."""

    cluster: ClusterConfig = field(default_factory=ClusterConfig)
    population: PopulationConfig = field(default_factory=PopulationConfig)
    integration: IntegrationConfig = field(default_factory=IntegrationConfig)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_yaml(self, path: str | Path) -> None:
        with open(path, "w") as fh:
            yaml.safe_dump(self.to_dict(), fh, sort_keys=False)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "SimulationConfig":
        return cls(
            cluster=ClusterConfig(**d.get("cluster", {})),
            population=PopulationConfig(**d.get("population", {})),
            integration=IntegrationConfig(**d.get("integration", {})),
        )

    @classmethod
    def from_yaml(cls, path: str | Path) -> "SimulationConfig":
        with open(path) as fh:
            d = yaml.safe_load(fh) or {}
        return cls.from_dict(d)
