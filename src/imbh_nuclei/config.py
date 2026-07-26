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
    #: Coulomb logarithm ln(Lambda) for the relaxation timescale (Eq. 22). NOT specified
    #: by Newton et al. 2026 -- see paper/limitations.md#coulomb-logarithm. ln(10) ~ 2.3
    #: is a placeholder pending a literature value; ln(M_SMBH/<m>) ~ 12-13 is a common
    #: alternative choice in this subfield -- deliberately not defaulted to that without
    #: a decision, so this default is conservative/small rather than silently "reasonable".
    coulomb_log: float = 10.0
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
    #: distribution", Section 4.1) and the Eq. 22 <M_avg> resolution. Phase 3 should set
    #: this consistently with whichever mass_sampler is actually used.
    mean_bh_mass: float = 20.0

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
